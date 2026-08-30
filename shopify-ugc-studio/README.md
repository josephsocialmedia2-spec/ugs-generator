# Shopify UGC Studio v2.2 · F1 Avatar Engine

Applicazione Windows per trasformare prodotti Shopify in concept UGC e video MP4 verticali. La generazione video/avatar è **locale**: non usa provider video esterni e non richiede crediti o chiavi API per avatar.

## Flusso

`Shopify → Ollama locale → concept/script UGC → UGC Motion oppure F1 Avatar Engine → MP4 9:16`

## F1 Avatar Engine

- profilo presenter da foto autorizzata;
- campione voce opzionale salvato sul PC;
- `F1Avatar Lite` sempre disponibile come renderer locale di compatibilità;
- backend `F1AvatarNeural.exe` rilevato automaticamente se presente nella cartella dati del modello oppure indicato da `F1_AVATAR_NEURAL_EXE`;
- nessun upload del volto o della voce a servizi video remoti.

Il backend neurale è un **model pack locale separato**: l'applicazione definisce il contratto di esecuzione e usa automaticamente il model pack quando installato. In sua assenza continua a funzionare con F1Avatar Lite. Questa distinzione evita di dichiarare qualità neurale non presente nel pacchetto base.

## Dati locali

Impostazioni, avatar e output sono salvati sotto `%LOCALAPPDATA%\ShopifyUGCStudio`. I token Shopify non vengono restituiti dalle API dell'interfaccia.

## Build Windows verificata

La CI esegue test unitari, smoke test Flask, self-test sorgente, build PyInstaller, self-test dell'EXE, compilazione Inno Setup, installazione silenziosa, self-test della copia installata e health-check HTTP che verifica F1 Avatar Engine in modalità locale.
