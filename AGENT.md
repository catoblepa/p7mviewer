# P7M Viewer - Agent Documentation

## Project Overview

**P7M Viewer** is a GTK4 application for GNOME that verifies and displays digitally signed files in `.p7m` (CAdES) and `.pdf` (PAdES) formats. Built with Python 3.8+, GTK4, PyGObject, OpenSSL, asn1crypto, and pypdf.

- **App ID:** `io.github.catoblepa.p7mviewer`
- **License:** GPL-3.0-or-later
- **Author:** Davide Truffa <davide@catoblepa.org>

## Architecture

### Main Components

```
src/
├── p7mviewer.py          # Main GTK4 application (GUI)
├── signature_parser.py   # Backend: ASN.1/CMS parsing with asn1crypto
├── locale/               # Translations (it, fr, es, de)
├── *.desktop             # Desktop entry
├── *.metainfo.xml        # AppStream metadata
└── *.svg                 # Application icon
```

### Data Flow (P7M / CAdES)

1. User drops/selects `.p7m` file
2. `p7mviewer.py` calls `signature_parser.analizza_busta()` to parse certificates/signers
3. `p7mviewer.py` uses `openssl smime -verify` to verify signatures and extract original document
4. Results displayed in expandable UI rows with signer details

### Data Flow (PAdES / PDF)

1. User drops/selects `.pdf` file
2. `p7mviewer.py` detects PDF magic bytes (`%PDF`)
3. `signature_parser.estrai_firme_da_pdf()` extracts PKCS#7 blobs from signature fields using pypdf
4. Each blob is parsed with `analizza_busta()` for signer info
5. `openssl smime -verify` verifies against reconstructed content (ByteRange)
6. The PDF itself is the extracted document (no extraction needed)

## Key Files

| File | Purpose |
|------|---------|
| `src/p7mviewer.py` | Main application window, UI, drag-drop, file operations |
| `src/signature_parser.py` | CMS/PKCS#7 parsing, certificate extraction, signer info |
| `io.github.catoblepa.p7mviewer.yaml` | Flatpak manifest |
| `Makefile` | Installation rules |
| `requirements.txt` | Python dependencies |
| `.github/workflows/flatpak.yml` | CI/CD for Flatpak builds |

## Development Setup

### Prerequisites
```bash
# System dependencies
sudo apt install python3-gi python3-pip openssl libgirepository1.0-dev

# Python dependencies
pip install -r requirements.txt
# Or: pip install pygobject asn1crypto==1.5.1 pypdf
```

### Run Locally
```bash
cd src
python3 p7mviewer.py [file.p7m]

# Debug mode
export P7MVIEWER_DEBUG=true
python3 p7mviewer.py
```

### Build Flatpak
```bash
flatpak-builder --user --install --force-clean build-dir io.github.catoblepa.p7mviewer.yaml
```

## Common Tasks

### Add New Language
1. Create `src/locale/<lang>/LC_MESSAGES/io.github.catoblepa.p7mviewer.po`
2. Run `msgfmt` to compile (handled by Makefile `install-locales`)
3. Add `<lang>` to Flatpak `finish-args` if needed

### Modify UI
- Main window: `FirmeWindow` class in `p7mviewer.py`
- Signature expander: `crea_expander_firma()` method
- Header bar: `_setup_headerbar()` method

### Modify Signature Parsing
- Core logic: `analizza_busta()` in `signature_parser.py`
- Certificate fields: `estrai_nome_cognome()`, `estrai_codice_fiscale()`, `estrai_organization()`
- Signer info: `mostra_info_firma()`

### Update Version
1. Update version in `metainfo.xml` `<release>` section
2. Tag release: `git tag v<version>`
3. GitHub Actions builds Flatpak automatically

## Testing

### Manual Testing
```bash
# Test with sample P7M files
python3 src/signature_parser.py test.p7m  # CLI parser test
python3 src/p7mviewer.py test.p7m         # GUI test
```

### Debug Output
```bash
export P7MVIEWER_DEBUG=true
python3 src/p7mviewer.py
```

## Known Limitations

- Requires OpenSSL CLI for verification (not pure Python)
- Certificate chain validation uses `-noverify` (trusts embedded certs from the P7M envelope, no CRL/OCSP check)
- Cache directory cleaned on window close: `~/.cache/p7mviewer/`
- OpenSSL subprocess has a 30-second timeout; very large files may time out
- Base64-encoded P7M files are decoded to DER before OpenSSL verification
- PAdES verification uses reconstructed content from `/ByteRange`; some PDF implementations may use non-standard ByteRange layouts
- Requires `pypdf` library for PDF parsing; if missing, PAdES support is unavailable

## Project Structure Details

### p7mviewer.py - Key Classes
- `FirmeApp(Gtk.Application)` - App lifecycle, handles file open
- `FirmeWindow(Gtk.ApplicationWindow)` - Main window, all UI logic

### signature_parser.py - Key Functions
- `rileva_formato_p7m()` - Detects Base64/DER/PEM
- `analizza_busta()` - Recursive envelope parsing
- `mostra_info_firma()` - Extracts signer details from certificate
- `estrai_firme_da_pdf()` - Extracts PAdES signatures from PDF via pypdf
- `ricostruisci_contenuto_pdf()` - Reconstructs signed PDF content from ByteRange

## Internationalization

Uses gettext with domain `io.github.catoblepa.p7mviewer`. Translations in `src/locale/<lang>/LC_MESSAGES/`.

Supported: Italian (default), French, Spanish, German.

## CI/CD

GitHub Actions (`.github/workflows/flatpak.yml`):
- Triggers on push to main, PR, tags `v*`
- Builds Flatpak using `flatpak/flatpak-github-actions`
- Uploads artifact and attaches to GitHub Release on tag push
