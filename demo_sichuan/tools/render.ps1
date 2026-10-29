param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$Python = ''
)

$ErrorActionPreference = 'Stop'
$tools = $PSScriptRoot

$csc = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $csc)) { throw "csc.exe not found: $csc" }

if (-not $Python) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $Python) { $Python = Join-Path $Root '..\env\comfy\Scripts\python.exe' }
}
$python = $Python
$encoder = (& $python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())').Trim()
if (-not (Test-Path -LiteralPath $encoder)) { throw "encoder.exe not found: $encoder" }

Write-Output "root   : $Root"
Write-Output "encoder: $encoder"

New-Item -ItemType Directory -Force -Path (Join-Path $Root 'output\frames') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'audio\voice') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'assets\characters') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'assets\scenes') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root 'assets\props') | Out-Null

Get-ChildItem -LiteralPath (Join-Path $Root 'output\frames') -Filter '*.jpg' -ErrorAction SilentlyContinue | Remove-Item -Force

Write-Output '1/5 compile renderer'
$exe = Join-Path $tools 'SichuanRenderer.exe'
& $csc /nologo /target:exe "/out:$exe" /r:System.Drawing.dll (Join-Path $tools 'SichuanRenderer.cs') (Join-Path $tools 'SichuanBeatGenerator.cs')
if ($LASTEXITCODE -ne 0) { throw "csc failed with exit code $LASTEXITCODE" }

Write-Output '2/5 render frames + beat + assets'
& $exe $Root
if ($LASTEXITCODE -ne 0) { throw "renderer failed with exit code $LASTEXITCODE" }

Write-Output '3/5 generate SAPI voice lines'
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $tools 'make_voice.ps1') -Root $Root -Rate 1
if ($LASTEXITCODE -ne 0) { throw "make_voice failed with exit code $LASTEXITCODE" }

Write-Output '4/5 mix beat + voice'
$mix = Join-Path $Root 'audio\mix.wav'
if (Test-Path -LiteralPath $mix) { Remove-Item -LiteralPath $mix -Force }
$filter = '[0:a]volume=0.40,afade=t=out:st=28.5:d=1.5[bg];' +
          '[1:a]aformat=channel_layouts=stereo,adelay=1000|1000,volume=1.55[v1];' +
          '[2:a]aformat=channel_layouts=stereo,adelay=5300|5300,volume=1.55[v2];' +
          '[3:a]aformat=channel_layouts=stereo,adelay=10300|10300,volume=1.55[v3];' +
          '[4:a]aformat=channel_layouts=stereo,adelay=15300|15300,volume=1.55[v4];' +
          '[5:a]aformat=channel_layouts=stereo,adelay=20300|20300,volume=1.55[v5];' +
          '[6:a]aformat=channel_layouts=stereo,adelay=25600|25600,volume=1.55[v6];' +
          '[bg][v1][v2][v3][v4][v5][v6]amix=inputs=7:duration=first:normalize=0,volume=0.82,alimiter=limit=0.90,atrim=0:30[a]'
$old = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& $encoder -y -hide_banner -loglevel warning `
    -i (Join-Path $Root 'audio\beat.wav') `
    -i (Join-Path $Root 'audio\voice\line01.wav') `
    -i (Join-Path $Root 'audio\voice\line02.wav') `
    -i (Join-Path $Root 'audio\voice\line03.wav') `
    -i (Join-Path $Root 'audio\voice\line04.wav') `
    -i (Join-Path $Root 'audio\voice\line05.wav') `
    -i (Join-Path $Root 'audio\voice\line06.wav') `
    -filter_complex $filter -map '[a]' -ac 2 -ar 44100 $mix 2>&1 | Out-Null
$code = $LASTEXITCODE
$ErrorActionPreference = $old
if ($code -ne 0) { throw "audio mix failed with exit code $code" }

Write-Output '5/5 encode H.264/AAC'
$video = Join-Path $Root 'output\sichuan_teahouse_16x9_v01.mp4'
if (Test-Path -LiteralPath $video) { Remove-Item -LiteralPath $video -Force }
$old = $ErrorActionPreference
$ErrorActionPreference = 'Continue'
& $encoder -y -hide_banner -loglevel warning -framerate 30 `
    -i (Join-Path $Root 'output\frames\frame_%04d.jpg') `
    -i $mix -c:v libx264 -b:v 4M -pix_fmt yuv420p `
    -c:a aac -b:a 192k -movflags +faststart -shortest $video 2>&1 | Out-Null
$code = $LASTEXITCODE
$ErrorActionPreference = $old
if ($code -ne 0) { throw "encode failed with exit code $code" }

Get-Item -LiteralPath $video | Select-Object FullName, Length, LastWriteTime | Format-List
Write-Output 'DONE'
