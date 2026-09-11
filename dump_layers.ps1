# PowerShell版 外部変形: 全レイヤグループ×全レイヤ(16x16=256)の状態を取得し、
# LAYER_RESTORE.JWLを生成する(dump_layers.pyのwrite_jwl()相当のみ、
# CSV/JSON等のデバッグ出力は省略した最小版)。
# 引数: ラベル(省略時 X) ※dump_layers.pyと同じ呼び出し規約
param(
    [string]$Label = "X"
)

$ErrorActionPreference = "Stop"
$enc = [System.Text.Encoding]::GetEncoding(932)  # cp932 / Shift_JIS

function Find-Temp {
    $here = $PSScriptRoot
    $candidates = @(
        (Join-Path (Get-Location) "jwc_temp.txt"),
        (Join-Path $here "jwc_temp.txt"),
        "C:\jww\jwc_temp.txt"
    )
    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p -PathType Leaf) { return $p }
    }
    return $null
}

function Reply-Message([string]$Path, [string]$Msg) {
    try {
        $bytes = $enc.GetBytes("he " + $Msg + "`r`n")
        [System.IO.File]::WriteAllBytes($Path, $bytes)
    } catch {
        Write-Host "reply write failed: $_"
    }
}

function Convert-ToJwl([string]$v) {
    # ones=表示(1)/非表示(0)、tens=編集可能(1),編集不可(0),プロテクト(2,3,6,7)
    $n = 0
    if (-not [int]::TryParse($v, [ref]$n)) { return 2 }
    $ones = $n % 10
    $tens = [Math]::Floor($n / 10)
    if ($ones -eq 0) {
        $state = 0
    } elseif ($tens -eq 1 -or $tens -eq 3 -or $tens -eq 7) {
        $state = 2
    } else {
        $state = 1
    }
    if ($tens -eq 2 -or $tens -eq 3) { $prot = 1 }
    elseif ($tens -eq 6 -or $tens -eq 7) { $prot = 2 }
    else { $prot = 0 }
    return $prot * 10 + $state
}

$temp = Find-Temp
if (-not $temp) {
    Write-Host "jwc_temp.txt not found. cwd=" (Get-Location)
    exit 1
}
Write-Host "source: $temp"

$rawBytes = [System.IO.File]::ReadAllBytes($temp)
Write-Host ("jwc_temp: {0} bytes" -f $rawBytes.Length)
$text = $enc.GetString($rawBytes)
$lines = $text -split "`r`n|`n"

$reLGN = [regex]"^lgn(.*)$"
$reLYN = [regex]"^lyn(.*)$"
$reLG = [regex]"^lg([0-9a-fA-F])\s*(\S*)"
$reLY = [regex]"^ly([0-9a-fA-F])\s*(\S*)"

$gstates = @{}
$cell = @{}
$writeGroup = $null
$writeLayer = $null
$curGroup = $null

foreach ($rawLine in $lines) {
    $s = $rawLine.Trim()
    if ($s.Length -eq 0) { continue }

    if ($reLGN.IsMatch($s)) { continue }
    if ($reLYN.IsMatch($s)) { continue }

    $m = $reLG.Match($s)
    if ($m.Success) {
        $g = $m.Groups[1].Value.ToLower()
        $v = $m.Groups[2].Value
        if ($v -eq "") {
            if ($null -eq $writeGroup) { $writeGroup = $g }
        } else {
            $curGroup = $g
            $gstates[$g] = $v
        }
        continue
    }

    $m = $reLY.Match($s)
    if ($m.Success) {
        $ly = $m.Groups[1].Value.ToLower()
        $v = $m.Groups[2].Value
        if ($v -eq "") {
            if ($null -eq $writeLayer) { $writeLayer = $ly }
            continue
        }
        $cell["$curGroup,$ly"] = $v
        continue
    }
}

$ngroup = ($gstates.Keys | Sort-Object -Unique).Count
$nlayer = $cell.Keys.Count
Write-Host ("groups: {0} layers: {1} write: lg{2}/ly{3}" -f $ngroup, $nlayer, $writeGroup, $writeLayer)

$hexDigits = "0123456789abcdef".ToCharArray()

if ($ngroup -eq 16 -and $nlayer -eq 256) {
    $lines_out = New-Object System.Collections.Generic.List[string]
    $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
    $lines_out.Add("# Jw_cad レイヤ設定ファイル (自動生成 $Label`_$stamp)")
    $lines_out.Add("# [設定]→[環境設定ファイル]→[読込み] で *.JWL を選んで読み込むと")
    $lines_out.Add("# 全レイヤグループ・全レイヤの状態がこの内容に戻ります。")
    $lines_out.Add("#")
    $lines_out.Add("PRTCT_CH =  1")

    foreach ($g in $hexDigits) {
        $gs = $g.ToString()
        $vals = New-Object System.Collections.Generic.List[int]
        if ($gs -eq $writeGroup) {
            $vals.Add(100)
        } else {
            $gv = if ($gstates.ContainsKey($gs)) { $gstates[$gs] } else { "11" }
            $vals.Add((Convert-ToJwl $gv))
        }
        foreach ($l in $hexDigits) {
            $ls = $l.ToString()
            if ($gs -eq $writeGroup -and $ls -eq $writeLayer) {
                $vals.Add(100)
            } else {
                $key = "$gs,$ls"
                $lv = if ($cell.ContainsKey($key)) { $cell[$key] } else { "11" }
                $vals.Add((Convert-ToJwl $lv))
            }
        }
        $joined = ($vals | ForEach-Object { "{0,3}" -f $_ }) -join ","
        $lines_out.Add("LAYCND_$($gs.ToUpper()) =$joined")
    }

    $outDir = Split-Path -Parent $temp
    $jwlPath = Join-Path $outDir "LAYER_RESTORE.JWL"
    $outBytes = $enc.GetBytes(($lines_out -join "`r`n") + "`r`n")
    [System.IO.File]::WriteAllBytes($jwlPath, $outBytes)
    Write-Host "jwl: $jwlPath"
    Reply-Message $temp ("[$Label] group=$ngroup layer=$nlayer write=lg$writeGroup/ly$writeLayer  JWL保存OK")
} else {
    Write-Host "jwl: SKIP (group=$ngroup layer=$nlayer 不完全なため復元ファイルは作らない)"
    Reply-Message $temp ("[$Label] group=$ngroup layer=$nlayer write=lg$writeGroup/ly$writeLayer  JWL未作成(256レイヤ揃わず)")
}
