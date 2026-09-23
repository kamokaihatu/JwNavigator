# PowerShell版 外部変形: 書込レイヤに点(1,1)を1個作図する応答を書く。
# mark_point.pyのPowerShell移植版。追加のexe/pythonを一切呼ばずに
# jwc_temp.txtへ返信するだけ(cmd.exe/PowerShell.exeはWindows標準の
# 署名済みバイナリなので、セキュリティソフトに追加exeとしてブロック
# されにくいという想定に基づく)。
$ErrorActionPreference = "Stop"
$enc = [System.Text.Encoding]::GetEncoding(932)  # cp932 / Shift_JIS

$MARK_X = 1
$MARK_Y = 1
$CHAIN_TO = "A_SAVE.BAT"

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

$temp = Find-Temp
if (-not $temp) {
    Write-Host "jwc_temp.txt not found. cwd=" (Get-Location)
    exit 1
}
Write-Host "target: $temp"

$body = ("pt {0:g} {1:g}`r`nh/{2}`r`n" -f $MARK_X, $MARK_Y, $CHAIN_TO)
[System.IO.File]::WriteAllBytes($temp, $enc.GetBytes($body))
Write-Host ("[MARK] pt {0} {1} を書込レイヤへ返信し、{2} へ連鎖しました" -f $MARK_X, $MARK_Y, $CHAIN_TO)
