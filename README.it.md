# RcFux

<img src="rcfux.svg" width="96" align="right" alt="Logo RcFux">

[English](README.md) | **Italiano**

RcFux è un'utility grafica (PySide6) per creare chiavette USB avviabili su Linux.
L'interfaccia è bilingue (inglese / italiano): segue la lingua del sistema e si può
cambiare dalla finestra.

## Funzioni
- Scrittura di immagini ISO/IMG in modalità DD, con verifica SHA-256 dei dati scritti
- Chiavette Windows FAT32 per avvio UEFI (divide `install.wim` oltre 4 GB con wimlib)
- Formattazione FAT32 / NTFS / exFAT / ext4, con schema di partizioni GPT o MBR
- Controllo dei blocchi danneggiati (sola lettura, non distruttivo)
- Calcolo e confronto SHA-256 dell'immagine
- Il disco di sistema non viene mai mostrato e il worker lo rifiuta comunque

## Installazione
Pacchetti di sistema (Debian / Ubuntu / Kubuntu):

```bash
sudo apt install parted dosfstools ntfs-3g exfatprogs e2fsprogs wimtools util-linux pkexec libqt6svg6
```

PySide6 - scegli una opzione:

```bash
sudo apt install python3-pyside6.qtwidgets        # dai repository, se disponibile
# oppure, in un ambiente virtuale:
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```

## Uso
```bash
git clone https://github.com/MrGodLink/RuFux.git
cd RuFux
python3 main.py
```

La GUI gira con i permessi dell'utente; le operazioni sul disco sono eseguite da `rcwk.py`
come root tramite `pkexec` (una richiesta di password per operazione).

## Struttura del progetto
| File | Scopo |
|------|-------|
| `main.py` | Interfaccia grafica |
| `rcwk.py` | Worker privilegiato (partizionamento, scrittura, formattazione) |
| `i18n.py` | Testi in inglese / italiano |
| `rcfux.svg` | Logo e icona della finestra |

## Attenzione
Tutti i dati sul dispositivo scelto vengono cancellati in modo definitivo. Usare a proprio rischio.

## Crediti
Creato da **Raffaele Catapano** - [github.com/MrGodLink](https://github.com/MrGodLink)

Se riutilizzi, modifichi o ridistribuisci questo progetto, mantieni la nota di copyright e
cita l'autore originale, come richiesto dalla licenza MIT.

### Altri progetti dell'autore
- [CISO-Converter](https://github.com/MrGodLink/CISO-Converter) - strumento desktop (PySide6) per convertire ISO in CSO e CSO in ISO, il formato di immagine disco compresso usato da PSP e dai suoi emulatori.

## Licenza
Il codice sorgente è rilasciato con licenza MIT - vedi [LICENSE](LICENSE).

RcFux dipende da [PySide6](https://doc.qt.io/qtforpython/), con licenza LGPLv3 (oppure licenza commerciale Qt). Viene installato separatamente (con `pip` o dalla distribuzione). Se distribuisci un eseguibile incorporato (per esempio creato con PyInstaller), devi rispettare anche i termini LGPL di PySide6 e Qt.
