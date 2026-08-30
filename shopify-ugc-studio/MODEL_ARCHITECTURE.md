# F1 Avatar Engine · model contract

F1 Avatar Engine è un motore locale, non un wrapper di servizi video esterni.

## Pacchetto base

`F1Avatar Lite` fornisce una pipeline deterministica e offline: immagine presenter → TTS locale Windows → envelope audio → animazione facciale di compatibilità → H.264/AAC MP4.

## Model pack neurale

L'app ricerca `F1AvatarNeural.exe` nella cartella dati del modello. Il runner deve accettare:

`F1AvatarNeural.exe --avatar <image> --text <script> --output <mp4> --duration <seconds> [--voice-sample <audio>]`

Requisiti del runner:

- esecuzione interamente locale;
- nessuna API video remota;
- exit code 0 solo se l'MP4 è valido;
- output H.264/AAC riproducibile;
- uso esclusivo di modelli/pesi con licenza compatibile con la distribuzione prevista.

L'architettura permette di sostituire o migliorare il model pack senza cambiare l'interfaccia Shopify UGC Studio.
