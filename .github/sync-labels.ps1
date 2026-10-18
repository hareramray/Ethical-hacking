[CmdletBinding()]
param(
    [ValidatePattern('^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$')]
    [string]$Repo = 'hareramray/Ethical-hacking',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$catalogPath = Join-Path $PSScriptRoot 'labels.json'
$labels = Get-Content -LiteralPath $catalogPath -Raw -Encoding UTF8 | ConvertFrom-Json
$names = @{}

# Validate the complete catalog before making any GitHub changes.
if ($labels.Count -eq 0) { throw 'The label catalog is empty.' }
foreach ($label in $labels) {
    if ([string]::IsNullOrWhiteSpace($label.name) -or $label.name.Length -gt 50) {
        throw "Invalid label name: $($label.name)"
    }
    if ($names.ContainsKey($label.name)) { throw "Duplicate label: $($label.name)" }
    $names[$label.name] = $true
    if ($label.color -notmatch '^[0-9A-Fa-f]{6}$') {
        throw "Invalid color for label: $($label.name)"
    }
    if ([string]::IsNullOrWhiteSpace($label.description) -or $label.description.Length -gt 100) {
        throw "Invalid description for label: $($label.name)"
    }
}

if (-not $DryRun) {
    $null = Get-Command gh -ErrorAction Stop
}
foreach ($label in $labels) {
    if ($DryRun) {
        Write-Output ("Would create/update {0}: {1} (#{2})" -f $Repo, $label.name, $label.color)
        continue
    }
    & gh label create $label.name --repo $Repo --color $label.color --description $label.description --force
    if ($LASTEXITCODE -ne 0) {
        throw "Label sync failed at '$($label.name)'. Earlier labels may have been updated; rerun after resolving the error."
    }
    Write-Output ("Synced: {0}" -f $label.name)
}
Write-Output ("{0} labels {1}." -f $labels.Count, $(if ($DryRun) { 'validated' } else { 'synced' }))
