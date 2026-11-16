# Construit l'application Windows portable (onedir) : dist\RAD-Gardes-V5-windows-x64.zip
# Prérequis : Windows et Python 3.12 (lanceur py).
$ErrorActionPreference = "Stop"
$Racine = Split-Path $PSScriptRoot -Parent
Set-Location $Racine

py -3.12 -m venv .build-venv
& .\.build-venv\Scripts\python.exe -m pip install --upgrade pip
& .\.build-venv\Scripts\python.exe -m pip install pyinstaller openpyxl==3.1.5

& .\.build-venv\Scripts\pyinstaller.exe packaging\rad_gardes_v5.spec `
    --noconfirm --clean --distpath dist --workpath .build-work

$Dossier = "dist\RAD Gardes V5"
Copy-Item examples\gardes-in-vide.xlsx $Dossier
Copy-Item examples\gardes-in-demo.xlsx $Dossier
Copy-Item packaging\LISEZ-MOI-windows.txt $Dossier

Compress-Archive -Path "$Dossier\*" -DestinationPath "dist\RAD-Gardes-V5-windows-x64.zip" -Force
Write-Host "Archive : $Racine\dist\RAD-Gardes-V5-windows-x64.zip"
