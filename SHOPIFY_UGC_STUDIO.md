# Shopify UGC Studio v2.1

Revisione automatica del pacchetto fornito dall'utente.

Correzioni principali:
- distribuzione Windows standalone senza Python preinstallato;
- dati e impostazioni persistenti in LocalAppData;
- smoke test Flask/API reale;
- self-test del motore video locale;
- installer Inno Setup;
- test dell'EXE prima e dopo installazione;
- health check HTTP dell'applicazione installata.

La sorgente revisionata è conservata in `shopify-ugc-studio-source.zip`. L'installer Windows viene pubblicato come artifact solo se tutti i controlli passano.
