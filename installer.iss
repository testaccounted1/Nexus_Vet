; NEXUS — Inno Setup 6 installer script
; Per-user install (no administrator rights needed — important for
; veterans on locked-down or family computers).

#define AppName "NEXUS"
#define AppVersion "0.4.0"
#define AppExe "NEXUS.exe"

[Setup]
AppId={{6B6F1F0A-7A4B-4F4D-9D3B-NEXUSVETTOOL}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=NEXUS Project (free, nonprofit)
AppPublisherURL=https://www.va.gov
DefaultDirName={userpf}\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
OutputDir=installer_out
OutputBaseFilename=NEXUS-Setup-{#AppVersion}
SetupIconFile=assets\nexus.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; \
  GroupDescription: "Shortcuts:"

[Files]
Source: "dist\NEXUS\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; \
  Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName} now"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Claim data lives in %APPDATA%\NEXUS and is deliberately NOT deleted
; on uninstall — it is the veteran's evidence record.
Type: filesandordirs; Name: "{app}"
