$ErrorActionPreference = 'Stop'
$packageRoot = Split-Path $PSScriptRoot
python -m pip install -r (Join-Path $PSScriptRoot 'requirements-build.txt')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m PyInstaller --noconfirm --clean --onefile --windowed --name 'SSYTDLP' --icon (Join-Path $PSScriptRoot 'app.ico') --distpath $packageRoot --workpath (Join-Path $packageRoot 'build') --specpath (Join-Path $packageRoot 'build') (Join-Path $PSScriptRoot 'app.py')
exit $LASTEXITCODE
