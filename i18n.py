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
"""i18n.py - UI strings for RcFux (English / Italian).

The privileged worker (rcwk.py) never sends human-readable text: it sends
message keys plus parameters, and the GUI translates them with tr().
"""

LANGUAGES = (("en", "English"), ("it", "Italiano"))
_lang = "en"

STRINGS = {
    "en": {
        "app_subtitle": "Create bootable USB drives on Linux",
        "language": "Language:",
        # groups / labels
        "grp_device": "Device", "lbl_device": "Device:", "btn_refresh": "Refresh",
        "chk_all": "Also show non-removable disks (dangerous)",
        "no_device": "No USB device found", "disk_generic": "Disk",
        "grp_boot": "Boot selection", "lbl_mode": "Mode:", "lbl_image": "Image:",
        "lbl_checksum": "Checksum:", "ph_image": "Select an .iso / .img file",
        "ph_hash": "Expected SHA256 (optional)", "btn_browse": "Browse...",
        "btn_hash": "Compute SHA256",
        "grp_options": "Formatting options", "lbl_scheme": "Partition scheme:",
        "lbl_fs": "File system:", "lbl_label": "Volume label:",
        "chk_verify": "Verify data after writing (DD mode)", "fs_na": "(not applicable)",
        "btn_start": "Start", "btn_cancel": "Cancel", "btn_quit": "Quit",
        # modes
        "mode_image": "ISO/IMG image (DD mode) - Linux and hybrid images",
        "mode_image_desc": "Copies the image byte by byte to the drive. Ideal for Linux, Kubuntu, etc.",
        "mode_windows": "Windows (file copy, UEFI boot)",
        "mode_windows_desc": "Creates a FAT32 Windows drive for UEFI boot; an install.wim larger than 4 GB is split with wimlib.",
        "mode_format": "Format only",
        "mode_format_desc": "Creates the partition table and formats the drive.",
        "mode_badblocks": "Bad blocks check",
        "mode_badblocks_desc": "Read-only, non-destructive test. It can take a long time.",
        "hint_windows_iso": "This looks like a Windows ISO: choose the \u00abWindows\u00bb mode, DD mode is usually not enough.",
        # dialogs
        "dlg_select_image": "Select image", "dlg_filter_images": "Disk images (*.iso *.img *.raw *.bin)",
        "dlg_filter_all": "All files (*)",
        "checksum_title": "Checksum", "select_image_first": "Please select a valid image file first.",
        "calculating": "Calculating...", "hash_error": "Error: {err}",
        "hash_match": "  \u2714 MATCHES", "hash_mismatch": "  \u2718 DOES NOT MATCH: the file may be corrupted!",
        "no_device_selected": "No device selected.", "select_valid_image": "Please select a valid image file.",
        "pkexec_missing": "pkexec not found. Install the 'pkexec' package (or 'policykit-1' on older distributions).",
        "confirm_title": "Confirm",
        "confirm_text": "ALL DATA on:\n\n{device}\n\nwill be PERMANENTLY ERASED.\n\nContinue?",
        "busy_quit": "An operation is in progress: cancel it before quitting.",
        # status
        "status_ready": "Ready.", "waiting_auth": "Waiting for authorization...",
        "cancelling": "Cancelling...", "status_done": "Completed.",
        "status_cancelled": "Operation cancelled.", "status_error": "Error.",
        "done_title": "Completed", "err_title": "Error",
        "auth_denied": "Authorization denied or cancelled.",
        "unexpected_exit": "The process stopped unexpectedly (code {code}).",
        "process_start_fail": "Unable to start the process (pkexec or Python not available).",
        # worker: status
        "st_unmount": "Unmounting partitions...", "st_writing": "Writing the image...",
        "st_syncing": "Syncing...", "st_verifying": "Verifying the written data...",
        "st_partition_table": "Creating the partition table...", "st_formatting": "Formatting {fs}...",
        "st_prepare": "Preparing the drive...", "st_format_fat32": "Formatting FAT32...",
        "st_mounting": "Mounting the ISO and the drive...",
        "st_splitting": "Splitting install.wim (this may take a few minutes)...",
        "st_copy": "Copying: {rel}", "st_sync_wait": "Syncing (do not remove the drive)...",
        "st_badblocks": "Reading blocks (non-destructive)...",
        # worker: results
        "done_image": "Image written successfully.",
        "done_image_verified": "Image written and verified successfully.",
        "done_format": "Formatting completed.", "done_windows": "Windows drive ready (UEFI boot).",
        "done_bad_none": "No bad blocks found.",
        "done_bad_found": "WARNING: {n} bad blocks found. It is better not to use this drive.",
        # worker: errors
        "cmd_not_found": "Command not found: {cmd}.",
        "cmd_not_found_pkg": "Command not found: {cmd}. Install the '{pkg}' package.",
        "cmd_failed": "{cmd}: {detail}", "bad_device": "Invalid device: {dev}",
        "not_disk": "The selected device is not a whole disk.",
        "system_device": "The device contains the operating system: operation refused.",
        "partition_missing": "Partition {path} did not appear.",
        "image_too_big": "The image is larger than the device.",
        "verify_short_read": "Incomplete read during verification.",
        "verify_failed": "Verification FAILED: the data on the drive does not match the image.",
        "not_windows_iso": "This does not look like a Windows ISO (missing 'sources' folder).",
        "file_too_big": "The file {rel} is larger than 4 GB and does not fit on FAT32.",
        "wimlib_failed": "wimlib-imagex failed: {detail}", "badblocks_failed": "badblocks failed: {detail}",
        "invalid_mode": "Invalid mode.", "invalid_params": "Invalid parameters.",
        "image_not_found": "Image file not found.", "root_required": "Root privileges are required.",
        "unexpected": "Unexpected error: {err}",
    },
    "it": {
        "app_subtitle": "Crea chiavette USB avviabili su Linux",
        "language": "Lingua:",
        "grp_device": "Dispositivo", "lbl_device": "Dispositivo:", "btn_refresh": "Aggiorna",
        "chk_all": "Mostra anche i dischi non rimovibili (pericoloso)",
        "no_device": "Nessun dispositivo USB trovato", "disk_generic": "Disco",
        "grp_boot": "Selezione di avvio", "lbl_mode": "Modalit\u00e0:", "lbl_image": "Immagine:",
        "lbl_checksum": "Checksum:", "ph_image": "Seleziona un file .iso / .img",
        "ph_hash": "SHA256 atteso (opzionale)", "btn_browse": "Sfoglia...",
        "btn_hash": "Calcola SHA256",
        "grp_options": "Opzioni di formattazione", "lbl_scheme": "Schema partizioni:",
        "lbl_fs": "File system:", "lbl_label": "Etichetta volume:",
        "chk_verify": "Verifica i dati dopo la scrittura (modalit\u00e0 DD)", "fs_na": "(non applicabile)",
        "btn_start": "Avvia", "btn_cancel": "Annulla", "btn_quit": "Esci",
        "mode_image": "Immagine ISO/IMG (modalit\u00e0 DD) - Linux e immagini ibride",
        "mode_image_desc": "Copia l'immagine byte per byte sulla chiavetta. Ideale per Linux, Kubuntu, ecc.",
        "mode_windows": "Windows (copia file, avvio UEFI)",
        "mode_windows_desc": "Crea una chiavetta Windows FAT32 per avvio UEFI; un install.wim oltre 4 GB viene diviso con wimlib.",
        "mode_format": "Solo formattazione",
        "mode_format_desc": "Crea la tabella delle partizioni e formatta la chiavetta.",
        "mode_badblocks": "Controllo blocchi danneggiati",
        "mode_badblocks_desc": "Test di sola lettura, non distruttivo. Pu\u00f2 richiedere parecchio tempo.",
        "hint_windows_iso": "Sembra un'ISO di Windows: scegli la modalit\u00e0 \u00abWindows\u00bb, la modalit\u00e0 DD di solito non basta.",
        "dlg_select_image": "Seleziona immagine", "dlg_filter_images": "Immagini disco (*.iso *.img *.raw *.bin)",
        "dlg_filter_all": "Tutti i file (*)",
        "checksum_title": "Checksum", "select_image_first": "Seleziona prima un file immagine valido.",
        "calculating": "Calcolo in corso...", "hash_error": "Errore: {err}",
        "hash_match": "  \u2714 CORRISPONDE", "hash_mismatch": "  \u2718 NON CORRISPONDE: il file potrebbe essere corrotto!",
        "no_device_selected": "Nessun dispositivo selezionato.", "select_valid_image": "Seleziona un file immagine valido.",
        "pkexec_missing": "pkexec non trovato. Installa il pacchetto 'pkexec' (o 'policykit-1' sulle distribuzioni pi\u00f9 datate).",
        "confirm_title": "Conferma",
        "confirm_text": "TUTTI I DATI su:\n\n{device}\n\nverranno CANCELLATI in modo definitivo.\n\nContinuare?",
        "busy_quit": "Un'operazione \u00e8 in corso: annullala prima di uscire.",
        "status_ready": "Pronto.", "waiting_auth": "In attesa dell'autorizzazione...",
        "cancelling": "Annullamento in corso...", "status_done": "Completato.",
        "status_cancelled": "Operazione annullata.", "status_error": "Errore.",
        "done_title": "Completato", "err_title": "Errore",
        "auth_denied": "Autorizzazione negata o annullata.",
        "unexpected_exit": "Il processo si \u00e8 interrotto in modo inatteso (codice {code}).",
        "process_start_fail": "Impossibile avviare il processo (pkexec o Python non disponibili).",
        "st_unmount": "Smonto le partizioni...", "st_writing": "Scrittura dell'immagine...",
        "st_syncing": "Sincronizzazione...", "st_verifying": "Verifica dei dati scritti...",
        "st_partition_table": "Creazione della tabella delle partizioni...", "st_formatting": "Formattazione {fs}...",
        "st_prepare": "Preparazione della chiavetta...", "st_format_fat32": "Formattazione FAT32...",
        "st_mounting": "Monto l'ISO e la chiavetta...",
        "st_splitting": "Divisione di install.wim (pu\u00f2 richiedere alcuni minuti)...",
        "st_copy": "Copia: {rel}", "st_sync_wait": "Sincronizzazione (non rimuovere la chiavetta)...",
        "st_badblocks": "Test di lettura dei blocchi (non distruttivo)...",
        "done_image": "Immagine scritta correttamente.",
        "done_image_verified": "Immagine scritta e verificata correttamente.",
        "done_format": "Formattazione completata.", "done_windows": "Chiavetta Windows pronta (avvio UEFI).",
        "done_bad_none": "Nessun blocco danneggiato trovato.",
        "done_bad_found": "ATTENZIONE: trovati {n} blocchi danneggiati. Meglio non usare questa chiavetta.",
        "cmd_not_found": "Comando non trovato: {cmd}.",
        "cmd_not_found_pkg": "Comando non trovato: {cmd}. Installa il pacchetto '{pkg}'.",
        "cmd_failed": "{cmd}: {detail}", "bad_device": "Dispositivo non valido: {dev}",
        "not_disk": "Il dispositivo scelto non \u00e8 un disco intero.",
        "system_device": "Il dispositivo contiene il sistema operativo: operazione rifiutata.",
        "partition_missing": "La partizione {path} non \u00e8 comparsa.",
        "image_too_big": "L'immagine \u00e8 pi\u00f9 grande del dispositivo.",
        "verify_short_read": "Lettura incompleta durante la verifica.",
        "verify_failed": "Verifica FALLITA: i dati sulla chiavetta non coincidono con l'immagine.",
        "not_windows_iso": "Questa non sembra un'ISO di Windows (manca la cartella 'sources').",
        "file_too_big": "Il file {rel} supera 4 GB e non entra in FAT32.",
        "wimlib_failed": "wimlib-imagex ha fallito: {detail}", "badblocks_failed": "badblocks ha fallito: {detail}",
        "invalid_mode": "Modalit\u00e0 non valida.", "invalid_params": "Parametri non validi.",
        "image_not_found": "File immagine non trovato.", "root_required": "Servono i privilegi di root.",
        "unexpected": "Errore inatteso: {err}",
    },
}


def set_lang(code):
    global _lang
    _lang = code if code in STRINGS else "en"


def get_lang():
    return _lang


def tr(key, **kw):
    text = STRINGS[_lang].get(key) or STRINGS["en"].get(key) or key
    try:
        return text.format(**kw) if kw else text
    except (KeyError, IndexError, ValueError):
        return text
