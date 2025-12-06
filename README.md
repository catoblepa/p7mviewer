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
flatpak-builder --user --install --force-clean build-dir io.github.catoblepa.p7mviewer.yaml
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


## Drag & Drop e permessi Flatpak

**Nota:** Se usi l'applicazione tramite Flatpak, il drag and drop di file dalla tua home directory o da altre cartelle utente potrebbe non funzionare a meno che l'app non abbia i permessi necessari per accedere ai file dell'utente.

Per abilitare il drag and drop di file dalla home, puoi:

- Avviare l'app con il permesso aggiuntivo:

  ```bash
  flatpak override --user --filesystem=home io.github.catoblepa.p7mviewer
  ```

- Oppure, per una singola cartella (es. Documenti):

  ```bash
  flatpak override --user --filesystem=xdg-documents io.github.catoblepa.p7mviewer
  ```

In alternativa, puoi sempre usare il selettore file integrato, che funziona anche senza permessi aggiuntivi grazie ai portali Flatpak.

## Debug

Per abilitare la modalità debug ed ottenere output dettagliati nel terminale, imposta la variabile d'ambiente `P7MVIEWER_DEBUG`:

```bash
# Modalità debug abilitata
export P7MVIEWER_DEBUG=true
python3 src/p7mviewer.py
```

## Licenza

[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html)
