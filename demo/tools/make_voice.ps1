param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [int]$Rate = 0
)

$ErrorActionPreference = 'Stop'

$voiceDir = Join-Path $Root 'audio\voice'
$linesFile = Join-Path $voiceDir 'lines.txt'
if (-not (Test-Path -LiteralPath $linesFile)) {
    throw "Missing voice lines: $linesFile"
}

Add-Type -AssemblyName System.Speech

function Get-WavSeconds {
    param([string]$Path)
    $b = [System.IO.File]::ReadAllBytes($Path)
    $sr = [BitConverter]::ToInt32($b, 24)
    $br = [BitConverter]::ToInt32($b, 28)
    $dataSize = 0
    for ($i = 0; $i -le $b.Length - 8; $i++) {
        if ($b[$i] -eq 100 -and $b[$i+1] -eq 97 -and $b[$i+2] -eq 116 -and $b[$i+3] -eq 97) {
            $dataSize = [BitConverter]::ToInt32($b, $i + 4)
            break
        }
    }
    if ($br -le 0) { return 0 }
    return [math]::Round($dataSize / $br, 3)
}

$lines = @(Get-Content -LiteralPath $linesFile -Encoding UTF8 | Where-Object { $_.Trim().Length -gt 0 })
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $synth.SelectVoice('Microsoft Huihui Desktop')
} catch {
    $zh = $synth.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Culture.Name -like 'zh-*' } | Select-Object -First 1
    if ($zh) { $synth.SelectVoice($zh.VoiceInfo.Name) }
}
$synth.Rate = $Rate
$synth.Volume = 100

$manifest = @()
for ($i = 0; $i -lt $lines.Count; $i++) {
    $text = $lines[$i].Trim()
    $file = Join-Path $voiceDir ('line{0:00}.wav' -f ($i + 1))
    if (Test-Path -LiteralPath $file) { Remove-Item -LiteralPath $file -Force }
    $synth.SetOutputToWaveFile($file)
    $synth.Speak($text)
    $synth.SetOutputToNull()
    $sec = Get-WavSeconds -Path $file
    $manifest += [pscustomobject]@{
        index = $i + 1
        start_s = @(2.0, 5.2, 9.0, 12.5, 16.0, 18.6, 21.5)[$i]
        duration_s = $sec
        file = ('audio/voice/line{0:00}.wav' -f ($i + 1))
        text = $text
    }
    Write-Output ("line{0:00}: {1}s  {2}" -f ($i + 1), $sec, $text)
}
$synth.Dispose()

$manifest | Export-Csv -LiteralPath (Join-Path $voiceDir 'manifest.csv') -NoTypeInformation -Encoding UTF8
Write-Output ("voice lines: {0}" -f $manifest.Count)
