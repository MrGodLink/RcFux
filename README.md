# RcFux

<img src="rcfux.svg" width="96" align="right" alt="RcFux logo">

**English** | [Italiano](README.it.md)

RcFux is a graphical (PySide6) utility to create bootable USB drives on Linux.
The interface is bilingual (English / Italian): it follows your system language and
can be switched from the window.

## Features
- Write ISO/IMG images in DD mode, with SHA-256 verification of the written data
- Windows FAT32 drives for UEFI boot (splits `install.wim` larger than 4 GB with wimlib)
- Format as FAT32 / NTFS / exFAT / ext4, with GPT or MBR partition scheme
- Bad blocks check (read-only, non-destructive)
- SHA-256 computation and comparison of the image
- The system disk is never listed, and the worker refuses it anyway

## Installation
System packages (Debian / Ubuntu / Kubuntu):

```bash
sudo apt install parted dosfstools ntfs-3g exfatprogs e2fsprogs wimtools util-linux pkexec libqt6svg6
```

PySide6 - pick one:

```bash
sudo apt install python3-pyside6.qtwidgets        # from the repositories, if available
# or, in a virtual environment:
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```

## Usage
```bash
git clone https://github.com/MrGodLink/RuFux.git
cd RuFux
python3 main.py
```

The GUI runs with your own permissions; disk operations are performed by `rcwk.py`
as root through `pkexec` (one password prompt per operation).

## Project layout
| File | Purpose |
|------|---------|
| `main.py` | Graphical interface |
| `rcwk.py` | Privileged worker (partitioning, writing, formatting) |
| `i18n.py` | English / Italian strings |
| `rcfux.svg` | Logo and window icon |

## Warning
All data on the selected device is permanently erased. Use at your own risk.

## Credits
Created by **Raffaele Catapano** - [github.com/MrGodLink](https://github.com/MrGodLink)

If you reuse, modify or redistribute this project, please keep the copyright notice and
credit the original author, as required by the MIT License.

### Other projects by the author
- [CISO-Converter](https://github.com/MrGodLink/CISO-Converter) - desktop tool (PySide6) to convert ISO to CSO and CSO to ISO, the compressed disc image format used by PSP and its emulators.

## License
The source code is released under the MIT License - see [LICENSE](LICENSE).

RcFux depends on [PySide6](https://doc.qt.io/qtforpython/), licensed under the LGPLv3 (or a Qt commercial license). It is installed separately (via `pip` or your distribution). If you distribute a bundled executable (for example built with PyInstaller), you must also comply with the LGPL terms for PySide6 and Qt.
