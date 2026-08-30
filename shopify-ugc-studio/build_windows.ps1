$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pip install -r requirements-build.txt
python -m pytest -q
python app/main.py --self-test
Remove-Item -Recurse -Force build,dist -ErrorAction SilentlyContinue
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name ShopifyUGCStudio `
  --paths "app" --add-data "templates;templates" --add-data "static;static" app/main.py
$built = Resolve-Path '.\dist\ShopifyUGCStudio.exe'
$p = Start-Process -FilePath $built -ArgumentList '--self-test' -Wait -PassThru
if ($p.ExitCode -ne 0) { throw "Built EXE self-test failed with $($p.ExitCode)" }
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" install\installer.iss
