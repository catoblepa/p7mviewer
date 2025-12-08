# P7M Viewer

**P7M Viewer** is a simple GTK4 application for GNOME that allows you to verify digitally signed files in `.p7m` (CAdES) format and view the details of the contained digital signatures.

## Main Features

- **.p7m file verification**
Opens and checks digital signature validity using OpenSSL.
- **Multi-format support**
Automatic handling of P7M files in Base64, DER, and PEM formats.
- **Complete signer details**
Name, Tax Code, Organization, certificate validity, signature date, and verification at signing time.
- **Multiple and nested signatures**
Full support for complex signed envelopes.
- **Extract original document**
Retrieve and open the file contained in the signed package.
- **Modern GTK4 interface**
Intuitive design with native drag \& drop.

## Requirements

- Python 3.8+
- GTK 4 and PyGObject
- OpenSSL installed on the system
- Python library `asn1crypto` (for digital certificate analysis)

## Installation

### Flatpak Installation

To install the application in a sandboxed environment using Flatpak:

```bash
flatpak-builder --user --install --force-clean build-dir io.github.catoblepa.p7mviewer.yaml
```

### Manual Installation

If you prefer to run the application directly:

```bash
# Install dependencies
pip install asn1crypto

# Run the application
cd src
python3 p7mviewer.py [file.p7m]
```

## Debug

To enable debug mode and get detailed output in the terminal, set the environment variable `P7MVIEWER_DEBUG`:

```bash
# Enable debug mode
export P7MVIEWER_DEBUG=true
python3 src/p7mviewer.py
```

## License

[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html)
