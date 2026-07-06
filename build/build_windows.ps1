# build_windows.ps1 — Construit PhotoOrganizer.exe (Windows, autonome).
# A executer depuis la racine du projet sur une machine Windows avec Python 3.9+.
# Le fichier .exe genere est compatible Windows 10/11 (x64).
#
# Usage (PowerShell, depuis la racine du projet) :
#   python -m venv venv
#   .\venv\Scripts\Activate.ps1
#   pip install -r requirements.txt
#   pip install pyinstaller>=6.0
#   .\build\build_windows.ps1

$ErrorActionPreference = "Stop"

$AppName  = "PhotoOrganizer"
$DistDir  = "dist"
$WorkDir  = "build\pyinstaller_work"
$SpecDir  = "build"
$IconPath = "build\assets\icon.ico"

Write-Host "=== Build PyInstaller (--onefile) ===" -ForegroundColor Cyan

# --add-data attend un chemin absolu pour la source : PyInstaller resout un chemin
# relatif par rapport a --specpath (ici "build\"), pas par rapport au dossier courant.
$ThemeJsonPath = Join-Path (Get-Location).Path "core\theme.json"

$pyinstallerArgs = @(
    "--onefile",
    "--windowed",
    "--name", $AppName,
    "--distpath", $DistDir,
    "--workpath", $WorkDir,
    "--specpath", $SpecDir,
    "--add-data", "$ThemeJsonPath;core"
)

# Icone optionnelle : placer un .ico 256x256 dans build\assets\icon.ico
if (Test-Path $IconPath) {
    $pyinstallerArgs += "--icon", $IconPath
    Write-Host "Icone incluse : $IconPath"
} else {
    Write-Warning "build\assets\icon.ico absent -- icone par defaut PyInstaller utilisee."
}

pyinstaller @pyinstallerArgs main.py

$ExePath = "$DistDir\$AppName.exe"
if (Test-Path $ExePath) {
    $size = [math]::Round((Get-Item $ExePath).Length / 1MB, 1)
    Write-Host ""
    Write-Host "Executable cree : $ExePath ($size Mo)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Distribution :"
    Write-Host "  Copier $ExePath sur la machine cible (aucune installation requise)."
} else {
    Write-Error "La build a echoue : $ExePath introuvable."
}
