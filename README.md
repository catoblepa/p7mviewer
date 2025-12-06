# P7M Viewer

**P7M Viewer** è una semplice applicazione GTK4 per GNOME che permette di verificare file firmati digitalmente in formato `.p7m` (CAdES) e visualizzare i dettagli delle firme digitali contenute.

## Funzionalità

- **Apertura e verifica di file .p7m**  
  Seleziona un file firmato digitalmente e verifica la validità della firma tramite OpenSSL.
- **Supporto formati multipli**  
  Rileva e gestisce automaticamente file P7M in formato Base64, DER e PEM.
- **Visualizzazione dettagli firmatari completi**  
  Mostra per ogni firmatario:
  - Nome completo
  - Codice Fiscale
  - Organizzazione
  - Periodo di validità del certificato
  - Stato certificato (valido/scaduto)
  - Data e ora della firma
  - Verifica se la firma era valida al momento della sottoscrizione
- **Supporto firme multiple e annidate**  
  Gestisce file con doppia firma (`.p7m`) e buste annidate.
- **Estrazione del file originale**  
  Permette di aprire il file estratto dal pacchetto firmato.
- **Interfaccia moderna**  
  Basata su GTK4, con headerbar e layout responsive.

## Come si usa

1. **Avvia l'applicazione.**
2. **Clicca su "📁 Seleziona file"** e seleziona un file `.p7m`.
3. **Visualizza i dettagli delle firme** nella finestra principale.
4. **Apri il file estratto** cliccando su "📄 Visualizza contenuto" (se la verifica ha successo).

## Requisiti

- Python 3.8+
- GTK 4 e PyGObject
- OpenSSL installato nel sistema
- Libreria Python `asn1crypto` (per analisi certificati digitali)

## Installazione

### Installazione tramite Flatpak

Per installare l'applicazione in ambiente isolato tramite Flatpak:

```bash
flatpak-builder --user --install --force-clean build-dir com.github.catoblepa.p7mviewer.yaml
```

### Installazione manuale

Se preferisci eseguire l'applicazione direttamente:

```bash
# Installa dipendenze
pip install asn1crypto

# Esegui l'applicazione
cd src
python3 p7mviewer.py [file.p7m]
```

## Localizzazione

L'applicazione supporta l'internazionalizzazione (i18n) tramite gettext. Attualmente sono disponibili le traduzioni per:
- **Inglese** (lingua predefinita)
- **Italiano**

### Aggiungere una nuova traduzione

Per aggiungere il supporto per una nuova lingua:

1. **Aggiorna il template POT** con le stringhe più recenti:
   ```bash
   cd src
   xgettext --language=Python --keyword=_ --output=p7mviewer.pot p7mviewer.py
   ```

2. **Crea una nuova traduzione** (esempio per il francese):
   ```bash
   mkdir -p locale/fr/LC_MESSAGES
   msginit --input=p7mviewer.pot --locale=fr --output=locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.po
   ```

3. **Traduci le stringhe** nel file `.po` appena creato:
   ```bash
   # Modifica il file con un editor di testo o usa strumenti come Poedit
   nano locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.po
   ```

4. **Compila la traduzione** in formato binario:
   ```bash
   msgfmt locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.po \
          -o locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.mo
   ```

5. **Aggiorna il manifest Flatpak** per includere la nuova traduzione in `com.github.catoblepa.p7mviewer.yaml`:
   ```yaml
   build-commands:
     # ... altri comandi ...
     - install -Dm644 locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.mo /app/share/locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.mo
   sources:
     # ... altri sources ...
     - type: file
       path: src/locale/fr/LC_MESSAGES/com.github.catoblepa.p7mviewer.mo
   ```

6. **Testa la traduzione** impostando la variabile d'ambiente:
   ```bash
   LANGUAGE=fr python3 p7mviewer.py
   ```

## Licenza

[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html)
