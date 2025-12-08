#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 Davide Truffa <davide@catoblepa.org>

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gio, Gdk
import subprocess
import os
import sys
from pathlib import Path
import gettext
import locale

from signature_parser import analizza_busta

# Setup localization
APP_ID = "io.github.catoblepa.p7mviewer"
LOCALE_DIR = '/app/share/locale' if os.path.exists('/app/share/locale') else \
            os.path.join(os.path.dirname(__file__), 'locale')

try:
    locale.setlocale(locale.LC_ALL, '')
    locale.bindtextdomain(APP_ID, LOCALE_DIR)
    locale.textdomain(APP_ID)
except:
    pass

gettext.bindtextdomain(APP_ID, LOCALE_DIR)
gettext.textdomain(APP_ID)
_ = gettext.gettext

# Debug mode
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
        debug_print("[DEBUG] Application initialized")
        
    def do_activate(self):
        debug_print("[DEBUG] do_activate called")
        win = FirmeWindow(self)
        win.present()

    def do_open(self, files, n_files, hint):
        debug_print(f"[DEBUG] do_open called with {n_files} file(s)")
        file_path = files[0].get_path() if n_files > 0 else None
        win = FirmeWindow(self, file_path)
        win.present()

class FirmeWindow(Gtk.ApplicationWindow):
    def __init__(self, app, file_p7m=None):
        super().__init__(application=app)
        debug_print("[DEBUG] Creating main window")
        self.set_title("P7M Viewer")
        self.set_icon_name("io.github.catoblepa.p7mviewer")
        self.file_estratto = None
        self.file_verificato = False

        # Headerbar
        self._setup_headerbar()
        
        # Main layout
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(self.vbox)
        self.set_default_size(700, 400)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_margin_start(10)
        self.set_margin_end(10)

        # UI components
        self._setup_ui_components()
        
        # Initial state
        self.aggiorna_ui()

        # Drag and drop
        self._setup_drag_drop()

        # Load file if passed
        if file_p7m:
            debug_print(f"[DEBUG] File passed at startup: {file_p7m}")
            self.verifica_firma(file_p7m)

    def _setup_headerbar(self):
        """Setup headerbar with buttons"""
        headerbar = Gtk.HeaderBar()
        title_label = Gtk.Label(label="<b>P7M Viewer</b>")
        title_label.set_use_markup(True)
        headerbar.set_title_widget(title_label)

        # Open button
        self.btn_apri = Gtk.Button.new_with_label(_("📁 Select file"))
        self.btn_apri.connect("clicked", self.on_file_chooser_clicked)
        self.btn_apri.set_tooltip_text(_("Select a P7M file to verify"))
        headerbar.pack_start(self.btn_apri)

        # View extracted button
        self.btn_apri_estratto = Gtk.Button.new_with_label(_("📄 View content"))
        self.btn_apri_estratto.set_sensitive(False)
        self.btn_apri_estratto.connect("clicked", self.on_apri_estratto_clicked)
        self.btn_apri_estratto.set_tooltip_text(_("Open the original document extracted from the signed file"))
        headerbar.pack_end(self.btn_apri_estratto)

        self.set_titlebar(headerbar)

    def _setup_ui_components(self):
        """Setup all UI labels and containers"""
        # File info box
        self.file_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.file_box.set_margin_top(12)
        self.file_box.set_margin_bottom(8)
        self.file_box.set_margin_start(16)
        self.file_box.set_margin_end(16)

        self.label_info_file = Gtk.Label()
        self.label_info_file.set_halign(Gtk.Align.START)
        self.label_info_file.set_wrap(True)
        self.label_info_file.set_xalign(0)
        
        self.status_badge = Gtk.Label()
        self.status_badge.set_halign(Gtk.Align.START)
        self.status_badge.set_visible(False)
        self.status_badge.set_margin_top(6)
        
        self.file_box.append(self.label_info_file)
        self.file_box.append(self.status_badge)

        # Separators and titles
        separator_sezioni = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator_sezioni.set_margin_top(20)
        separator_sezioni.set_margin_bottom(16)
        separator_sezioni.set_margin_start(16)
        separator_sezioni.set_margin_end(16)

        self.label_firme_title = Gtk.Label()
        self.label_firme_title.set_markup(f'<span size="small" weight="bold" color="#336699">{_("DIGITAL SIGNATURES:")}</span>')
        self.label_firme_title.set_halign(Gtk.Align.START)
        self.label_firme_title.set_margin_top(8)
        self.label_firme_title.set_margin_bottom(6)
        self.label_firme_title.set_margin_start(16)
        self.label_firme_title.set_margin_end(16)

        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator2.set_margin_bottom(8)
        separator2.set_margin_start(16)
        separator2.set_margin_end(16)

        # Signatures list
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

        # Empty state
        self.image = Gtk.Image.new_from_icon_name("application-certificate")
        self.image.set_pixel_size(96)
        self.image.set_margin_top(24)
        self.image.set_opacity(0.5)

        self.label = Gtk.Label()
        self.label.set_markup(f'<span size="large"><b>📄 {_("Select a .p7m file to verify")}</b></span>\n\n<span size="small" color="#666666">{_("Click on")}</span> <span size="small" color="#666666">"📁 {_("Select file")}"</span> <span size="small" color="#666666">{_("to start")}</span>')
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.CENTER)

    def _setup_drag_drop(self):
        """Setup drag and drop with FileTransfer Portal"""
        debug_print("[DEBUG] Initializing DropTarget for drag and drop")
        drop_target = Gtk.DropTarget.new(Gio.File, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_file_drop)
        self.add_controller(drop_target)

    def mostra_stato_file(self, tipo="info", messaggio=""):
        """Gestisce tutti gli stati del file in modo coerente"""
        self.file_verificato = tipo != "info"
        self.aggiorna_ui()
        
        if tipo == "success":
            self.status_badge.set_markup(f'<span size="small" bgcolor="#e8f5e9" color="#2e7d32"> ✓ {messaggio} </span>')
            self.status_badge.set_visible(True)
        elif tipo == "error":
            self.status_badge.set_markup(f'<span size="small" bgcolor="#ffebee" color="#c62828"> ❌ {messaggio} </span>')
            self.status_badge.set_visible(True)
        else:
            self.status_badge.set_visible(False)

    def aggiorna_ui(self):
        """Update UI based on verification state"""
        debug_print(f"[DEBUG] aggiorna_ui called, file_verificato={self.file_verificato}")
        for child in list(self.vbox):
            self.vbox.remove(child)
            
        if not self.file_verificato:
            self.vbox.append(self.image)
            self.vbox.append(self.label)
        else:
            self.vbox.append(self.file_box)
            self.vbox.append(self.label_firme_title)
            self.vbox.append(self.scrolled)

    def on_file_drop(self, drop_target, value, x, y):
        """Handle drag and drop file"""
        debug_print(f"[DEBUG] Drop event received: value={value!r}")
        if not value:
            self.mostra_stato_file("error", _("File not accessible"))
            return False
        
        file_path = value.get_path()
        debug_print(f"[DEBUG] File path from Gio.File: {file_path}")
        
        if not file_path or not os.access(file_path, os.R_OK):
            self.mostra_stato_file("error", _("File not accessible"))
            return False
        
        self.pulisci_sezioni()
        self.verifica_firma(file_path)
        return True

    def on_file_chooser_clicked(self, widget):
        """Open file chooser dialog"""
        debug_print("[DEBUG] File chooser clicked")
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title(_("Select a .p7m file to verify"))
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filter_p7m = Gtk.FileFilter()
        filter_p7m.set_name(_("Digitally signed files (.p7m)"))
        filter_p7m.add_pattern("*.p7m")
        filter_p7m.add_pattern("*.P7M")
        filters.append(filter_p7m)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name(_("All files"))
        filter_all.add_pattern("*")
        filters.append(filter_all)
        
        file_dialog.set_filters(filters)

        def on_file_selected(dialog, result):
            try:
                file = dialog.open_finish(result)
                if file:
                    file_p7m = file.get_path()
                    debug_print(f"[DEBUG] File selected: {file_p7m}")
                    self.pulisci_sezioni()
                    self.verifica_firma(file_p7m)
            except GLib.Error as e:
                if e.code != 2:  # Not cancelled
                    debug_print(f"[DEBUG] File open error: {e}")
                    self.mostra_stato_file("error", str(e)[:100])

        file_dialog.open(self, None, on_file_selected)

    def pulisci_sezioni(self):
        """Clear all sections for new verification"""
        debug_print("[DEBUG] pulisci_sezioni called")
        self.label_info_file.set_markup(f'<span size="small" color="#999999">🔒 {_("No file selected")}</span>')
        self.status_badge.set_visible(False)
        self.pulisci_listbox()
        self.btn_apri_estratto.set_sensitive(False)

    def pulisci_listbox(self):
        """Clear listbox content"""
        while True:
            row = self.firme_listbox.get_row_at_index(0)
            if row is None:
                break
            self.firme_listbox.remove(row)

    def verifica_firma(self, file_p7m):
        """Main signature verification workflow"""
        debug_print(f"[DEBUG] verifica_firma: {file_p7m}")
        self.pulisci_sezioni()
        self.file_estratto = None
        self.file_verificato = False
        
        # Cache directory
        cache_dir = os.path.join(GLib.get_user_cache_dir(), 'p7mviewer')
        os.makedirs(cache_dir, exist_ok=True)

        # File info
        base_path = Path(file_p7m)
        nome_file = base_path.name
        percorso_dir = base_path.parent
        file_markup = f'<span size="small" color="#666666">📂 {percorso_dir}</span>\n<span size="medium" weight="bold">{nome_file}</span>'
        self.label_info_file.set_markup(file_markup)

        try:
            with open(file_p7m, 'rb') as f:
                data = f.read()
            firme_info = analizza_busta(data)
            
            if not firme_info:
                self.mostra_stato_file("error", _("No digital signature found in file"))
                return
            
            # Extract signatures recursively
            max_livello = max(info.get('livello_busta', 1) for info in firme_info)
            file_corrente = file_p7m
            
            for livello in range(1, max_livello + 1):
                base_name = base_path.name.rstrip('.p7m').rstrip('.P7M')
                file_output = os.path.join(cache_dir, f"{base_name}_level{livello}")
                
                cmd = [
                    "openssl", "smime", "-verify",
                    "-in", file_corrente, "-inform", "DER",
                    "-noverify", "-out", file_output
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    self.mostra_stato_file("error", _("Verification error"))
                    self.mostra_errore_verifica(result.stderr)
                    return
                
                file_corrente = file_output
            
            # Success
            self.file_estratto = file_corrente
            self.btn_apri_estratto.set_sensitive(True)
            self.mostra_stato_file("success", _("Verification completed successfully"))
            self.mostra_info_firma(file_p7m)
            
        except Exception as e:
            self.mostra_stato_file("error", str(e)[:50])
            self.mostra_errore_verifica(str(e))

    def crea_expander_firma(self, info, idx):
        """Create signature expander"""
        identita = info.get(_('Identity'), _('Unknown'))
        stato = info.get(_('Certificate status'), '')
        
        expander = Gtk.Expander()
        expander.set_margin_top(4)
        expander.set_margin_bottom(4)
        expander.set_margin_start(8)
        expander.set_margin_end(8)
        
        header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_label = Gtk.Label(label=f'<b>🖊️ {identita}</b>')
        title_label.set_use_markup(True)
        title_label.set_halign(Gtk.Align.START)
        header_box.append(title_label)
        
        subtitle = Gtk.Label(label=f'<span size="small" color="#666">{stato}</span>')
        subtitle.set_use_markup(True)
        subtitle.set_halign(Gtk.Align.START)
        header_box.append(subtitle)
        
        expander.set_label_widget(header_box)
        
        # Details
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        details_box.set_margin_top(8)
        details_box.set_margin_start(12)
        
        campi_dettagli = [
            (_('Tax Code'), '🆔'),
            (_('Organization'), '🏢'),
            (_('Signature date and time'), '📅'),
            (_('Signature valid at signing time'), '✔️'),
            (_('Valid from'), '📆'),
            (_('Valid until'), '📆'),
            (_('Certificate issued by'), '🏛️'),
        ]
        
        for campo_tradotto, icona in campi_dettagli:
            if campo_tradotto in info:
                valore = info[campo_tradotto]
                detail_label = Gtk.Label(label=f'<span size="small">{icona} <b>{campo_tradotto}:</b> {valore}</span>')
                detail_label.set_use_markup(True)
                detail_label.set_halign(Gtk.Align.START)
                detail_label.set_wrap(True)
                detail_label.set_xalign(0)
                details_box.append(detail_label)
        
        expander.set_child(details_box)
        return expander

    def mostra_info_firma(self, file_p7m):
        """Display signature information"""
        self.pulisci_listbox()
        try:
            with open(file_p7m, 'rb') as f:
                data = f.read()
            firme_info = analizza_busta(data)
            
            if not firme_info:
                no_firme_label = Gtk.Label(label=f'<span size="small" color="#999">⚠️ {_("No digital signature found in file")}</span>')
                no_firme_label.set_use_markup(True)
                no_firme_label.set_margin_top(20)
                no_firme_label.set_margin_bottom(20)
                self.firme_listbox.append(no_firme_label)
                return
            
            for info in firme_info:
                expander = self.crea_expander_firma(info, 0)
                self.firme_listbox.append(expander)
            
            # Footer
            n_signatures = len(firme_info)
            sig_word = _("signature") if n_signatures == 1 else _("signatures")
            footer_label = Gtk.Label(label=f'<span size="small" color="#666">✓ {_("Total")}: {n_signatures} {sig_word} {_("verified")}</span>')
            footer_label.set_use_markup(True)
            footer_label.set_margin_top(12)
            footer_label.set_margin_bottom(8)
            self.firme_listbox.append(footer_label)
            
        except Exception as e:
            self.mostra_errore_verifica(str(e))

    def mostra_errore_verifica(self, errore):
        """Show verification error in listbox"""
        self.pulisci_listbox()
        
        error_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        error_box.set_margin_top(30)
        error_box.set_margin_bottom(30)
        error_box.set_margin_start(20)
        error_box.set_margin_end(20)
        
        title_label = Gtk.Label(label=f'<span size="large">❌</span>\n<span size="large" weight="bold">{_("Unable to verify file")}</span>')
        title_label.set_use_markup(True)
        title_label.set_justify(Gtk.Justification.CENTER)
        error_box.append(title_label)
        
        msg_label = Gtk.Label(label=f'<span color="#666">{_("The selected file is not a valid P7M file or cannot be processed.")}</span>')
        msg_label.set_use_markup(True)
        msg_label.set_justify(Gtk.Justification.CENTER)
        msg_label.set_wrap(True)
        error_box.append(msg_label)
        
        if errore:
            errore_pulito = errore.split('\n')[0] if '\n' in errore else errore
            if 'Error reading S/MIME message' in errore:
                errore_pulito = _("File is not in valid P7M/CAdES format")
            
            details_expander = Gtk.Expander(label=_("Technical details"))
            details_expander.set_margin_top(12)
            
            details_label = Gtk.Label(label=f'<span size="small" font_family="monospace" color="#999">{errore_pulito}</span>')
            details_label.set_use_markup(True)
            details_label.set_wrap(True)
            details_label.set_xalign(0)
            details_label.set_margin_start(12)
            details_label.set_margin_top(8)
            details_expander.set_child(details_label)
            error_box.append(details_expander)
        
        self.firme_listbox.append(error_box)

    def on_apri_estratto_clicked(self, widget):
        """Open extracted file with portal"""
        debug_print(f"[DEBUG] Open extracted file: {self.file_estratto}")
        if not self.file_estratto or not os.path.exists(self.file_estratto):
            self.mostra_stato_file("error", _("Extracted file no longer exists"))
            return
        
        try:
            gfile = Gio.File.new_for_path(self.file_estratto)
            launcher = Gtk.FileLauncher.new(gfile)
            
            def on_launch_finish(launcher, result):
                try:
                    launcher.launch_finish(result)
                    debug_print("[DEBUG] File opened successfully")
                except Exception as e:
                    debug_print(f"[DEBUG] File launch error: {e}")
                    self.mostra_stato_file("error", _("File opening error"))
            
            launcher.launch(self, None, on_launch_finish)
        except Exception as e:
            self.mostra_stato_file("error", str(e)[:100])

def main():
    debug_print("[DEBUG] main() called")
    app = FirmeApp()
    app.run(sys.argv)

if __name__ == "__main__":
    main()
