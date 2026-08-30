$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pip install -r requirements-build.txt
python -m pytest -q
python app/main.py --self-test
Remove-Item -Recurse -Force build,dist -ErrorAction SilentlyContinue
python -m PyInstaller --noconfirm --clean --onefile --noconsole --name ShopifyUGCStudio `
  --add-data "templates;templates" --add-data "static;static" app/main.py
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" install\installer.iss
