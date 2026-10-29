param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$tools = $PSScriptRoot

$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $csc)) {
    throw "csc.exe not found: $csc"
}

# Try CapCut install roots first, then ffmpeg on PATH.
$capcutRoots = @(
    (Join-Path $env:ProgramFiles 'CapCut'),
    (Join-Path ${env:ProgramFiles(x86)} 'CapCut'),
    'D:\Program Files\CapCut'
)
$ffmpeg = $null
foreach ($root in $capcutRoots) {
    if ($root -and (Test-Path -LiteralPath $root)) {
        $found = Get-ChildItem -LiteralPath $root -Filter 'ffmpeg.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $ffmpeg = $found.FullName; break }
    }
}
if (-not $ffmpeg) {
    $cmd = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($cmd) { $ffmpeg = $cmd.Source }
}
if (-not $ffmpeg -or -not (Test-Path -LiteralPath $ffmpeg)) {
    throw "ffmpeg.exe not found. Install CapCut or put ffmpeg on PATH."
}

Write-Output "root   : $Root"
Write-Output "ffmpeg : $ffmpeg"

New-Item -ItemType Directory -Force -Path (Join-Path $Root 'output\frames') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'audio\voice') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'assets\characters') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'assets\scenes') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'assets\props') | Out-Null

Get-ChildItem -LiteralPath (Join-Path $Root 'output\frames') -Filter '*.jpg' -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Output '1/5 compile renderer'
$exe = Join-Path $tools 'DemoRenderer.exe'
& $csc /nologo /target:exe "/out:$exe" /r:System.Drawing.dll (Join-Path $tools 'DemoRenderer.cs') (Join-Path $tools 'BeatGenerator.cs')
if ($LASTEXITCODE -ne 0) { throw "csc failed with exit code $LASTEXITCODE" }

Write-Output '2/5 render frames + beat + assets'
& (Join-Path $tools 'DemoRenderer.exe') $Root
if ($LASTEXITCODE -ne 0) { throw "renderer failed with exit code $LASTEXITCODE" }

Write-Output '3/5 generate SAPI voice lines'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tools 'make_voice.ps1') -Root $Root -Rate 2
if ($LASTEXITCODE -ne 0) { throw "make_voice failed with exit code $LASTEXITCODE" }

Write-Output '4/5 mix beat + voice'
$mix = Join-Path $Root 'audio\mix.wav'
if (Test-Path -LiteralPath $mix) { Remove-Item -LiteralPath $mix -Force }
$filter = '[0:a]volume=0.40,afade=t=out:st=23.2:d=0.8[bg];' +
          '[1:a]aformat=channel_layouts=stereo,adelay=2000|2000,volume=1.55[v1];' +
          '[2:a]aformat=channel_layouts=stereo,adelay=5200|5200,volume=1.55[v2];' +
          '[3:a]aformat=channel_layouts=stereo,adelay=9000|9000,volume=1.55[v3];' +
          '[4:a]aformat=channel_layouts=stereo,adelay=12500|12500,volume=1.55[v4];' +
          '[5:a]aformat=channel_layouts=stereo,adelay=16000|16000,volume=1.55[v5];' +
          '[6:a]aformat=channel_layouts=stereo,adelay=18600|18600,volume=1.55[v6];' +
          '[7:a]aformat=channel_layouts=stereo,adelay=21500|21500,volume=1.55[v7];' +
          '[bg][v1][v2][v3][v4][v5][v6][v7]amix=inputs=8:duration=first:normalize=0,volume=0.82,alimiter=limit=0.90,atrim=0:24[a]'
$old = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& $ffmpeg -y -hide_banner -loglevel warning `
    -i (Join-Path $Root 'audio\beat.wav') `
    -i (Join-Path $Root 'audio\voice\line01.wav') `
    -i (Join-Path $Root 'audio\voice\line02.wav') `
    -i (Join-Path $Root 'audio\voice\line03.wav') `
    -i (Join-Path $Root 'audio\voice\line04.wav') `
    -i (Join-Path $Root 'audio\voice\line05.wav') `
    -i (Join-Path $Root 'audio\voice\line06.wav') `
    -i (Join-Path $Root 'audio\voice\line07.wav') `
    -filter_complex $filter -map '[a]' -ac 2 -ar 44100 $mix 2>&1 | Out-Null
$code = $LASTEXITCODE
$ErrorActionPreference = $old
if ($code -ne 0) { throw "audio mix failed with exit code $code" }

Write-Output '5/5 encode H.264/AAC'
$video = Join-Path $Root 'output\street_corner_cafe_16x9_v01.mp4'
if (Test-Path -LiteralPath $video) { Remove-Item -LiteralPath $video -Force }
$old = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& $ffmpeg -y -hide_banner -loglevel warning -framerate 30 `
    -i (Join-Path $Root 'output\frames\frame_%04d.jpg') `
    -i $mix -c:v h264_mf -b:v 4M -pix_fmt yuv420p `
    -c:a aac -b:a 192k -movflags +faststart -shortest $video 2>&1 | Out-Null
$code = $LASTEXITCODE
$ErrorActionPreference = $old
if ($code -ne 0) { throw "encode failed with exit code $code" }

Get-Item -LiteralPath $video | Select-Object FullName, Length, LastWriteTime | Format-List
Write-Output 'DONE'
