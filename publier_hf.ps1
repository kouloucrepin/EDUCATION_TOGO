# =============================================================================
# Publication du dashboard sur Hugging Face Spaces (koulou/EDUCATION_TOGO)
#
# Usage :
#   .\publier_hf.ps1 "feat: description courte du changement"
#   .\publier_hf.ps1 "feat: ..." -Reclone     # repartir d'un clone tout neuf
#   .\publier_hf.ps1 "feat: ..." -Modele      # premier push : forcer le full re-add
#
# Le script : clone le Space si besoin, active git-lfs pour les CSV/PDF,
# synchronise le projet de façon incrémentale SANS secrets ni artefacts,
# vérifie qu'aucune clé API ne fuite, montre le poids total, committe et pousse.
# =============================================================================
param(
    [Parameter(Mandatory = $true)]
    [string]$Message,
    [switch]$Reclone,
    [switch]$Modele
)

$Projet = "c:\Users\Ultra Tech\Desktop\SOLUTION1\Competition 3"
$Clone  = "c:\Users\Ultra Tech\Desktop\SOLUTION1\EDUCATION_TOGO"
$Espace = "https://huggingface.co/spaces/koulou/EDUCATION_TOGO"

# --- 0. Clone du Space (auto si absent, ou force avec -Reclone) --------------
if ($Reclone -and (Test-Path $Clone)) {
    Write-Host "Suppression de l'ancien clone..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $Clone
}
if (-not (Test-Path "$Clone\.git")) {
    Write-Host "Clonage du Space..." -ForegroundColor Cyan
    git clone $Espace $Clone 2>&1
    if (-not $?) { Write-Host "ERREUR : clonage impossible." -ForegroundColor Red; exit 1 }
}

Set-Location $Clone

# --- 1. git-lfs pour les fichiers volumineux (HF exige LFS >10 Mo) ----------
git lfs install --local | Out-Null
# L'ajout est idempotent : si deja dans .gitattributes, ca ne change rien
git lfs track "*.csv" "*.pdf" | Out-Null

# --- 2. Synchronisation incrementale (seulement fichiers modifies) -----------
Write-Host "`n--- Copie des fichiers (incrementale) ---" -ForegroundColor Cyan
$robocopy_exit = robocopy $Projet $Clone /E /XO /NP `
    /XD exports_onglet1 exports_onglet2 exports_onglet3 exports_onglet4 `
        .git __pycache__ .ipynb_checkpoints `
    /XF .env *.pyc *.pyo publier_hf.ps1 /NFL /NDL /NJH
# robocopy exit codes : 0-7 = success, 8+ = error
if ($LASTEXITCODE -ge 8) {
    Write-Host "ERREUR robocopy (code $LASTEXITCODE)." -ForegroundColor Red; exit 1
}

# On recopie aussi .gitattributes (le source peut ne pas l'avoir)
if (Test-Path "$Clone\.gitattributes") {
    Copy-Item "$Clone\.gitattributes" "$Projet\.gitattributes" -Force
}

# --- 3. Securite : aucun secret dans le clone --------------------------------
if (Test-Path "$Clone\.env") {
    Remove-Item "$Clone\.env" -Force
    Write-Host "ATTENTION : un .env trainait dans le clone - supprime." -ForegroundColor Yellow
}
Get-ChildItem $Clone -Recurse -Include *.env, *.env.* -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch '\\\.git\\' } |
    ForEach-Object { Remove-Item $_.FullName -Force; Write-Host "Supprime : $($_.Name)" -ForegroundColor Yellow }

$fuites = Get-ChildItem $Clone -Recurse -Include *.py, *.html, *.md, *.yml, *.yaml -File |
    Where-Object { $_.FullName -notmatch '\\\.git\\' } |
    Select-String -Pattern 'AIza[0-9A-Za-z_-]{30,}' -ErrorAction SilentlyContinue
if ($fuites) {
    Write-Host "BLOCAGE : une cle API semble ecrite en dur :" -ForegroundColor Red
    $fuites | Select-Object -First 5 | ForEach-Object { Write-Host "  $($_.Path):$($_.LineNumber)" }
    exit 1
}

# --- 4. Staging & estimation du poids ----------------------------------------
Write-Host "`n--- Changements a publier ---" -ForegroundColor Cyan
if ($Modele) {
    git add --all --force
} else {
    git add --all
}
git status --short | Select-Object -First 30

# Poids total des fichiers staged
$poids = git diff --cached --numstat |
    ForEach-Object { ($_ -split '\s+')[0] -as [int] } |
    Measure-Object -Sum
if ($poids.Sum -and $poids.Sum -gt 0) {
    $poidsMo = [math]::Round($poids.Sum / 1MB, 1)
    Write-Host "`nPoids total a pousser : $poidsMo Mo" -ForegroundColor Yellow
    if ($poidsMo -gt 50) {
        Write-Host "ATTENTION : > 50 Mo, verifie que les CSV sont bien en LFS :" -ForegroundColor Red
        Write-Host "  git lfs ls-files" -ForegroundColor Gray
    }
} else {
    Write-Host "`nSeuls des suppressions ou meta-donnees." -ForegroundColor Yellow
}

# --- 5. Commit + push --------------------------------------------------------
git diff --cached --quiet
if ($?) {
    Write-Host "`nRien a publier : le Space est deja a jour." -ForegroundColor Green
    exit 0
}
git commit -m $Message
Write-Host "`n--- Push (cette etape peut prendre 1-3 min selon le volume LFS) ---" -ForegroundColor Cyan
git push origin main
if ($?) {
    Write-Host "`nPousse ! Construction du Space (3-8 min) :" -ForegroundColor Green
    Write-Host "  $Espace`?logs=build"
    Write-Host "`nRappels :" -ForegroundColor Yellow
    Write-Host "  - Settings > Variables and secrets > New secret : GEMMA_API_KEY"
} else {
    Write-Host "`nEchec du push. Si 403 : huggingface-cli login (compte koulou, jeton Write)." -ForegroundColor Red
}
