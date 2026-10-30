# Install the dev-workflow commands, agents and hook into your Claude Code config.
# Existing files with the same name are backed up, never silently overwritten.
$ErrorActionPreference = "Stop"

$Src = $PSScriptRoot
$Dest = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME ".claude" }
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

foreach ($sub in "skills", "agents", "hooks", "scripts") {
    New-Item -ItemType Directory -Force -Path (Join-Path $Dest $sub) | Out-Null
}

function Install-Item($from, $to) {
    if (Test-Path $to) {
        Move-Item $to "$to.bak-$Stamp"
        Write-Output "backed up  $to -> $to.bak-$Stamp"
    }
    Copy-Item -Recurse $from $to
    Write-Output "installed  $to"
}

Get-ChildItem -Directory (Join-Path $Src "skills") | ForEach-Object {
    Install-Item $_.FullName (Join-Path $Dest "skills\$($_.Name)")
}
Get-ChildItem -File (Join-Path $Src "agents") -Filter *.md | ForEach-Object {
    Install-Item $_.FullName (Join-Path $Dest "agents\$($_.Name)")
}
Get-ChildItem -File (Join-Path $Src "hooks") -Filter *.py | ForEach-Object {
    Install-Item $_.FullName (Join-Path $Dest "hooks\$($_.Name)")
}
Get-ChildItem -File (Join-Path $Src "scripts") -Filter *.py | ForEach-Object {
    Install-Item $_.FullName (Join-Path $Dest "scripts\$($_.Name)")
}

Write-Output ""
Write-Output "Done. One manual step: merge the Stop hook from settings.example.json into"
Write-Output "$Dest\settings.json (don't replace the file; add the `"hooks`" block)."
Write-Output "Then restart Claude Code and type /dev- to see the commands."
