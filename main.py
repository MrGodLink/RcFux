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
"""RcFux - graphical interface (PySide6).

Runs with the user's permissions; disk operations are executed by rcwk.py
as root through pkexec (one password prompt per operation).
The interface is bilingual (English / Italian), see i18n.py.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PySide6.QtCore import QLocale, QProcess, QThread, Qt, Signal
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from i18n import LANGUAGES, get_lang, set_lang, tr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(BASE_DIR, "rcwk.py")
ICON_PATH = os.path.join(BASE_DIR, "rcfux.svg")
APP_NAME = "RcFux"
AUTHOR = "Raffaele Catapano"
__version__ = "2.1"

SYSTEM_MOUNTS = {"/", "/boot", "/boot/efi", "/home", "/usr", "/var", "/opt", "[SWAP]"}

# (mode id, i18n key of the name; the description key is "<name key>_desc")
MODES = [
    ("image", "mode_image"),
    ("windows", "mode_windows"),
    ("format", "mode_format"),
    ("badblocks", "mode_badblocks"),
]


def human(n):
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024


def truthy(v):
    return str(v).lower() in ("1", "true")


def mountpoints(node):
    mps = node.get("mountpoints") or [node.get("mountpoint")]
    return [m for m in mps if m]


def walk(node):
    yield node
    for c in node.get("children") or []:
        yield from walk(c)


def list_devices(show_all):
    try:
        r = subprocess.run(
            ["lsblk", "-J", "-b", "-o", "NAME,PATH,TYPE,SIZE,MODEL,VENDOR,TRAN,RM,HOTPLUG,MOUNTPOINTS,LABEL"],
            capture_output=True, text=True, check=True)
        data = json.loads(r.stdout)["blockdevices"]
    except Exception:  # noqa: BLE001
        return []
    devs = []
    for d in data:
        if d.get("type") != "disk" or not int(d.get("size") or 0):
            continue
        if any(m in SYSTEM_MOUNTS or m.startswith("/boot") for n in walk(d) for m in mountpoints(n)):
            continue  # the system disk is never shown
        removable = d.get("tran") == "usb" or truthy(d.get("rm")) or truthy(d.get("hotplug"))
        if not (removable or show_all):
            continue
        name = " ".join(x for x in ((d.get("vendor") or "").strip(), (d.get("model") or "").strip()) if x) \
            or tr("disk_generic")
        labels = [c.get("label") for c in d.get("children") or [] if c.get("label")]
        extra = f" [{labels[0]}]" if labels else ""
        devs.append((f"{name}{extra} - {human(d['size'])} ({d['path']})", d["path"]))
    return devs


class HashThread(QThread):
    progress = Signal(int)
    result = Signal(str)

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.abort = False

    def run(self):
        h = hashlib.sha256()
        total = max(os.path.getsize(self.path), 1)
        done = 0
        try:
            with open(self.path, "rb") as f:
                while not self.abort:
                    buf = f.read(4 * 1024 * 1024)
                    if not buf:
                        break
                    h.update(buf)
                    done += len(buf)
                    self.progress.emit(int(done * 100 / total))
        except OSError as e:
            self.result.emit(f"ERR:{e}")
            return
        self.result.emit("" if self.abort else h.hexdigest())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} * Author : {AUTHOR}")
        self.setMinimumWidth(680)
        self.proc = None
        self.cancel_file = None
        self.hash_thread = None
        self.buf = ""
        self.result = None
        self._status = ("status_ready", {})   # re-translated when the language changes
        self._hash_view = None                # ("calc",) | ("err", msg) | ("ok", digest)
        self._retranslating = False

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- Header with logo and language selector
        banner = QHBoxLayout()
        logo = QLabel()
        icon = QIcon(ICON_PATH)
        if not icon.isNull():
            logo.setPixmap(icon.pixmap(64, 64))
        title = QLabel(APP_NAME)
        tf = QFont(title.font())
        tf.setPointSize(tf.pointSize() + 8)
        tf.setBold(True)
        title.setFont(tf)
        self.subtitle = QLabel()
        text_col = QVBoxLayout()
        text_col.setSpacing(0)
        text_col.addWidget(title)
        text_col.addWidget(self.subtitle)
        self.lang_label = QLabel()
        self.lang_combo = QComboBox()
        for code, name in LANGUAGES:
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(self.lang_combo.findData(get_lang()))
        banner.addWidget(logo)
        banner.addLayout(text_col, 1)
        banner.addWidget(self.lang_label)
        banner.addWidget(self.lang_combo)
        root.addLayout(banner)

        # --- Device
        self.g_dev = QGroupBox()
        f = QFormLayout(self.g_dev)
        self.dev_combo = QComboBox()
        self.btn_refresh = QPushButton()
        row = QHBoxLayout()
        row.addWidget(self.dev_combo, 1)
        row.addWidget(self.btn_refresh)
        self.chk_all = QCheckBox()
        self.lbl_device = QLabel()
        f.addRow(self.lbl_device, row)
        f.addRow("", self.chk_all)
        root.addWidget(self.g_dev)

        # --- Boot selection
        self.g_boot = QGroupBox()
        f = QFormLayout(self.g_boot)
        self.mode_combo = QComboBox()
        for mode_id, key in MODES:
            self.mode_combo.addItem("", mode_id)
        self.mode_desc = QLabel()
        self.mode_desc.setWordWrap(True)
        self.img_edit = QLineEdit()
        self.btn_browse = QPushButton()
        row = QHBoxLayout()
        row.addWidget(self.img_edit, 1)
        row.addWidget(self.btn_browse)
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        self.hash_expected = QLineEdit()
        self.btn_hash = QPushButton()
        row2 = QHBoxLayout()
        row2.addWidget(self.hash_expected, 1)
        row2.addWidget(self.btn_hash)
        self.hash_result = QLabel()
        self.hash_result.setWordWrap(True)
        self.hash_result.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lbl_mode, self.lbl_image, self.lbl_checksum = QLabel(), QLabel(), QLabel()
        f.addRow(self.lbl_mode, self.mode_combo)
        f.addRow("", self.mode_desc)
        f.addRow(self.lbl_image, row)
        f.addRow("", self.hint)
        f.addRow(self.lbl_checksum, row2)
        f.addRow("", self.hash_result)
        root.addWidget(self.g_boot)

        # --- Options
        self.g_opts = QGroupBox()
        f = QFormLayout(self.g_opts)
        self.scheme_combo = QComboBox()
        self.scheme_combo.addItem("GPT (UEFI)", "gpt")
        self.scheme_combo.addItem("MBR (BIOS/UEFI-CSM)", "mbr")
        self.fs_combo = QComboBox()
        self.label_edit = QLineEdit("USB")
        self.chk_verify = QCheckBox()
        self.chk_verify.setChecked(True)
        self.lbl_scheme, self.lbl_fs, self.lbl_label = QLabel(), QLabel(), QLabel()
        f.addRow(self.lbl_scheme, self.scheme_combo)
        f.addRow(self.lbl_fs, self.fs_combo)
        f.addRow(self.lbl_label, self.label_edit)
        f.addRow("", self.chk_verify)
        root.addWidget(self.g_opts)

        # --- Status
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.status = QLabel()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log.setMaximumHeight(110)
        root.addWidget(self.bar)
        root.addWidget(self.status)
        root.addWidget(self.log)

        row = QHBoxLayout()
        self.btn_start = QPushButton()
        self.btn_start.setDefault(True)
        self.btn_cancel = QPushButton()
        self.btn_cancel.setEnabled(False)
        self.btn_quit = QPushButton()
        row.addStretch(1)
        row.addWidget(self.btn_start)
        row.addWidget(self.btn_cancel)
        row.addWidget(self.btn_quit)
        root.addLayout(row)

        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        self.btn_refresh.clicked.connect(self.refresh_devices)
        self.chk_all.toggled.connect(self.refresh_devices)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        self.btn_browse.clicked.connect(self.browse)
        self.img_edit.textChanged.connect(self.on_image_changed)
        self.btn_hash.clicked.connect(self.compute_hash)
        self.btn_start.clicked.connect(self.start)
        self.btn_cancel.clicked.connect(self.cancel)
        self.btn_quit.clicked.connect(self.close)

        self.retranslate()

    # ------------------------------------------------------------ language
    def on_language_changed(self):
        set_lang(self.lang_combo.currentData())
        self.retranslate()

    def retranslate(self):
        """(Re)apply every visible text in the current language."""
        self._retranslating = True
        self.subtitle.setText(f"{tr('app_subtitle')}  -  v{__version__}  -  {AUTHOR}")
        self.lang_label.setText(tr("language"))
        self.g_dev.setTitle(tr("grp_device"))
        self.lbl_device.setText(tr("lbl_device"))
        self.btn_refresh.setText(tr("btn_refresh"))
        self.chk_all.setText(tr("chk_all"))
        self.g_boot.setTitle(tr("grp_boot"))
        self.lbl_mode.setText(tr("lbl_mode"))
        self.lbl_image.setText(tr("lbl_image"))
        self.lbl_checksum.setText(tr("lbl_checksum"))
        for i, (_, key) in enumerate(MODES):
            self.mode_combo.setItemText(i, tr(key))
        self.img_edit.setPlaceholderText(tr("ph_image"))
        self.btn_browse.setText(tr("btn_browse"))
        self.hash_expected.setPlaceholderText(tr("ph_hash"))
        self.btn_hash.setText(tr("btn_hash"))
        self.g_opts.setTitle(tr("grp_options"))
        self.lbl_scheme.setText(tr("lbl_scheme"))
        self.lbl_fs.setText(tr("lbl_fs"))
        self.lbl_label.setText(tr("lbl_label"))
        self.chk_verify.setText(tr("chk_verify"))
        self.btn_start.setText(tr("btn_start"))
        self.btn_cancel.setText(tr("btn_cancel"))
        self.btn_quit.setText(tr("btn_quit"))
        self.set_status(*self._status[:1], **self._status[1])
        self.render_hash()
        self._retranslating = False
        self.refresh_devices()
        self.on_mode_changed()

    # ------------------------------------------------------------ interface
    def set_status(self, key, **params):
        self._status = (key, params)
        self.status.setText(tr(key, **params))

    def refresh_devices(self):
        if getattr(self, "_retranslating", False):
            return
        current = self.dev_combo.currentData()
        self.dev_combo.clear()
        devs = list_devices(self.chk_all.isChecked())
        for text, path in devs:
            self.dev_combo.addItem(text, path)
        if devs:
            idx = self.dev_combo.findData(current)
            if idx >= 0:
                self.dev_combo.setCurrentIndex(idx)
        else:
            self.dev_combo.addItem(tr("no_device"), None)

    def on_mode_changed(self):
        if self._retranslating:
            return
        mode = self.mode_combo.currentData()
        self.mode_desc.setText(tr(dict(MODES)[mode] + "_desc"))
        needs_img = mode in ("image", "windows")
        for w in (self.img_edit, self.btn_browse, self.btn_hash, self.hash_expected):
            w.setEnabled(needs_img)
        fmt = mode in ("windows", "format")
        self.scheme_combo.setEnabled(fmt)
        self.label_edit.setEnabled(fmt)
        self.chk_verify.setEnabled(mode == "image")
        previous_fs = self.fs_combo.currentData()
        self.fs_combo.clear()
        if mode == "format":
            for text, v in (("FAT32", "fat32"), ("NTFS", "ntfs"), ("exFAT", "exfat"), ("ext4", "ext4")):
                self.fs_combo.addItem(text, v)
            idx = self.fs_combo.findData(previous_fs)
            if idx >= 0:
                self.fs_combo.setCurrentIndex(idx)
        else:
            self.fs_combo.addItem("FAT32" if mode == "windows" else tr("fs_na"), "fat32")
        self.fs_combo.setEnabled(mode == "format")
        self.on_image_changed()

    def on_image_changed(self):
        name = os.path.basename(self.img_edit.text()).lower()
        mode = self.mode_combo.currentData()
        self.hint.setText(tr("hint_windows_iso") if mode == "image" and "win" in name else "")

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dlg_select_image"), os.path.expanduser("~"),
            f"{tr('dlg_filter_images')};;{tr('dlg_filter_all')}")
        if path:
            self.img_edit.setText(path)

    def set_busy(self, busy):
        for w in (self.dev_combo, self.btn_refresh, self.chk_all, self.mode_combo, self.img_edit,
                  self.btn_browse, self.btn_hash, self.hash_expected, self.scheme_combo, self.fs_combo,
                  self.label_edit, self.chk_verify, self.btn_start, self.lang_combo):
            w.setEnabled(not busy)
        self.btn_cancel.setEnabled(busy)
        if not busy:
            self.on_mode_changed()

    def append_log(self, text):
        self.log.appendPlainText(text)

    # ------------------------------------------------------------- checksum
    def render_hash(self):
        view = self._hash_view
        if not view:
            self.hash_result.setText("")
        elif view[0] == "calc":
            self.hash_result.setText(tr("calculating"))
        elif view[0] == "err":
            self.hash_result.setText(tr("hash_error", err=view[1]))
        else:
            digest = view[1]
            expected = self.hash_expected.text().strip().lower()
            verdict = ""
            if expected:
                verdict = tr("hash_match") if expected == digest else tr("hash_mismatch")
            self.hash_result.setText(f"SHA256: {digest}{verdict}")

    def compute_hash(self):
        path = self.img_edit.text().strip()
        if not os.path.isfile(path):
            QMessageBox.warning(self, tr("checksum_title"), tr("select_image_first"))
            return
        self.btn_hash.setEnabled(False)
        self._hash_view = ("calc",)
        self.render_hash()
        self.hash_thread = HashThread(path)
        self.hash_thread.progress.connect(self.bar.setValue)
        self.hash_thread.result.connect(self.on_hash_done)
        self.hash_thread.start()

    def on_hash_done(self, digest):
        self.btn_hash.setEnabled(True)
        self.bar.setValue(0)
        if digest.startswith("ERR:"):
            self._hash_view = ("err", digest[4:])
        elif not digest:
            self._hash_view = None
        else:
            self._hash_view = ("ok", digest)
        self.render_hash()

    # ------------------------------------------------------------ execution
    def start(self):
        dev = self.dev_combo.currentData()
        mode = self.mode_combo.currentData()
        image = self.img_edit.text().strip()
        if not dev:
            QMessageBox.warning(self, APP_NAME, tr("no_device_selected"))
            return
        if mode in ("image", "windows") and not os.path.isfile(image):
            QMessageBox.warning(self, APP_NAME, tr("select_valid_image"))
            return
        if os.geteuid() != 0 and not shutil.which("pkexec"):
            QMessageBox.critical(self, APP_NAME, tr("pkexec_missing"))
            return
        if mode != "badblocks":
            r = QMessageBox.warning(
                self, tr("confirm_title"), tr("confirm_text", device=self.dev_combo.currentText()),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if r != QMessageBox.StandardButton.Yes:
                return

        spec = {
            "mode": mode, "device": dev, "image": image,
            "scheme": self.scheme_combo.currentData(), "fs": self.fs_combo.currentData(),
            "label": self.label_edit.text(), "verify": self.chk_verify.isChecked(),
        }
        fd, self.cancel_file = tempfile.mkstemp(prefix="rcfux-cancel-")
        os.close(fd)
        os.remove(self.cancel_file)

        self.buf, self.result = "", None
        self.bar.setValue(0)
        self.log.clear()
        self.set_status("waiting_auth")
        self.set_busy(True)

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self.on_output)
        self.proc.finished.connect(lambda code, _st: self.job_ended(code))
        self.proc.errorOccurred.connect(self.on_proc_error)
        args = [WORKER, json.dumps(spec), self.cancel_file]
        if os.geteuid() == 0:
            self.proc.start(sys.executable, args)
        else:
            self.proc.start("pkexec", [sys.executable] + args)

    def cancel(self):
        if self.cancel_file:
            open(self.cancel_file, "w").close()
            self.set_status("cancelling")
            self.btn_cancel.setEnabled(False)

    def on_output(self):
        self.buf += bytes(self.proc.readAllStandardOutput()).decode(errors="replace")
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            self.handle_line(line.strip())

    def handle_line(self, line):
        """Parse a worker message: KIND [key [json-params]]."""
        if not line:
            return
        kind, _, rest = line.partition(" ")
        key, _, raw = rest.partition(" ")
        try:
            params = json.loads(raw) if raw else {}
        except ValueError:
            params = {}
        if kind == "PROGRESS":
            try:
                self.bar.setValue(int(key))
            except ValueError:
                pass
        elif kind == "STATUS":
            self.set_status(key, **params)
            self.append_log(tr(key, **params))
        elif kind in ("DONE", "ERROR"):
            self.result = (kind, key, params)
        elif kind == "CANCELLED":
            self.result = ("CANCELLED", "", {})
        else:
            self.append_log(line)  # e.g. raw pkexec/polkit output

    def on_proc_error(self, err):
        if err == QProcess.ProcessError.FailedToStart:
            self.result = ("ERROR", "process_start_fail", {})
            self.job_ended(-1)

    def job_ended(self, code):
        if self.buf.strip():
            self.handle_line(self.buf.strip())
            self.buf = ""
        if self.cancel_file and os.path.exists(self.cancel_file):
            os.remove(self.cancel_file)
        self.cancel_file = None
        self.set_busy(False)
        self.refresh_devices()
        res = self.result
        if res is None:
            if code in (126, 127):
                res = ("ERROR", "auth_denied", {})
            else:
                res = ("ERROR", "unexpected_exit", {"code": code})
        kind, key, params = res
        if kind == "DONE":
            self.bar.setValue(100)
            self.set_status("status_done")
            QMessageBox.information(self, tr("done_title"), tr(key, **params))
        elif kind == "CANCELLED":
            self.set_status("status_cancelled")
        else:
            self.set_status("status_error")
            QMessageBox.critical(self, tr("err_title"), tr(key, **params))
        self.result = None

    def closeEvent(self, event):
        if self.proc and self.proc.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, APP_NAME, tr("busy_quit"))
            event.ignore()
            return
        if self.hash_thread and self.hash_thread.isRunning():
            self.hash_thread.abort = True
            self.hash_thread.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    if os.path.isfile(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    set_lang("it" if QLocale.system().name().startswith("it") else "en")
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
