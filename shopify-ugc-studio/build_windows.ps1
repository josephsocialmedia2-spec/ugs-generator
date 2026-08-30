$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
python -m pip install -r requirements-build.txt
python -m pytest -q
python app/main.py --self-test
Remove-Item -Recurse -Force build,dist -ErrorAction SilentlyContinue
python -m PyInstaller --noconfirm --clean --onedir --noconsole --name ShopifyUGCStudio `
  --paths "app" --add-data "templates;templates" --add-data "static;static" app/main.py
$built = Resolve-Path '.\dist\ShopifyUGCStudio\ShopifyUGCStudio.exe'
$p = Start-Process -FilePath $built -ArgumentList '--no-browser' -PassThru
try {
  $ok = $false
  foreach ($i in 1..45) {
    Start-Sleep -Seconds 1
    if ($p.HasExited) { throw "Built application exited early with $($p.ExitCode)" }
    try {
      $r = Invoke-RestMethod -Uri 'http://127.0.0.1:7865/api/health' -TimeoutSec 2
      if ($r.status -eq 'ok' -and $r.local_only -eq $true) { $ok = $true; break }
    } catch {}
  }
  if (-not $ok) { throw 'Built application health check failed' }
} finally {
  Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
}
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" install\installer.iss
