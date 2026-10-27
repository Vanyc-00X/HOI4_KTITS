# Remap Mir Kazualnosti tags onto vanilla HOI4 world map (Option A).
$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -ErrorAction SilentlyContinue
if (-not $Root) { $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Vanilla = "C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"

$OwnerMap = @{
  GER="CRE"; AUS="CRE"; CZE="CRE"
  SOV="KRZ"
  ITA="BTR"; ETH="BTR"; ALB="BTR"; AFA="BTR"
  JAP="DMK"; MAN="DMK"; MEN="DMK"
  USA="SOY"; PHI="SOY"; LIB="SOY"
  ENG="MUS"; IRE="MUS"
  FRA="ZLD"
  HOL="ADL"; BEL="ADL"; LUX="ADL"
  SWE="SVA"; NOR="SVA"; DEN="SVA"; FIN="SVA"; ICE="SVA"
  RAJ="KMS"; BRM="KMS"; NEP="KMS"; BHU="KMS"
  AST="ZKR"; NZL="ZKR"
  SPR="HRL"; POR="HRL"
  CHI="VCI"; PRC="VCI"; GXC="VCI"; YUN="VCI"; SHX="VCI"; XSM="VCI"; SIK="VCI"; TIB="VCI"
  POL="KZS"; LIT="KZS"; LAT="KZS"; EST="KZS"; ROM="KZS"; HUN="KZS"
  TUR="ISL"; PER="ISL"; AFG="ISL"; IRQ="ISL"; SAU="ISL"; YEM="ISL"; OMA="ISL"
  PAL="ISL"; JOR="ISL"; LEB="ISL"; SYR="ISL"; KUW="ISL"
  CAN="CLB"
  YUG="FDP"; GRE="FDP"; BUL="FDP"; SWI="FDP"
  ARG="ART"; CHL="ART"; URG="ART"; PAR="ART"
  BRA="NBL"; BOL="NBL"; PRU="NBL"; ECU="NBL"; COL="NBL"; VEN="NBL"
  MEX="TRF"; COS="TRF"; CUB="TRF"; DOM="TRF"; ELS="TRF"; GUA="TRF"; HAI="TRF"; HON="TRF"; NIC="TRF"; PAN="TRF"
  MON="ZML"; TAN="ZML"
  SIA="ISG"; MAL="ISG"
  INS="SHF"
  SAF="ZNS"
}

$Capitals = @{
  KRZ=219; CRE=64; BTR=2; DMK=282; SOY=361; MUS=126; ZLD=16; ADL=7
  SVA=141; KMS=439; ZKR=285; HRL=41; VCI=608; KZS=10; ISL=49; CLB=276
  FDP=107; ART=278; ZNS=275; TRF=277; ZML=330; NBL=500; ISG=1076; SHF=335
}

$CountryFiles = @{
  VCI="VCI - Velikaya Kazualnaya Imperiya.txt"
  SOY="SOY - Soevaya Respublika.txt"
  BTR="BTR - Chyornaya Tartariya.txt"
  KRZ="KRZ - Krasnaya Zemlya.txt"
  KZS="KZS - Kazachi Shtaty.txt"
  MUS="MUS - Korolevstvo Musi.txt"
  TRF="TRF - Travinnaya Federatsiya.txt"
  ZLD="ZLD - Demokraticheskiy Zelenodolsk.txt"
  ISL="ISL - Islamskaya Respublika.txt"
  CLB="CLB - Chelyaba.txt"
  ADL="ADL - Aydaliya.txt"
  DMK="DMK - Dmitro Knyazhestvo.txt"
  FDP="FDP - Federatsiya Deputatov.txt"
  CRE="CRE - Chyornaya Respublika.txt"
  SVA="SVA - Severnaya Assambleya.txt"
  ART="ART - Ayratskaya Respublika.txt"
  KMS="KMS - Kamilskoe Sodruzhestvo.txt"
  ZNS="ZNS - Zaynutdinovskiy Soyuz.txt"
  ZKR="ZKR - Respublika Zakariya.txt"
  ZML="ZML - Zemlya Zamaliya.txt"
  NBL="NBL - Novaya Bulatiya.txt"
  ISG="ISG - Respublika Ismagil.txt"
  HRL="HRL - Kharitonovskaya Liga.txt"
  SHF="SHF - Sharafutdinovskaya Federatsiya.txt"
}

$Maghreb = @(458,459,460,461,462,513,290,699,783)
$Colonial = @("MUS","ZLD","ADL","HRL")
$MkTags = @($Capitals.Keys)

# continent indices from map/continent.txt (1-based)
$C_AFRICA = 5
$C_ASIA = 6
$C_ME = 7

Write-Host "Root: $Root"
Write-Host "Loading province continents..."
$ProvCont = @{}
Get-Content (Join-Path $Vanilla "map\definition.csv") | ForEach-Object {
  $p = $_.Split(";")
  if ($p.Length -ge 8) {
    $provId = 0; $cont = 0
    if ([int]::TryParse($p[0], [ref]$provId) -and [int]::TryParse($p[7], [ref]$cont)) {
      $ProvCont[$provId] = $cont
    }
  }
}
Write-Host "  provinces:" $ProvCont.Count

function Get-StateContinent([string]$text) {
  if ($text -notmatch "provinces\s*=\s*\{([^}]*)\}") { return $null }
  $ids = $Matches[1].Split(@(" ","`t","`r","`n"), [System.StringSplitOptions]::RemoveEmptyEntries) | Where-Object { $_ -match "^\d+$" }
  $counts = @{}
  foreach ($id in $ids) {
    $provId = [int]$id
    if ($ProvCont.ContainsKey($provId)) {
      $c = $ProvCont[$provId]
      if ($c -gt 0) {
        if (-not $counts.ContainsKey($c)) { $counts[$c] = 0 }
        $counts[$c]++
      }
    }
  }
  if ($counts.Count -eq 0) { return $null }
  return ($counts.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 1).Key
}

function Resolve-Owner([string]$vanillaOwner, [int]$stateId, $continent) {
  $base = if ($OwnerMap.ContainsKey($vanillaOwner)) { $OwnerMap[$vanillaOwner] } else { $vanillaOwner }
  if ($Maghreb -contains $stateId) { return "ISL" }
  if ($null -ne $continent -and $continent -eq $C_AFRICA -and ($Colonial -contains $base -or $base -eq "MUS")) {
    return "ZNS"
  }
  if ($null -ne $continent -and $continent -eq $C_ME -and ($Colonial -contains $base -or $base -eq "MUS" -or $base -eq "ZLD")) {
    return "ISL"
  }
  if ($null -ne $continent -and $continent -eq $C_ASIA -and $vanillaOwner -eq "FRA") {
    return "ISG"
  }
  if ($null -ne $continent -and $continent -eq $C_ASIA -and $vanillaOwner -eq "ENG") {
    return "ISG"
  }
  return $base
}

function Remap-StateText([string]$text, [string]$newOwner) {
  # drop DLC releasable transfers
  $text = [regex]::Replace($text, "(?m)^\s*transfer_state_to\s*=\s*\w+\s*$", "")

  $text = [regex]::Replace($text, "(?m)^(\s*owner\s*=\s*)\w+", "`${1}$newOwner")
  $text = [regex]::Replace($text, "(?m)^(\s*controller\s*=\s*)\w+", "`${1}$newOwner")

  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($line in ($text -split "`n", -1)) {
    $eol = ""
    $raw = $line
    if ($raw -match "\r$") { $raw = $raw.TrimEnd("`r") }
    if ($raw -match "^(\s*)(add_core_of|add_claim_by)\s*=\s*(\w+)\s*$") {
      $indent = $Matches[1]
      $key = $Matches[2]
      $old = $Matches[3]
      $mapped = if ($OwnerMap.ContainsKey($old)) { $OwnerMap[$old] } else { $old }
      if ($MkTags -contains $mapped) {
        $lines.Add("$indent$key = $mapped")
      }
      continue
    }
    $lines.Add($raw)
  }
  $text = ($lines -join "`n")
  if ($text -notmatch "add_core_of\s*=\s*$newOwner") {
    $text = [regex]::Replace($text, "(?m)^(\s*owner\s*=\s*$newOwner)\s*$", "`${1}`n`t`tadd_core_of = $newOwner", 1)
  }
  return $text
}

# --- copy states ---
$src = Join-Path $Vanilla "history\states"
$dst = Join-Path $Root "history\states"
Write-Host "Remapping states into $dst"
if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
New-Item -ItemType Directory -Path $dst | Out-Null

$counts = @{}
foreach ($t in $MkTags) { $counts[$t] = 0 }
$unmapped = @{}

Get-ChildItem $src -Filter "*.txt" | ForEach-Object {
  $raw = Get-Content $_.FullName -Raw -Encoding UTF8
  if ($raw -notmatch "(?m)^\s*owner\s*=\s*(\w+)") {
    Set-Content -Path (Join-Path $dst $_.Name) -Value $raw -Encoding UTF8 -NoNewline
    return
  }
  $vanillaOwner = $Matches[1]
  if (-not $OwnerMap.ContainsKey($vanillaOwner)) {
    if (-not $unmapped.ContainsKey($vanillaOwner)) { $unmapped[$vanillaOwner] = 0 }
    $unmapped[$vanillaOwner]++
  }
  $stateId = -1
  if ($raw -match "(?m)^\s*id\s*=\s*(\d+)") { $stateId = [int]$Matches[1] }
  $cont = Get-StateContinent $raw
  $newOwner = Resolve-Owner $vanillaOwner $stateId $cont
  if ($MkTags -notcontains $newOwner) {
    Write-Host "Fallback state $stateId ($vanillaOwner) -> ZNS"
    $newOwner = "ZNS"
  }
  $new = Remap-StateText $raw $newOwner
  $counts[$newOwner]++
  # Write with UTF8 no BOM preferred
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText((Join-Path $dst $_.Name), $new, $utf8)
}

Write-Host "State counts:"
$counts.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object {
  Write-Host ("  {0}: {1}" -f $_.Key, $_.Value)
}
if ($unmapped.Count -gt 0) {
  Write-Host "WARNING unmapped owners:"
  $unmapped.GetEnumerator() | Sort-Object Name | ForEach-Object { Write-Host ("  {0}: {1}" -f $_.Key, $_.Value) }
}

# --- capitals ---
Write-Host "Updating capitals..."
$cdir = Join-Path $Root "history\countries"
foreach ($tag in $CountryFiles.Keys) {
  $path = Join-Path $cdir $CountryFiles[$tag]
  if (-not (Test-Path $path)) { Write-Host "MISSING $path"; continue }
  $text = Get-Content $path -Raw -Encoding UTF8
  $cap = $Capitals[$tag]
  if ($text -match "(?m)^capital\s*=\s*\d+") {
    $text = [regex]::Replace($text, "(?m)^capital\s*=\s*\d+", "capital = $cap", 1)
  } else {
    $text = "capital = $cap`n" + $text
  }
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($path, $text, $utf8)
}

# --- archive map ---
$mapDir = Join-Path $Root "map"
$archive = Join-Path $Root "_archive_custom_map"
if (Test-Path $mapDir) {
  if (Test-Path $archive) { Remove-Item $archive -Recurse -Force }
  Move-Item $mapDir $archive
  Write-Host "Archived custom map -> $archive"
}

# --- descriptors ---
foreach ($name in @("descriptor.mod", "Mir_Kazualnosti.mod")) {
  $path = Join-Path $Root $name
  if (-not (Test-Path $path)) { continue }
  $lines = Get-Content $path | Where-Object { $_ -notmatch "map/strategicregions" }
  $text = ($lines -join "`n") + "`n"
  $text = [regex]::Replace($text, 'version="[^"]*"', 'version="0.13.0-vanilla-map"')
  $utf8 = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($path, $text, $utf8)
  Write-Host "Patched $name"
}

# --- doc ---
$doc = @()
$doc += "# Vanilla world remap (v0.13)"
$doc += ""
$doc += "Custom Kazualia map archived to ``_archive_custom_map/``."
$doc += "Option A: all land states owned by the 24 MK tags."
$doc += ""
$doc += "| TAG | States | Capital |"
$doc += "|-----|--------|---------|"
foreach ($tag in ($Capitals.Keys | Sort-Object)) {
  $doc += "| $tag | $($counts[$tag]) | $($Capitals[$tag]) |"
}
$docPath = Join-Path $Root "docs\VANILLA_WORLD_REMAP.md"
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($docPath, ($doc -join "`n") + "`n", $utf8)
Write-Host "Wrote $docPath"
Write-Host "DONE"
