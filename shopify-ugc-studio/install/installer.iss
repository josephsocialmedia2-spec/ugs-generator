#define MyAppName "Shopify UGC Studio - F1 Avatar"
#define MyAppVersion "2.2.0"
#define MyAppPublisher "Real Media Pro"
#define MyAppExeName "ShopifyUGCStudio.exe"

[Setup]
AppId={{74A5AB98-D789-4FF6-9D95-E05E299A5E33}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\ShopifyUGCStudio
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=ShopifyUGCStudio-F1Avatar-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Avvia Shopify UGC Studio - F1 Avatar"; Flags: nowait postinstall skipifsilent
