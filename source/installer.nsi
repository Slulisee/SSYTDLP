; Per-user setup; generated payload/uninstall lists contain only app-owned files.
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
Name "SSYTDLP"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\SSYTDLP"
InstallDirRegKey HKCU "Software\Slulisee\SSYTDLP" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
BrandingText "made by Slulisee"
Icon "${ROOT}\source\app.ico"
UninstallIcon "${ROOT}\source\app.ico"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "SSYTDLP"
VIAddVersionKey "FileDescription" "SSYTDLP setup and upgrade"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "Slulisee - MIT License"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\SSYTDLP.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Open SSYTDLP"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${ROOT}\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "French"
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY "Software\Slulisee\SSYTDLP"
!define MUI_LANGDLL_REGISTRY_VALUENAME "InstallerLanguage"

!macro WAIT_FOR_APP PREFIX
  StrCpy $0 0
  ${Do}
    System::Call 'kernel32::OpenMutexW(i 0x100000, i 0, w "Local\Slulisee.SSYTDLP.Application") p.r1'
    ${If} $1 = 0
      ${ExitDo}
    ${EndIf}
    System::Call 'kernel32::CloseHandle(p r1)'
    IntOp $0 $0 + 1
    ${If} $0 >= 40
      IfSilent ${PREFIX}busy
      MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Close all SSYTDLP windows before continuing. Your queue is saved when the app closes." IDRETRY ${PREFIX}retry
      ${PREFIX}busy:
      SetErrorLevel 2
      Quit
      ${PREFIX}retry:
      StrCpy $0 0
    ${EndIf}
    Sleep 250
  ${Loop}
!macroend

Function .onInit
  SetShellVarContext current
  !insertmacro MUI_LANGDLL_DISPLAY
  !insertmacro WAIT_FOR_APP init
FunctionEnd

Section "SSYTDLP" Main
  !insertmacro WAIT_FOR_APP install
  !ifdef UPDATE_ONLY
    IfFileExists "$INSTDIR\SSYTDLP.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\yt-dlp.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\ffmpeg.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\ffprobe.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\deno.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\engines.json" update_ready incomplete
    incomplete:
      MessageBox MB_OK|MB_ICONSTOP "Choose an existing SSYTDLP app folder, or download the full Setup package for a first installation." /SD IDOK
      SetErrorLevel 3
      Quit
    update_ready:
  !endif
  SetOverwrite on
  !include "${PAYLOAD}"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Slulisee\SSYTDLP" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "DisplayName" "SSYTDLP"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "Publisher" "Slulisee"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "DisplayIcon" "$INSTDIR\SSYTDLP.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "URLInfoAbout" "https://github.com/Slulisee/SSYTDLP"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP" "NoRepair" 1
  CreateDirectory "$SMPROGRAMS\SSYTDLP"
  CreateShortcut "$SMPROGRAMS\SSYTDLP\SSYTDLP.lnk" "$INSTDIR\SSYTDLP.exe"
SectionEnd

Function un.onInit
  SetShellVarContext current
  !insertmacro WAIT_FOR_APP uninstall
FunctionEnd

Section "Uninstall"
  !include "${UNINSTALL_FILES}"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  ; An older portable/secondary copy must not unregister a different installation.
  ReadRegStr $0 HKCU "Software\Slulisee\SSYTDLP" "InstallDir"
  ${If} $0 == $INSTDIR
    DeleteRegKey HKCU "Software\Slulisee\SSYTDLP"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP"
    Delete "$SMPROGRAMS\SSYTDLP\SSYTDLP.lnk"
    RMDir "$SMPROGRAMS\SSYTDLP"
  ${EndIf}
  ; Never delete the separate settings/queue folder or any downloaded media.
SectionEnd
