param(
  [ValidateSet('semua', 'situs', 'admin')]
  [string]$Target = 'semua'
)

$ProgressPreference = 'SilentlyContinue'

$situs = 'http://localhost:1313/'
$admin = 'http://localhost:1313/admin/'

function Get-BrowserAdmin {
  # Sveltia CMS hanya jalan di peramban berbasis Chromium (Edge/Chrome/Brave).
  # Firefox dan Zen (Gecko) akan menolak atau gagal memuat.
  $calon = @(
    "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
    "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "$env:ProgramFiles\BraveSoftware\Brave-Browser\Application\brave.exe"
  ) | Where-Object { $_ -and (Test-Path $_) }
  return ($calon | Select-Object -First 1)
}

function Test-Server {
  try {
    $r = Invoke-WebRequest -Uri $situs -UseBasicParsing -TimeoutSec 3
    return ($r.StatusCode -eq 200)
  } catch {
    return $false
  }
}

if ($Target -eq 'semua') {
  Start-Sleep -Seconds 4
  Start-Process $situs
  Start-Sleep -Seconds 3
}

if ($Target -eq 'admin' -and -not (Test-Server)) {
  Write-Host ''
  Write-Host '  Server lokal belum menyala.'
  Write-Host '  Jalankan dulu Pratinjau.cmd, lalu buka lagi berkas ini.'
  Write-Host ''
  Start-Sleep -Seconds 6
  exit 1
}

$browser = Get-BrowserAdmin
if ($browser) {
  Start-Process $browser $admin
  Write-Host "  Admin dibuka di: $(Split-Path $browser -Leaf)"
} else {
  Start-Process $admin
  Write-Host '  Edge/Chrome tidak ditemukan - admin dibuka di peramban bawaan.'
  Write-Host '  Bila halaman admin tidak muncul, pasang Microsoft Edge lalu coba lagi.'
}
