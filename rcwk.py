#!/usr/bin/env python3
#
# =============================================================================
#  Project      : RcFux
#  Description  : Bootable USB creator for Linux (ISO/IMG, Windows, format, bad blocks)
#  Author       : Raffaele Catapano
#  License      : MIT (see LICENSE)
#  Created on   : 11/11/2026
#  Version      : 2.1
#
#  Copyright (c) 2025-2026 Raffaele Catapano
#  Released under the MIT License - see the LICENSE file for details.
#  SPDX-License-Identifier: MIT
# =============================================================================
"""rcwk.py - privileged part of RcFux.

Run as root through pkexec by the GUI (main.py).
Usage: rcwk.py '<json-job>' <cancel-file>

Protocol (one line per message on stdout):
  PROGRESS <0-100>
  STATUS <key> [<json-params>]
  DONE <key> [<json-params>]
  ERROR <key> [<json-params>]
  CANCELLED
The worker never sends human-readable text: <key> is translated by the GUI
(see i18n.py), so this file stays independent from the UI language.
"""
import hashlib
import json
import os
import re
import select
import subprocess
import sys
import tempfile
import time

CHUNK = 4 * 1024 * 1024
FAT32_MAX = 4 * 1024**3 - 1
SYSTEM_MOUNTS = {"/", "/boot", "/boot/efi", "/home", "/usr", "/var", "/opt", "[SWAP]"}
DEV_RE = re.compile(r"^/dev/(sd[a-z]+|vd[a-z]+|nvme\d+n\d+|mmcblk\d+)$")
# command -> package that provides it (Debian/Ubuntu names)
PACKAGES = {
    "parted": "parted",
    "mkfs.vfat": "dosfstools",
    "mkfs.ntfs": "ntfs-3g",
    "mkfs.exfat": "exfatprogs",
    "mkfs.ext4": "e2fsprogs",
    "badblocks": "e2fsprogs",
    "wimlib-imagex": "wimtools",
}


class Cancelled(Exception):
    pass


class JobError(Exception):
    """Error carrying a message key and its parameters (translated by the GUI)."""

    def __init__(self, key, **params):
        super().__init__(key)
        self.key = key
        self.params = params


def out(kind, key="", **params):
    line = f"{kind} {key}".rstrip()
    if params:
        line += " " + json.dumps(params)  # JSON escapes newlines: one message per line
    print(line, flush=True)


class Job:
    def __init__(self, spec, cancel_file):
        self.mode = spec["mode"]
        self.dev = spec["device"]
        self.image = spec.get("image") or ""
        self.scheme = spec.get("scheme", "gpt")
        self.fs = spec.get("fs", "fat32")
        self.label = (spec.get("label") or "USB").strip() or "USB"
        self.verify = bool(spec.get("verify"))
        self.cancel_file = cancel_file
        self._last = -1

    def check_cancel(self):
        if os.path.exists(self.cancel_file):
            raise Cancelled()

    def progress(self, pct):
        pct = max(0, min(100, int(pct)))
        if pct != self._last:
            self._last = pct
            out("PROGRESS", str(pct))

    def status(self, key, **params):
        out("STATUS", key, **params)


def missing_command(cmd):
    pkg = PACKAGES.get(cmd)
    if pkg:
        return JobError("cmd_not_found_pkg", cmd=cmd, pkg=pkg)
    return JobError("cmd_not_found", cmd=cmd)


# -------------------------------------------------------------- utilities ---
def run(cmd, check=True):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        raise missing_command(cmd[0])
    if check and r.returncode != 0:
        raise JobError("cmd_failed", cmd=" ".join(cmd), detail=(r.stderr or r.stdout).strip())
    return r


def run_stream(job, cmd, on_text=None):
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        raise missing_command(cmd[0])
    fd = p.stdout.fileno()
    collected = []
    try:
        while True:
            if os.path.exists(job.cancel_file):
                p.terminate()
                p.wait()
                raise Cancelled()
            ready, _, _ = select.select([fd], [], [], 0.5)
            if ready:
                data = os.read(fd, 4096)
                if not data:
                    break
                text = data.decode(errors="replace")
                collected.append(text)
                if on_text:
                    on_text(text)
            elif p.poll() is not None:
                break
    finally:
        if p.poll() is None:
            p.kill()
    p.wait()
    return p.returncode, "".join(collected)


