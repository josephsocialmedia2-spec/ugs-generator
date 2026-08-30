# F1 Avatar Engine — architettura modello

Obiettivo: presenter AI locale con pipeline simile a un sistema avatar commerciale, senza API video esterne.

## Stadi

1. Identity input: foto/video autorizzato dell'avatar.
2. Speech: TTS locale; voice sample opzionale per voice conversion/cloning locale.
3. Audio features: estrazione di energia, fonemi e rappresentazione temporale.
4. Audio-to-expression: mappatura audio → bocca/espressioni/pose.
5. Face renderer: generazione dei frame del volto preservando identità e stabilità.
6. Motion composer: micro-movimenti testa/corpo e composizione 9:16.
7. Lip-sync QA: controllo sincronizzazione audio-video.
8. Video encode: H.264 + AAC MP4.

## Backend v0.1

`F1Avatar Lite` è il fallback eseguibile ovunque e serve a garantire il flusso end-to-end.

## Backend neurale

`F1AvatarNeural.exe` è il contratto runtime previsto. Il programma lo cerca in:
`%LOCALAPPDATA%\ShopifyUGCStudio\models\f1-avatar\F1AvatarNeural.exe`

Input CLI previsti:
`--avatar <file> --text <script> --output <mp4> --duration <sec> [--voice-sample <file>]`

L'app non deve conoscere il framework ML sottostante: il runtime neurale può evolvere senza cambiare il prodotto desktop.

## Direzione commerciale

Per un prodotto rivendibile, usare solo codice, pesi e dataset con licenze compatibili con uso commerciale. Evitare modelli o checkpoint non-commerciali.
