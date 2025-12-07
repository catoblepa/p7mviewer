# P7M Viewer

**P7M Viewer** is a simple GTK4 application for GNOME that allows you to verify digitally signed files in `.p7m` (CAdES) format and view the details of the contained digital signatures.

## Features

- **Open and verify .p7m files**  
	Select a digitally signed file and verify the signature validity using OpenSSL.
- **Multiple format support**  
	Automatically detects and handles P7M files in Base64, DER, and PEM formats.
- **Complete signer details view**  
	Shows for each signer:
	- Full name
	- Tax code
	- Organization
	- Certificate validity period
	- Certificate status (valid/expired)
	- Signature date and time
	- Checks if the signature was valid at signing time
- **Support for multiple and nested signatures**  
	Handles files with double signature (`.p7m`) and nested envelopes.
- **Extract original file**  
	Allows opening the extracted file from the signed package.
- **Modern interface**  
	Based on GTK4, with headerbar and responsive layout.

## Usage

1. **Start the application.**
2. **Click "📁 Select file"** and choose a `.p7m` file.
3. **View signature details** in the main window.
4. **Open the extracted file** by clicking "📄 View content" (if verification succeeds).

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

## Drag & Drop and Flatpak Permissions

**Note:** If you use the application via Flatpak, dragging and dropping files from your home directory or other user folders may not work unless the app has the necessary permissions to access user files.

To enable drag and drop from your home, you can:

- Start the app with additional permission:

	```bash
	flatpak override --user --filesystem=home io.github.catoblepa.p7mviewer
	```

- Or, for a single folder (e.g. Documents):

	```bash
	flatpak override --user --filesystem=xdg-documents io.github.catoblepa.p7mviewer
	```

Alternatively, you can always use the integrated file selector, which works even without extra permissions thanks to Flatpak portals.

## Debug

To enable debug mode and get detailed output in the terminal, set the environment variable `P7MVIEWER_DEBUG`:

```bash
# Enable debug mode
export P7MVIEWER_DEBUG=true
python3 src/p7mviewer.py
```

## Localization

The application supports internationalization (i18n) via gettext. Currently available translations:
- **English** (default language)
- **Italian**

### Add a new translation

To add support for a new language:

1. **Update the POT template** with the latest strings:
	 ```bash
	 cd src
	 xgettext --language=Python --keyword=_ --output=p7mviewer.pot p7mviewer.py signature_parser.py
	 ```

2. **Create a new translation** (example for French):
	 ```bash
	 mkdir -p locale/fr/LC_MESSAGES
	 msginit --input=p7mviewer.pot --locale=fr --output=locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.po
	 ```

3. **Translate the strings** in the newly created `.po` file:
	 ```bash
	 # Edit the file with a text editor or use tools like Poedit
	 nano locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.po
	 ```

4. **Compile the translation** to binary format:
	 ```bash
	 msgfmt locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.po \
					-o locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.mo
	 ```

5. **Update the Flatpak manifest** to include the new translation in `com.github.catoblepa.p7mviewer.yaml`:
	 ```yaml
	 build-commands:
		 # ... other commands ...
		 - install -Dm644 locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.mo /app/share/locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.mo
	 sources:
		 # ... other sources ...
		 - type: file
			 path: src/locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.mo
	 ```

6. **Test the translation** by setting the environment variable:
	 ```bash
	 LANGUAGE=fr python3 p7mviewer.py
	 ```

## License

[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html)
