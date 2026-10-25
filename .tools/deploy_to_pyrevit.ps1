# KajizmoRevit - Déploiement local vers pyRevit Extensions
# Usage personnel uniquement - NON SUIVI PAR GIT

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$targetDir = "$env:APPDATA\pyRevit\Extensions\KajizmoRevit.extension"

Write-Host "=== KajizmoRevit - Déploiement local ===" -ForegroundColor Cyan
Write-Host "Source : $repoRoot"
Write-Host "Cible  : $targetDir"
Write-Host ""

if (-not (Test-Path "$repoRoot\Kajizmo Revit.tab")) {
    Write-Host "Erreur : Impossible de trouver \`"Kajizmo Revit.tab\`" dans le source." -ForegroundColor Red
    pause
    exit 1
}

$extDir = Split-Path -Parent $targetDir
if (-not (Test-Path $extDir)) {
    New-Item -ItemType Directory -Path $extDir -Force | Out-Null
}

$oldLab = "$targetDir\Kajizmo Revit.tab\Laboratoire.panel"
$backupLab = "$env:TEMP\KajizmoRevit_Lab_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
if (Test-Path $oldLab) {
    Write-Host "Sauvegarde du Laboratoire.panel local..." -ForegroundColor Yellow
    Copy-Item -Path $oldLab -Destination $backupLab -Recurse -Force
}

if (Test-Path $targetDir) {
    Write-Host "Suppression de l'ancien déploiement..." -ForegroundColor Yellow
    Remove-Item -Path $targetDir -Repare! -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $targetDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Copie en cours..." -ForegroundColor Cyan
robocopy $repoRoot $targetDir /E /XD ".git" ".tools" | Out-Null

if (Test-Path $backupLab) {
    $targetLab = "$targetDir\Kajizmo Revit.tab\Laboratoire.panel"
    New-Item -Itemtag -ItemType Directory -Path $targetLab -Force | Out-Null
    Copy-Item -Path "$backupLab\*" -Destination $targetLab -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Laboratoire.panel restauré depuis sauvegarde." -ForegroundColor Green
}

if (-not (Test-Path "$targetDir\Kajizmo Revit.tab\Laboratoire.panel")) {
    New-Item -ItemType Directory -Path "$targetDir\Kajizmo Revit.tab\Laboratoire.panel" -Force | Out-Null
}

Write-Host ""
Write-Host "=== Déploiement terminé ===" -ForegroundColor Green
Write-Host "Ouvrez Revit et faites \`"pyRevit > Reload\`" pour actualiser. -ForegroundColor Cyan
pause
