# Shopify UGC Studio v2.2

Applicazione Windows locale per trasformare prodotti Shopify in concept UGC, video motion e presenter/avatar AI.

## Principio fondamentale

**Nessuna integrazione HeyGen. Nessuna API video esterna.**

Il presenter è gestito da **F1 Avatar Engine**, il motore locale del programma. Foto avatar, campioni voce, job e video restano nella cartella dati locale del PC.

## Pipeline

1. Import prodotto Shopify da URL o catalogo Admin GraphQL.
2. Ollama genera angoli, hook, script, scene, caption e CTA.
3. Produzione:
   - **UGC Motion**: immagini prodotto + motion + voice-over locale;
   - **F1 Avatar**: foto avatar + script + motore avatar locale.
4. Esportazione MP4 verticale 9:16.

## F1 Avatar Engine

Versione iniziale: `0.1.0`.

Il motore ha due backend:
- **Lite locale**: sempre disponibile, non usa servizi esterni ed esegue il render sul PC;
- **Neural locale**: interfaccia predisposta per il model pack `F1AvatarNeural`, eseguito come runtime locale. Quando installato viene preferito automaticamente.

Il model pack neurale è progettato per includere lip-sync e voice cloning senza inviare contenuti a provider cloud. Il codice applicativo non contiene chiavi HeyGen o route HeyGen.

## Profilo avatar

Dall'interfaccia si possono salvare:
- foto frontale dell'avatar;
- campione voce opzionale.

Dati Windows:
`%LOCALAPPDATA%\ShopifyUGCStudio\avatar\`

Output:
`%LOCALAPPDATA%\ShopifyUGCStudio\output\<job_id>\`

## Distribuzione Windows

La build finale è `ShopifyUGCStudio-Setup.exe`. Il cliente non deve installare Python: l'app viene compilata in EXE standalone con PyInstaller.

## QA

La pipeline deve verificare:
- test unitari e smoke test Flask;
- assenza di dipendenze video esterne;
- self-test del motore UGC locale;
- build EXE;
- self-test EXE;
- compilazione installer;
- installazione silenziosa su Windows;
- health-check dell'app installata.

## Nota sul livello “HeyGen-like”

Il prodotto e l'orchestrazione sono nostri. Un motore neurale con qualità equivalente ai migliori servizi commerciali richiede pesi locali, GPU e un ciclo di training/ottimizzazione dedicato. La v2.2 elimina la dipendenza esterna e crea l'architettura su cui installare e poi addestrare il model pack proprietario.
