# Construit l'application Windows portable (onedir) et son archive :
# dist\RAD Gardes V7\ et dist\RAD-Gardes-V7-windows-x64.zip
# Prérequis : Windows et Python 3.12 (lanceur py).
$ErrorActionPreference = "Stop"
$Racine = Split-Path $PSScriptRoot -Parent
Set-Location $Racine

if (-not (Test-Path ".build-venv")) {
    py -3.12 -m venv .build-venv
}
& .\.build-venv\Scripts\python.exe -m pip install --upgrade pip
& .\.build-venv\Scripts\python.exe -m pip install -e ".[build]"

& .\.build-venv\Scripts\pyinstaller.exe packaging\rad_gardes_v7.spec `
    --noconfirm --clean --distpath dist --workpath .build-work

$Dossier = "dist\RAD Gardes V7"
Copy-Item README.md $Dossier
Copy-Item LICENSE $Dossier
Copy-Item THIRD_PARTY_NOTICES.md $Dossier
Copy-Item -Recurse licenses $Dossier
Copy-Item packaging\LISEZ-MOI-windows.txt "$Dossier\LISEZ-MOI.txt"

Compress-Archive -Path "$Dossier\*" `
    -DestinationPath "dist\RAD-Gardes-V7-windows-x64.zip" -Force

Write-Host "Dossier : $Racine\$Dossier"
Write-Host "Archive : $Racine\dist\RAD-Gardes-V7-windows-x64.zip"
