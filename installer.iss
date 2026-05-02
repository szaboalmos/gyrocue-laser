; ─────────────────────────────────────────────────────────────────
;  GYROCUE Laser – Inno Setup installer script
;  Output: Output\GYROCUELaser_Setup_v6.0.exe
;
;  Requirements:
;    1. Run build_all.bat first  (builds dist\GYROCUELaser.exe)
;    2. Inno Setup 6:  https://jrsoftware.org/isdl.php
; ─────────────────────────────────────────────────────────────────

#define MyAppName        "GYROCUE Laser"
#define MyAppVersion     "6.0"
#define MyAppPublisher   "Gyrocue Kft"
#define MyAppURL         "https://gyrocue.com"
#define MyAppExeName     "GYROCUELaser.exe"
#define MyAppId          "{{A8F1C4D2-3B5E-4A9F-B6C7-1D2E3F4A5B6C}"
#define MyAppCopyright   "Copyright © 2025 Gyrocue Kft"

; ── Setup metadata ────────────────────────────────────────────────
[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppCopyright={#MyAppCopyright}

; Installation directory
DefaultDirName={autopf}\GYROCUELaser
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
DisableDirPage=no
AllowNoIcons=yes

; Output
OutputDir=Output
OutputBaseFilename=GYROCUELaser_Setup_v{#MyAppVersion}
SetupIconFile=Gyrocue_Logok_EPS-05.ico

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Appearance
WizardStyle=modern
WizardSizePercent=120
ShowLanguageDialog=no

; Privileges – installs per-user by default, can elevate on request
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Uninstall
UninstallDisplayName={#MyAppName} {#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
CloseApplicationsFilter=*{#MyAppExeName}*
RestartApplications=no

; Version info embedded in the Setup .exe
VersionInfoVersion={#MyAppVersion}.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} {#MyAppVersion} – Setup
VersionInfoCopyright={#MyAppCopyright}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}.0.0
VersionInfoProductTextVersion={#MyAppVersion}

; 64-bit only
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Minimum Windows version: Windows 10
MinVersion=10.0

; ── Language ──────────────────────────────────────────────────────
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ── Optional tasks ────────────────────────────────────────────────
[Tasks]
Name: "desktopicon";   Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startupentry";  Description: "Start GYROCUE Laser with Windows"; GroupDescription: "Startup:"

; ── Files ─────────────────────────────────────────────────────────
[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; ── Shortcuts ─────────────────────────────────────────────────────
[Icons]
Name: "{autoprograms}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; Tasks: startupentry

; ── Run after install ─────────────────────────────────────────────
[Run]
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

; ── Uninstall cleanup ─────────────────────────────────────────────
[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\GYROCUELaser"

; ── Code ──────────────────────────────────────────────────────────
[Code]
procedure KillApp;
var ResultCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM ' + '{#MyAppExeName}', '', SW_HIDE,
       ewWaitUntilTerminated, ResultCode);
end;

function InitializeSetup(): Boolean;
begin
  KillApp;
  Result := True;
end;

function InitializeUninstall(): Boolean;
begin
  KillApp;
  Result := True;
end;
