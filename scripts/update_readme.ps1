# PowerShell script to update the dynamic section of README.md
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\update_readme.ps1

# Resolve repository root (one level up from the scripts folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $scriptDir "..")
$repoRoot = $repoRoot.Path

# Ensure git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git not found in PATH. Install Git and try again."
    exit 1
}

# Gather dynamic info
$commitCount = (& git -C $repoRoot rev-list --count HEAD) 2>$null
if (-not $commitCount) { $commitCount = 0 }
$lastCommit = (& git -C $repoRoot log -1 --pretty=format:'%an <%ae>') 2>$null
if (-not $lastCommit) { $lastCommit = 'N/A' }
$currentBranch = (& git -C $repoRoot rev-parse --abbrev-ref HEAD) 2>$null
if (-not $currentBranch) { $currentBranch = 'N/A' }

$contributorsRaw = (& git -C $repoRoot shortlog -sne) 2>$null
$contributorsCount = 0
if ($contributorsRaw) {
    $contributorsCount = ($contributorsRaw | Where-Object { $_ -match '\S' } | Measure-Object).Count
}

# Build dynamic block
$dynamic = @"<!-- DYNAMIC_START -->
- Commit count: $commitCount
- Current branch: $currentBranch
- Last commit by: $lastCommit
- Registered contributors: $contributorsCount
<!-- DYNAMIC_END -->"@

# Update README.md
$readmePath = Join-Path $repoRoot 'README.md'
if (-not (Test-Path $readmePath)) { Write-Error "README.md not found at $readmePath"; exit 1 }

$readmeContent = Get-Content -Raw -Path $readmePath -ErrorAction Stop

# Replace existing dynamic region or append if missing
if ($readmeContent -match '(?ms)<!-- DYNAMIC_START -->.*?<!-- DYNAMIC_END -->') {
    $newReadme = [regex]::Replace($readmeContent, '(?ms)<!-- DYNAMIC_START -->.*?<!-- DYNAMIC_END -->', [System.Text.RegularExpressions.Regex]::Escape($dynamic).Replace('\x0D\x0A','`n'))
    # The Replace above escapes the dynamic block; do a simpler replace instead
    $newReadme = [regex]::Replace($readmeContent, '(?ms)<!-- DYNAMIC_START -->.*?<!-- DYNAMIC_END -->', $dynamic)
} else {
    $newReadme = $readmeContent.TrimEnd() + "`n`n" + $dynamic
}

# Write the updated README
Set-Content -Path $readmePath -Value $newReadme -Encoding UTF8
Write-Output "README.md dynamic section updated."