def mountpoints(node):
    mps = node.get("mountpoints") or [node.get("mountpoint")]
    return [m for m in mps if m]


def walk(node):
    yield node
    for c in node.get("children") or []:
        yield from walk(c)


def lsblk(dev):
    r = run(["lsblk", "-J", "-b", "-o", "NAME,PATH,TYPE,SIZE,MOUNTPOINTS", dev])
    return json.loads(r.stdout)["blockdevices"][0]


def validate_device(dev):
    if not DEV_RE.match(dev) or not os.path.exists(dev):
        raise JobError("bad_device", dev=dev)
    info = lsblk(dev)
    if info.get("type") != "disk":
        raise JobError("not_disk")
    for n in walk(info):
        for mp in mountpoints(n):
            if mp in SYSTEM_MOUNTS or mp.startswith("/boot"):
                raise JobError("system_device")


def unmount_all(dev):
    for n in reversed(list(walk(lsblk(dev)))):
        if mountpoints(n):
            run(["umount", n["path"]], check=False)


def part_path(dev, n=1):
    return f"{dev}{'p' if dev[-1].isdigit() else ''}{n}"


def wait_for(path):
    run(["udevadm", "settle"], check=False)
    for _ in range(50):
        if os.path.exists(path):
            return
        time.sleep(0.2)
    raise JobError("partition_missing", path=path)


def make_partition(job):
    dev, fs = job.dev, job.fs
    unmount_all(dev)
    run(["wipefs", "-a", dev])
    run(["parted", "-s", dev, "mklabel", "gpt" if job.scheme == "gpt" else "msdos"])
    ptype = {"fat32": "fat32", "ntfs": "ntfs", "exfat": "ntfs", "ext4": "ext4"}[fs]
    run(["parted", "-s", "-a", "optimal", dev, "mkpart", "primary", ptype, "1MiB", "100%"])
    if job.scheme == "mbr":
        run(["parted", "-s", dev, "set", "1", "boot", "on"])
    elif fs != "ext4":
        run(["parted", "-s", dev, "set", "1", "msftdata", "on"])
    run(["partprobe", dev], check=False)
    part = part_path(dev)
    wait_for(part)
    unmount_all(dev)  # keep desktop automounters (e.g. KDE) out of the way
    return part


def make_fs(part, fs, label):
    if fs == "fat32":
        run(["mkfs.vfat", "-F", "32", "-n", label.upper()[:11], part])
    elif fs == "ntfs":
        run(["mkfs.ntfs", "-f", "-L", label[:32], part])
    elif fs == "exfat":
        run(["mkfs.exfat", "-L", label[:15], part])
    elif fs == "ext4":
        run(["mkfs.ext4", "-F", "-L", label[:16], part])


# ------------------------------------------------------------------ modes ---
def write_image(job):
    size = os.path.getsize(job.image)
    devsize = int(run(["blockdev", "--getsize64", job.dev]).stdout.strip())
    if size > devsize:
        raise JobError("image_too_big")
    job.status("st_unmount")
    unmount_all(job.dev)
    run(["wipefs", "-a", job.dev])
    total = size * (2 if job.verify else 1)
    done = 0
    h = hashlib.sha256()
    job.status("st_writing")
    fd = os.open(job.dev, os.O_RDWR)
    try:
        with open(job.image, "rb") as src:
            n = 0
            while True:
                job.check_cancel()
                buf = src.read(CHUNK)
                if not buf:
                    break
                h.update(buf)
                view = memoryview(buf)
                while view:
                    view = view[os.write(fd, view):]
                done += len(buf)
                n += 1
                if n % 16 == 0:
                    os.fsync(fd)
                job.progress(done * 100 / total)
        job.status("st_syncing")
        os.fsync(fd)
        if job.verify:
            job.status("st_verifying")
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
            os.lseek(fd, 0, os.SEEK_SET)
            h2 = hashlib.sha256()
            remaining = size
            while remaining > 0:
                job.check_cancel()
                buf = os.read(fd, min(CHUNK, remaining))
                if not buf:
                    raise JobError("verify_short_read")
                h2.update(buf)
                remaining -= len(buf)
                done += len(buf)
                job.progress(done * 100 / total)
            if h.digest() != h2.digest():
                raise JobError("verify_failed")
    finally:
        os.close(fd)
    run(["partprobe", job.dev], check=False)
    job.progress(100)
    return ("done_image_verified" if job.verify else "done_image"), {}


