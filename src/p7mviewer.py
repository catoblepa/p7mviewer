#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Davide Truffa <davide@catoblepa.org>

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio
import subprocess
import os
import sys
import io
import contextlib
from pathlib import Path

from signature_parser import analizza_busta

# Debug mode: controllabile via variabile d'ambiente P7MVIEWER_DEBUG=true
DEBUG = os.getenv('P7MVIEWER_DEBUG', 'false').lower() in ('true', '1', 'yes')

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

class FirmeApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="io.github.catoblepa.p7mviewer",
            flags=Gio.ApplicationFlags.HANDLES_OPEN
        )
        debug_print("[DEBUG] Applicazione inizializzata")
        
    def do_activate(self):
        debug_print("[DEBUG] do_activate chiamato")
        win = FirmeWindow(self)
        win.present()

    def do_open(self, files, n_files, hint):
        debug_print(f"[DEBUG] do_open chiamato con {n_files} file")
        file_path = files[0].get_path() if n_files > 0 else None
        win = FirmeWindow(self, file_path)
        win.present()

class FirmeWindow(Gtk.ApplicationWindow):
    def __init__(self, app, file_p7m=None):
        super().__init__(application=app)
        debug_print("[DEBUG] Creazione finestra principale")
        self.set_title("P7M Viewer")
        self.set_icon_name("io.github.catoblepa.p7mviewer")
        self.file_estratto = None
        self.file_verificato = False

        headerbar = Gtk.HeaderBar()
        title_label = Gtk.Label()
        title_label.set_markup("<b>P7M Viewer</b>")
        headerbar.set_title_widget(title_label)

        btn_apri = Gtk.Button.new_with_label("📁 Seleziona file")
        btn_apri.connect("clicked", self.on_file_chooser_clicked)
        btn_apri.set_tooltip_text("Seleziona un file P7M da verificare")
        headerbar.pack_start(btn_apri)

        self.btn_apri_estratto = Gtk.Button.new_with_label("📄 Visualizza contenuto")
        self.btn_apri_estratto.set_sensitive(False)
        self.btn_apri_estratto.connect("clicked", self.on_apri_estratto_clicked)
        self.btn_apri_estratto.set_tooltip_text("Apri il documento originale estratto dal file firmato")
        headerbar.pack_end(self.btn_apri_estratto)

        self.set_titlebar(headerbar)
        self.set_default_size(700, 400)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(self.vbox)

        # SEZIONE 1: Box per file verificato con margini
        self.file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.file_box.set_margin_top(12)
        self.file_box.set_margin_bottom(8)
        self.file_box.set_margin_start(16)
        self.file_box.set_margin_end(16)

        self.label_info_file = Gtk.Label()
        self.label_info_file.set_markup('<span size="small" color="#999999">🔒 Nessun file selezionato</span>')
        self.label_info_file.set_halign(Gtk.Align.START)
        self.label_info_file.set_selectable(False)
        self.label_info_file.set_wrap(True)
        self.label_info_file.set_xalign(0)
        self.file_box.append(self.label_info_file)
        
        # Badge stato verifica (inizialmente nascosto)
        self.status_badge = Gtk.Label()
        self.status_badge.set_halign(Gtk.Align.START)
        self.status_badge.set_visible(False)
        self.status_badge.set_margin_top(6)
        self.file_box.append(self.status_badge)
        
        self.vbox.append(self.file_box)
        
        # Separatore tra sezioni
        separator_sezioni = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator_sezioni.set_margin_top(20)
        separator_sezioni.set_margin_bottom(16)
        separator_sezioni.set_margin_start(16)
        separator_sezioni.set_margin_end(16)
        self.vbox.append(separator_sezioni)

        # SEZIONE 2: Titolo firme
        self.label_firme_title = Gtk.Label()
        self.label_firme_title.set_markup('<span size="small" weight="bold" color="#336699">FIRME DIGITALI:</span>')
        self.label_firme_title.set_halign(Gtk.Align.START)
        self.label_firme_title.set_margin_top(8)
        self.label_firme_title.set_margin_bottom(6)
        self.label_firme_title.set_margin_start(16)
        self.label_firme_title.set_margin_end(16)
        self.vbox.append(self.label_firme_title)
        
        # Separatore dopo titolo firme
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator2.set_margin_bottom(8)
        separator2.set_margin_start(16)
        separator2.set_margin_end(16)
        self.vbox.append(separator2)

        # SEZIONE 3: Elenco firme con expander (scrollabile)
        self.firme_listbox = Gtk.ListBox()
        self.firme_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.firme_listbox.add_css_class('boxed-list')
        self.firme_listbox.set_hexpand(True)
        self.firme_listbox.set_vexpand(True)

        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_min_content_height(100)
        self.scrolled.set_hexpand(True)
        self.scrolled.set_vexpand(True)
        self.scrolled.set_child(self.firme_listbox)
        self.vbox.append(self.scrolled)

        # Immagine e label iniziale
        self.image = Gtk.Image.new_from_icon_name("application-certificate")
        self.image.set_pixel_size(96)
        self.image.set_margin_top(24)
        self.image.set_opacity(0.5)

        self.label = Gtk.Label()
        self.label.set_margin_top(24)
        self.label.set_markup('<span size="large"><b>📄 Seleziona un file .p7m da verificare</b></span>\n\n<span size="small" color="#666666">Clicca su "📁 Seleziona file" per cominciare</span>')
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)

        self.aggiorna_ui()

        if file_p7m:
            debug_print(f"[DEBUG] File passato all'avvio: {file_p7m}")
            self.verifica_firma(file_p7m)

    def aggiorna_ui(self):
        debug_print(f"[DEBUG] aggiorna_ui chiamato, file_verificato={self.file_verificato}")
        for child in list(self.vbox):
            self.vbox.remove(child)
        if not self.file_verificato:
            self.vbox.append(self.image)
            self.vbox.append(self.label)
        else:
            self.vbox.append(self.file_box)
            self.vbox.append(self.label_firme_title)
            self.vbox.append(self.scrolled)

    def on_file_chooser_clicked(self, widget):
        debug_print("[DEBUG] Pulsante 'Apri' cliccato, apro file dialog")
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Seleziona un file .p7m da verificare")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filter_p7m = Gtk.FileFilter()
        filter_p7m.set_name("File firmati digitalmente (.p7m)")
        filter_p7m.add_pattern("*.p7m")
        filter_p7m.add_pattern("*.P7M")
        filters.append(filter_p7m)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("Tutti i file")
        filter_all.add_pattern("*")
        filters.append(filter_all)
        
        file_dialog.set_filters(filters)

        def on_file_selected(dialog, result):
            try:
                file = dialog.open_finish(result)
                if file:
                    file_p7m = file.get_path()
                    debug_print(f"[DEBUG] File selezionato: {file_p7m}")
                    self.pulisci_sezioni()
                    self.verifica_firma(file_p7m)
            except GLib.Error as e:
                # Utente ha annullato la selezione
                if e.code != 2:  # GTK_DIALOG_ERROR_DISMISSED
                    debug_print(f"[DEBUG] Errore apertura file: {e}")
                    self.label_info_file.set_markup(f'<span size="small" color="#c62828">❌ Errore selezione file: {str(e)[:100]}</span>')
                self.file_verificato = False
                self.aggiorna_ui()

        file_dialog.open(self, None, on_file_selected)

    def pulisci_listbox(self):
        """Helper per pulire tutti i widget dalla listbox"""
        while True:
            row = self.firme_listbox.get_row_at_index(0)
            if row is None:
                break
            self.firme_listbox.remove(row)
    
    def pulisci_sezioni(self):
        debug_print("[DEBUG] pulisci_sezioni chiamato")
        self.label_info_file.set_markup('<span size="small" color="#999999">🔒 Nessun file selezionato</span>')
        self.status_badge.set_visible(False)
        self.pulisci_listbox()

    def verifica_firma(self, file_p7m):
        debug_print(f"[DEBUG] verifica_firma chiamato con file: {file_p7m}")
        self.pulisci_sezioni()
        self.btn_apri_estratto.set_sensitive(False)
        self.file_estratto = None
        self.file_verificato = False
        self.aggiorna_ui()

        # Crea una directory nella cache accessibile dal sandbox
        cache_dir = os.path.join(GLib.get_user_cache_dir(), 'p7mviewer')
        os.makedirs(cache_dir, exist_ok=True)
        debug_print(f"[DEBUG] Directory cache: {cache_dir}")

        # Nome file estratto senza .p7m
        base_path = Path(file_p7m)
        base_name = base_path.name
        while base_name.lower().endswith('.p7m'):
            base_name = base_name[:-4]
        base_name = base_name.strip()
        file_output = os.path.join(cache_dir, base_name)
        debug_print(f"[DEBUG] File estratto sarà: {file_output}")

        cmd = [
            "openssl", "smime", "-verify",
            "-in", file_p7m,
            "-inform", "DER",
            "-noverify",
            "-out", file_output
        ]

        # Formatta info file
        nome_file = os.path.basename(file_p7m)
        percorso_dir = os.path.dirname(file_p7m)
        file_markup = f'<span size="small" color="#666666">📂 {percorso_dir}</span>\n<span size="medium" weight="bold">{nome_file}</span>'
        self.label_info_file.set_markup(file_markup)

        try:
            debug_print(f"[DEBUG] Eseguo comando: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            debug_print(f"[DEBUG] Return code: {result.returncode}")
            debug_print(f"[DEBUG] stdout: {result.stdout}")
            debug_print(f"[DEBUG] stderr: {result.stderr}")
            if result.returncode == 0:
                self.file_estratto = file_output
                debug_print(f"[DEBUG] File estratto impostato a: {self.file_estratto}")
                self.btn_apri_estratto.set_sensitive(True)
                self.file_verificato = True
                self.aggiorna_ui()
                # Mostra badge successo
                self.label_info_file.set_markup(file_markup)
                self.status_badge.set_markup('<span size="small" bgcolor="#e8f5e9" color="#2e7d32"> ✓ Verifica completata con successo </span>')
                self.status_badge.set_visible(True)
                self.mostra_info_firma(file_p7m)
            else:
                # Errore nella verifica - mostra interfaccia con messaggio
                self.file_verificato = True
                self.aggiorna_ui()
                self.label_info_file.set_markup(file_markup)
                self.status_badge.set_markup('<span size="small" bgcolor="#ffebee" color="#c62828"> ❌ Errore nella verifica </span>')
                self.status_badge.set_visible(True)
                # Mostra messaggio di errore nella listbox
                self.mostra_errore_verifica(result.stderr)
                debug_print(f"[DEBUG] Errore openssl: {result.stderr}")
        except Exception as e:
            # Eccezione - mostra interfaccia con messaggio
            self.file_verificato = True
            self.aggiorna_ui()
            self.label_info_file.set_markup(file_markup)
            self.status_badge.set_markup(f'<span size="small" bgcolor="#ffebee" color="#c62828"> ❌ Errore: {str(e)[:50]} </span>')
            self.status_badge.set_visible(True)
            # Mostra messaggio di errore nella listbox
            self.mostra_errore_verifica(str(e))
            debug_print(f"[DEBUG] Eccezione in verifica_firma: {e}")

    def crea_expander_firma(self, info, idx):
        """Crea un expander per una singola firma con dettagli espandibili"""
        identita = info.get('Identità', 'Sconosciuto')
        stato = info.get('Stato certificato', '')
        
        expander = Gtk.Expander()
        expander.set_margin_top(4)
        expander.set_margin_bottom(4)
        expander.set_margin_start(8)
        expander.set_margin_end(8)
        
        # Header sempre visibile
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        
        title_label = Gtk.Label()
        title_label.set_markup(f'<b>🖊️ {identita}</b>')
        title_label.set_halign(Gtk.Align.START)
        header_box.append(title_label)
        
        subtitle = Gtk.Label()
        subtitle.set_markup(f'<span size="small" color="#666">{stato}</span>')
        subtitle.set_halign(Gtk.Align.START)
        header_box.append(subtitle)
        
        expander.set_label_widget(header_box)
        
        # Contenuto espandibile (dettagli)
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        details_box.set_margin_top(8)
        details_box.set_margin_start(12)
        
        # Campi da mostrare quando espanso
        campi_dettagli = [
            ('Codice Fiscale', '🆔'),
            ('Organizzazione', '🏢'),
            ('Data e ora firma', '📅'),
            ('Firma valida al momento', '✔️'),
            ('Validità dal', '📆'),
            ('Validità al', '📆'),
            ('Certificato emesso da', '🏛️'),
        ]
        
        for campo, icona in campi_dettagli:
            if campo in info:
                valore = info[campo]
                detail_label = Gtk.Label()
                detail_label.set_markup(f'<span size="small">{icona} <b>{campo}:</b> {valore}</span>')
                detail_label.set_halign(Gtk.Align.START)
                detail_label.set_wrap(True)
                detail_label.set_xalign(0)
                details_box.append(detail_label)
        
        expander.set_child(details_box)
        return expander
    
    def mostra_info_firma(self, file_p7m):
        debug_print(f"[DEBUG] mostra_info_firma chiamato per file: {file_p7m}")
        self.pulisci_listbox()
        try:
            with open(file_p7m, 'rb') as f:
                data = f.read()
            firme_info = analizza_busta(data)
            
            if not firme_info:
                # Messaggio quando non ci sono firme
                no_firme_label = Gtk.Label()
                no_firme_label.set_markup('<span size="small" color="#999">⚠️  Nessuna firma digitale trovata nel file</span>')
                no_firme_label.set_margin_top(20)
                no_firme_label.set_margin_bottom(20)
                self.firme_listbox.append(no_firme_label)
                return
            
            # Aggiungi ogni firma come expander
            for idx, info in enumerate(firme_info, 1):
                expander = self.crea_expander_firma(info, idx)
                self.firme_listbox.append(expander)
            
            # Aggiungi footer con conteggio
            footer_label = Gtk.Label()
            footer_label.set_markup(f'<span size="small" color="#666">✓ Totale: {len(firme_info)} firma/e verificata/e</span>')
            footer_label.set_margin_top(12)
            footer_label.set_margin_bottom(8)
            self.firme_listbox.append(footer_label)
            
            debug_print(f"[DEBUG] Informazioni firma mostrate per {file_p7m}")
        except Exception as e:
            self.pulisci_listbox()
            error_label = Gtk.Label()
            error_label.set_markup(f'<span color="#c62828">❌ Errore durante l\'analisi delle firme:\n\n{str(e)}</span>')
            error_label.set_margin_top(20)
            error_label.set_margin_bottom(20)
            self.firme_listbox.append(error_label)
            debug_print(f"[DEBUG] Eccezione in mostra_info_firma: {e}")
    
    def mostra_errore_verifica(self, errore):
        """Mostra un messaggio di errore nella listbox delle firme"""
        self.pulisci_listbox()
        
        error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        error_box.set_margin_top(30)
        error_box.set_margin_bottom(30)
        error_box.set_margin_start(20)
        error_box.set_margin_end(20)
        
        # Titolo
        title_label = Gtk.Label()
        title_label.set_markup('<span size="large">❌</span>\n<span size="large" weight="bold">Impossibile verificare il file</span>')
        title_label.set_justify(Gtk.Justification.CENTER)
        error_box.append(title_label)
        
        # Messaggio
        msg_label = Gtk.Label()
        msg_label.set_markup('<span color="#666">Il file selezionato non è un file P7M valido\no non può essere processato.</span>')
        msg_label.set_justify(Gtk.Justification.CENTER)
        msg_label.set_wrap(True)
        error_box.append(msg_label)
        
        # Dettagli tecnici
        if errore:
            errore_pulito = errore.split('\n')[0] if '\n' in errore else errore
            if 'Error reading S/MIME message' in errore:
                errore_pulito = "Il file non è in formato P7M/CAdES valido"
            
            details_expander = Gtk.Expander(label="Dettagli tecnici")
            details_expander.set_margin_top(12)
            
            details_label = Gtk.Label()
            details_label.set_markup(f'<span size="small" font_family="monospace" color="#999">{errore_pulito}</span>')
            details_label.set_wrap(True)
            details_label.set_xalign(0)
            details_label.set_margin_start(12)
            details_label.set_margin_top(8)
            details_expander.set_child(details_label)
            error_box.append(details_expander)
        
        self.firme_listbox.append(error_box)

    def on_apri_estratto_clicked(self, widget):
        debug_print(f"[DEBUG] Cliccato su 'Apri file estratto'. file_estratto = {self.file_estratto}")
        if self.file_estratto:
            debug_print(f"[DEBUG] Verifico esistenza file: {self.file_estratto}")
            if os.path.exists(self.file_estratto):
                debug_print("[DEBUG] File esiste, uso Gtk.FileLauncher per aprirlo")
                try:
                    gfile = Gio.File.new_for_path(self.file_estratto)
                    launcher = Gtk.FileLauncher.new(gfile)
                    debug_print(f"[DEBUG] FileLauncher creato per: {self.file_estratto}")
                    
                    def on_launch_finish(launcher, result):
                        try:
                            launcher.launch_finish(result)
                            debug_print("[DEBUG] File aperto con successo tramite portal")
                        except Exception as e:
                            debug_print(f"[DEBUG] Errore apertura file: {e}")
                            self.label_info_file.set_markup(f'<span size="small" color="#c62828">❌ Errore apertura: {str(e)[:100]}</span>')
                    
                    launcher.launch(self, None, on_launch_finish)
                except Exception as e:
                    self.label_info_file.set_markup(f'<span size="small" color="#c62828">❌ Errore apertura file: {str(e)[:100]}</span>')
                    debug_print(f"[DEBUG] Eccezione in on_apri_estratto_clicked: {e}")
            else:
                debug_print(f"[DEBUG] File NON esiste: {self.file_estratto}")
                self.label_info_file.set_markup(f'<span size="small" color="#c62828">❌ Il file estratto non esiste più</span>')
        else:
            debug_print("[DEBUG] file_estratto non impostato.")
            self.label_info_file.set_markup('<span size="small" color="#f57c00">⚠️ Nessun file estratto disponibile</span>')

def main():
    debug_print("[DEBUG] main() chiamato")
    app = FirmeApp()
    app.run(sys.argv)

if __name__ == "__main__":
    main()
