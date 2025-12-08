# P7M Viewer

**P7M Viewer** è una semplice applicazione GTK4 per GNOME che permette di verificare file firmati digitalmente in formato `.p7m` (CAdES) e visualizzare i dettagli delle firme digitali contenute.

## Funzionalità

- **Verifica file .p7m**
Apertura e controllo della validità delle firme digitali tramite OpenSSL.
- **Supporto multi-formato**
Gestione automatica di P7M in Base64, DER e PEM.
- **Dettagli firmatari completi**
Nome, Codice Fiscale, Organizzazione, validità certificato, data firma e verifica al momento della sottoscrizione.
- **Firme multiple e annidate**
Supporto completo per buste firmate complesse.
- **Estrazione documento originale**
Recupero e apertura del file contenuto nel pacchetto firmato.
- **Interfaccia GTK4 moderna**
Design intuitivo con drag \& drop nativo.

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

## Debug

Per abilitare la modalità debug ed ottenere output dettagliati nel terminale, imposta la variabile d'ambiente `P7MVIEWER_DEBUG`:

```bash
# Modalità debug abilitata
export P7MVIEWER_DEBUG=true
python3 src/p7mviewer.py
```

## Licenza

[GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.html)
