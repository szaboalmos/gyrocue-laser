; GYROCUE Laser C++ – Inno Setup installer

#define MyAppName        "GYROCUE Laser"
#define MyAppVersion     "6.0"
#define MyAppPublisher   "Gyrocue Kft"
#define MyAppURL         "https://gyrocue.com"
#define MyAppExeName     "GYROCUELaser.exe"
#define MyAppId          "{{B9G2D5E3-4C6F-5B0A-C7D8-2E3F4A5B6C7D}"
#define MyAppCopyright   "Copyright © 2025 Gyrocue Kft"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppCopyright={#MyAppCopyright}
DefaultDirName={autopf}\GYROCUELaser
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=GYROCUELaser_Setup_v{#MyAppVersion}
SetupIconFile=..\resources\GYROCUELaser.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
VersionInfoVersion={#MyAppVersion}.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} {#MyAppVersion} Setup
VersionInfoCopyright={#MyAppCopyright}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";  Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce
Name: "startupentry"; Description: "Start GYROCUE Laser with Windows"; GroupDescription: "Startup:"

[Files]
Source: "..\build\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\build\*.dll";           DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "..\build\platforms\*";     DestDir: "{app}\platforms"; Flags: ignoreversion recursesubdirs
Source: "..\build\styles\*";        DestDir: "{app}\styles"; Flags: ignoreversion recursesubdirs skipifsourcedoesntexist

[Icons]
Name: "{autoprograms}\{#MyAppName}";           Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}";            Filename: "{app}\{#MyAppExeName}"; Tasks: startupentry

[Run]
Filename: "{app}\{#MyAppExeName}"; \
  Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{userappdata}\GYROCUELaser"

[Code]
procedure KillApp;
var ResultCode: Integer;
begin
  Exec('taskkill.exe', '/F /IM {#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function InitializeSetup(): Boolean;
begin KillApp; Result := True; end;

function InitializeUninstall(): Boolean;
begin KillApp; Result := True; end;
