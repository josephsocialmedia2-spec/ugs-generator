# Shopify UGC Studio v2.1

Applicazione Windows locale per trasformare prodotti Shopify in concept e video UGC.

## Flusso

1. Importa un prodotto da URL oppure collega il catalogo Shopify.
2. Ollama genera angoli creativi, hook, script, scene, caption e CTA.
3. Scegli **UGC Motion locale** oppure **Creator AI**.
4. Il programma salva job e video nella cartella dati locale dell'utente.

## Versione cliente Windows

La distribuzione finale è `ShopifyUGCStudio-Setup.exe`. Non richiede Python installato sul PC cliente: Python e dipendenze sono incorporati nell'EXE generato con PyInstaller.

Dopo l'installazione:
- viene creato un collegamento sul Desktop e nel menu Start;
- il programma viene avviato;
- viene registrato l'avvio automatico all'accesso Windows;
- l'interfaccia locale è `http://127.0.0.1:7865`.

Dati persistenti su Windows:
`%LOCALAPPDATA%\ShopifyUGCStudio\`

Contiene `settings.json` e `output\<job_id>\`. Le chiavi non vengono incluse nel repository o nell'installer.

## QA obbligatorio

La pipeline Windows accetta l'installer solo se passano:
- pytest;
- self-test sorgente;
- build EXE standalone;
- self-test EXE;
- compilazione installer;
- installazione silenziosa su Windows;
- self-test dell'EXE installato;
- avvio reale del server e risposta HTTP `/api/health`.

## Shopify

La versione Admin GraphQL usata è `2026-07`. Servono dominio `*.myshopify.com` e token con accesso ai prodotti.

## Ollama

Default: `http://127.0.0.1:11434`, modello `qwen2.5-coder:7b`. Se Ollama non risponde, vengono generati concept di fallback e il programma non resta bloccato.

## Creator AI HeyGen

Opzionale. Richiede credenziali valide e disponibilità del servizio. I test automatici verificano il codice e il comportamento senza consumare crediti; un render remoto reale richiede un account configurato.

## Sviluppo

`INSTALLA_E_AVVIA.bat` e `AVVIA.bat` restano disponibili per sviluppo da sorgente. Il cliente finale deve usare l'installer `.exe` prodotto dalla CI.