def format_only(job):
    job.status("st_partition_table")
    job.progress(10)
    part = make_partition(job)
    job.status("st_formatting", fs=job.fs.upper())
    job.progress(40)
    make_fs(part, job.fs, job.label)
    unmount_all(job.dev)
    job.progress(100)
    return "done_format", {}


def write_windows(job):
    job.fs = "fat32"
    job.status("st_prepare")
    part = make_partition(job)
    job.progress(2)
    job.status("st_format_fat32")
    make_fs(part, "fat32", job.label)
    iso_mnt = tempfile.mkdtemp(prefix="rcfux-iso-")
    usb_mnt = tempfile.mkdtemp(prefix="rcfux-usb-")
    mounted = []
    try:
        job.status("st_mounting")
        run(["mount", "-o", "loop,ro", job.image, iso_mnt])
        mounted.append(iso_mnt)
        run(["mount", part, usb_mnt])
        mounted.append(usb_mnt)
        if not os.path.isdir(os.path.join(iso_mnt, "sources")):
            raise JobError("not_windows_iso")

        files, total = [], 0
        for root, _dirs, names in os.walk(iso_mnt):
            for name in names:
                src = os.path.join(root, name)
                rel = os.path.relpath(src, iso_mnt)
                size = os.path.getsize(src)
                files.append((src, rel, size))
                total += size
        total = max(total, 1)
        state = {"done": 0}

        for src, rel, size in files:
            job.check_cancel()
            dst = os.path.join(usb_mnt, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if size > FAT32_MAX:
                if rel.lower().replace("\\", "/") != "sources/install.wim":
                    raise JobError("file_too_big", rel=rel)
                job.status("st_splitting")
                code, text = run_stream(job, ["wimlib-imagex", "split", src,
                                              os.path.join(os.path.dirname(dst), "install.swm"), "3800"])
                if code != 0:
                    raise JobError("wimlib_failed", detail=text.strip()[-300:])
                state["done"] += size
            else:
                job.status("st_copy", rel=rel)
                with open(src, "rb") as a, open(dst, "wb") as b:
                    while True:
                        job.check_cancel()
                        buf = a.read(CHUNK)
                        if not buf:
                            break
                        b.write(buf)
                        state["done"] += len(buf)
                        job.progress(5 + state["done"] * 93 / total)
            job.progress(5 + state["done"] * 93 / total)
        job.status("st_sync_wait")
        os.sync()
    finally:
        os.sync()
        for m in reversed(mounted):
            run(["umount", m], check=False)
        for d in (usb_mnt, iso_mnt):
            try:
                os.rmdir(d)
            except OSError:
                pass
        unmount_all(job.dev)
    job.progress(100)
    return "done_windows", {}


def bad_blocks(job):
    job.status("st_badblocks")
    unmount_all(job.dev)

    def on_text(t):
        m = re.findall(r"(\d+(?:\.\d+)?)%", t)
        if m:
            job.progress(float(m[-1]))

    code, text = run_stream(job, ["badblocks", "-sv", "-b", "4096", job.dev], on_text)
    if code != 0:
        raise JobError("badblocks_failed", detail=text.strip()[-300:])
    job.progress(100)
    m = re.search(r"(\d+) bad blocks found", text)
    bad = int(m.group(1)) if m else 0
    if bad:
        return "done_bad_found", {"n": bad}
    return "done_bad_none", {}


MODES = {"image": write_image, "windows": write_windows, "format": format_only, "badblocks": bad_blocks}


def main():
    if os.geteuid() != 0:
        out("ERROR", "root_required")
        return 1
    try:
        spec = json.loads(sys.argv[1])
        cancel_file = sys.argv[2]
        if spec.get("mode") not in MODES:
            raise JobError("invalid_mode")
        if spec.get("scheme", "gpt") not in ("gpt", "mbr") or spec.get("fs", "fat32") not in ("fat32", "ntfs", "exfat", "ext4"):
            raise JobError("invalid_params")
        job = Job(spec, cancel_file)
        if job.mode in ("image", "windows") and not os.path.isfile(job.image):
            raise JobError("image_not_found")
        validate_device(job.dev)
        key, params = MODES[job.mode](job)
        out("DONE", key, **params)
    except Cancelled:
        out("CANCELLED")
    except JobError as e:
        out("ERROR", e.key, **e.params)
    except Exception as e:  # noqa: BLE001
        out("ERROR", "unexpected", err=repr(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
