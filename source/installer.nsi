; Per-user setup; generated payload/uninstall lists contain only app-owned files.
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
Name "SSMD - Slulisee's simple media downloader"
OutFile "${OUTPUT}"
InstallDir "$LOCALAPPDATA\Programs\SSMD"
; Keep this private location pointer stable; NSIS itself applies /D afterward.
InstallDirRegKey HKCU "Software\Slulisee\SSYTDLP" "InstallDir"
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetCompressorDictSize 32
BrandingText "made by Slulisee"
Icon "${ROOT}\source\app.ico"
UninstallIcon "${ROOT}\source\app.ico"
VIProductVersion "${VERSION}.0"
VIAddVersionKey "ProductName" "SSMD"
VIAddVersionKey "FileDescription" "Slulisee's simple media downloader setup and upgrade"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "LegalCopyright" "Slulisee - MIT License"
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\SSMD.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Open SSMD"
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
!define MUI_LANGDLL_REGISTRY_KEY "Software\Slulisee\SSMD"
!define MUI_LANGDLL_REGISTRY_VALUENAME "InstallerLanguage"

!macro WAIT_FOR_APP PREFIX
  StrCpy $0 0
  ${Do}
    System::Call 'kernel32::OpenMutexW(i 0x100000, i 0, w "Local\Slulisee.SSMD.Application") p.r1'
    System::Call 'kernel32::OpenMutexW(i 0x100000, i 0, w "Local\Slulisee.SSYTDLP.Application") p.r2'
    FindWindow $3 "" "SSYTDLP - Slulisee's Simple yt-dlp Downloader"
    FindWindow $4 "" "SSMD - Slulisee's simple media downloader"
    ${If} $1 = 0
    ${AndIf} $2 = 0
    ${AndIf} $3 = 0
    ${AndIf} $4 = 0
      ${ExitDo}
    ${EndIf}
    ${If} $1 != 0
      System::Call 'kernel32::CloseHandle(p r1)'
    ${EndIf}
    ${If} $2 != 0
      System::Call 'kernel32::CloseHandle(p r2)'
    ${EndIf}
    IntOp $0 $0 + 1
    ${If} $0 >= 40
      IfSilent ${PREFIX}busy
      MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "Close all SSMD / SSYTDLP windows before continuing. Your queue is saved when the app closes." IDRETRY ${PREFIX}retry
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

Section "SSMD" Main
  !insertmacro WAIT_FOR_APP install
  !ifdef UPDATE_ONLY
    IfFileExists "$INSTDIR\SSMD.exe" app_present 0
    IfFileExists "$INSTDIR\SSYTDLP.exe" app_present incomplete
    app_present:
    IfFileExists "$INSTDIR\tools\yt-dlp.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\ffmpeg.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\ffprobe.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\deno.exe" 0 incomplete
    IfFileExists "$INSTDIR\tools\engines.json" update_ready incomplete
    incomplete:
      MessageBox MB_OK|MB_ICONSTOP "Choose an existing SSMD / SSYTDLP app folder, or download the full Setup package for a first installation." /SD IDOK
      SetErrorLevel 3
      Quit
    update_ready:
  !endif
  SetOverwrite on
  !include "${PAYLOAD}"
  Delete "$INSTDIR\SSYTDLP.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Slulisee\SSMD" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "DisplayName" "SSMD - Slulisee's simple media downloader"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "Publisher" "Slulisee"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "DisplayIcon" "$INSTDIR\SSMD.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "UninstallString" '$\"$INSTDIR\Uninstall.exe$\"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "QuietUninstallString" '$\"$INSTDIR\Uninstall.exe$\" /S'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "URLInfoAbout" "https://github.com/Slulisee/SSYTDLP"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD" "NoRepair" 1
  ReadRegStr $0 HKCU "Software\Slulisee\SSYTDLP" "InstallDir"
  ${If} $0 == $INSTDIR
    DeleteRegKey HKCU "Software\Slulisee\SSYTDLP"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSYTDLP"
    Delete "$SMPROGRAMS\SSYTDLP\SSYTDLP.lnk"
    RMDir "$SMPROGRAMS\SSYTDLP"
  ${EndIf}
  WriteRegStr HKCU "Software\Slulisee\SSYTDLP" "InstallDir" "$INSTDIR"
  CreateDirectory "$SMPROGRAMS\SSMD"
  CreateShortcut "$SMPROGRAMS\SSMD\SSMD.lnk" "$INSTDIR\SSMD.exe"
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
  ReadRegStr $0 HKCU "Software\Slulisee\SSMD" "InstallDir"
  ${If} $0 == $INSTDIR
    DeleteRegKey HKCU "Software\Slulisee\SSMD"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\SSMD"
    Delete "$SMPROGRAMS\SSMD\SSMD.lnk"
    RMDir "$SMPROGRAMS\SSMD"
    ReadRegStr $0 HKCU "Software\Slulisee\SSYTDLP" "InstallDir"
    ${If} $0 == $INSTDIR
      DeleteRegKey HKCU "Software\Slulisee\SSYTDLP"
    ${EndIf}
  ${EndIf}
  ; Never delete the separate settings/queue folder or any downloaded media.
SectionEnd
