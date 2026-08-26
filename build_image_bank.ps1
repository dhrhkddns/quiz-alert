# Build questions.json from exam image pairs + Windows OCR answer extraction.
# ASCII-only source; circled digits via Unicode codepoints.
$ErrorActionPreference = 'Stop'
chcp 65001 | Out-Null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Project = Split-Path -Parent $MyInvocation.MyCommand.Path
$downloads = 'C:\Users\Administrator\Downloads'
$parent = Get-ChildItem -LiteralPath $downloads -Directory | Where-Object { $_.Name -like '*QUESTION_ANSWERS*' } | Select-Object -First 1
if (-not $parent) { throw 'QUESTION_ANSWERS folder not found under Downloads' }
$SrcRoot = (Get-ChildItem -LiteralPath $parent.FullName -Directory | Select-Object -First 1).FullName
if (-not (Test-Path -LiteralPath (Join-Path $SrcRoot 'exam_data.json'))) { throw "exam_data.json missing under $SrcRoot" }
Write-Host "SrcRoot: $SrcRoot"
$MediaDir = Join-Path $Project 'exam_images'
$QDir = Join-Path $MediaDir 'questions'
$ADir = Join-Path $MediaDir 'answers'
$OutJson = Join-Path $Project 'questions.json'
$Report = Join-Path $Project '_ocr_answer_report.json'

New-Item -ItemType Directory -Force -Path $QDir, $ADir | Out-Null

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Storage.StorageFile,Windows.Foundation,ContentType=WindowsRuntime]

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
})[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
if (-not $engine) { throw 'Windows OCR engine unavailable' }

function Ocr-File([string]$path) {
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    return $result.Text
}

# U+2460..2464 = circled 1-5, U+2776.. = dingbat, U+3260.. hangul circled (OCR misreads)
function New-CircledMap {
    $m = @{}
    for ($i = 0; $i -lt 5; $i++) {
        $m[[string][char](0x2460 + $i)] = $i + 1
        $m[[string][char](0x2776 + $i)] = $i + 1
    }
    foreach ($pair in @(
        @(0x3260,1),@(0x3261,2),@(0x3262,3),@(0x3263,4),
        @(0x3264,1),@(0x3265,2),@(0x3266,3),@(0x3267,4),
        @(0x3268,2),@(0x3269,3),@(0x326A,4),@(0x326B,1),
        @(0x326C,2),@(0x326D,3),@(0x326E,4),@(0x326F,1),
        @(0x320E,1),@(0x320F,2),@(0x3210,3),@(0x3211,4)
    )) {
        $m[[string][char]$pair[0]] = $pair[1]
    }
    $m['1'] = 1; $m['2'] = 2; $m['3'] = 3; $m['4'] = 4
    return $m
}
$script:CircledMap = New-CircledMap

function Map-CircledToken([string]$token) {
    if ([string]::IsNullOrWhiteSpace($token)) { return $null }
    $t = $token.Trim()
    if ($script:CircledMap.ContainsKey($t)) { return $script:CircledMap[$t] }
    foreach ($ch in $t.ToCharArray()) {
        $s = [string]$ch
        if ($script:CircledMap.ContainsKey($s)) { return $script:CircledMap[$s] }
    }
    if ($t -match '(?<![0-9])([1-4])(?![0-9])') { return [int]$Matches[1] }
    return $null
}

function Extract-Answer([string]$ocrText, [int]$qNum) {
    if ([string]::IsNullOrWhiteSpace($ocrText)) {
        return @{ answer = $null; method = 'empty'; confidence = 'none' }
    }
    $text = $ocrText -replace '\r', ''

    $answerLine = [regex]::Match($text, 'ANSWER\s*([^\n]+)', 'IgnoreCase')
    if ($answerLine.Success) {
        $chunk = $answerLine.Groups[1].Value
        $pairs = [regex]::Matches($chunk, '(\d+)\s*[\.]\s*(\S{1,4})')
        foreach ($p in $pairs) {
            $n = [int]$p.Groups[1].Value
            if ($n -eq $qNum) {
                $ans = Map-CircledToken $p.Groups[2].Value
                if ($ans -ge 1 -and $ans -le 4) {
                    return @{ answer = $ans; method = 'ANSWER_line'; confidence = 'high' }
                }
            }
        }
        $one = [regex]::Match($chunk, '[\.]\s*(\S{1,4})')
        if ($one.Success) {
            $ans = Map-CircledToken $one.Groups[1].Value
            if ($ans -ge 1 -and $ans -le 4) {
                return @{ answer = $ans; method = 'ANSWER_single'; confidence = 'medium' }
            }
        }
    }

    $lead = [regex]::Match($text, ('^\s*{0}\s*[\.\)]?\s*(\S)' -f $qNum))
    if ($lead.Success) {
        $ans = Map-CircledToken $lead.Groups[1].Value
        if ($ans -ge 1 -and $ans -le 4) {
            return @{ answer = $ans; method = 'leading_circle'; confidence = 'medium' }
        }
    }

    # "정답" U+C815 U+B2F5
    $jd = ([string][char]0xC815) + ([string][char]0xB2F5)
    $explicit = [regex]::Match($text, [regex]::Escape($jd) + '\s*([:=\s])?\s*(\S)')
    if ($explicit.Success) {
        $ans = Map-CircledToken $explicit.Groups[2].Value
        if ($ans -ge 1 -and $ans -le 4) {
            return @{ answer = $ans; method = 'jeongdap'; confidence = 'high' }
        }
    }

    $headLen = [Math]::Min(120, $text.Length)
    $head = $text.Substring(0, $headLen)
    foreach ($ch in $head.ToCharArray()) {
        $code = [int]$ch
        if (($code -ge 0x2460 -and $code -le 0x2463) -or ($code -ge 0x2776 -and $code -le 0x2779)) {
            $ans = Map-CircledToken ([string]$ch)
            if ($ans -ge 1 -and $ans -le 4) {
                return @{ answer = $ans; method = 'first_circle_head'; confidence = 'low' }
            }
        }
    }
    foreach ($ch in $head.ToCharArray()) {
        $code = [int]$ch
        if (($code -ge 0x3260 -and $code -le 0x326F) -or ($code -ge 0x320E -and $code -le 0x3211)) {
            $ans = Map-CircledToken ([string]$ch)
            if ($ans -ge 1 -and $ans -le 4) {
                return @{ answer = $ans; method = 'ocr_hangul_circle'; confidence = 'low' }
            }
        }
    }

    return @{ answer = $null; method = 'unparsed'; confidence = 'none' }
}

function Get-Subject([string]$qPath) {
    $elec = [string]([char]0xC804) + [string]([char]0xAE30)    # jeongi
    $gi2 = [string]([char]0xAE30) + [string]([char]0xAE30)     # gigi
    $iron2 = [string]([char]0xC774) + [string]([char]0xB860)   # iron
    if ($qPath.Contains($elec + $gi2)) { return $elec + $gi2 }
    if ($qPath.Contains($elec + $iron2)) { return $elec + $iron2 }
    return $elec
}

function Get-QNum([string]$qPath) {
    if ($qPath -match 'no(\d+)') { return [int]$Matches[1] }
    return 0
}

Write-Host 'Loading exam_data.json ...'
$exam = Get-Content -LiteralPath (Join-Path $SrcRoot 'exam_data.json') -Encoding UTF8 -Raw | ConvertFrom-Json
Write-Host ("Entries: {0}" -f $exam.Count)

$entries = New-Object System.Collections.Generic.List[object]
$seenQ = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($e in $exam) {
    $qn = [IO.Path]::GetFileName($e.questions)
    if ($seenQ.Add($qn)) { $entries.Add($e) }
}

$qFiles = Get-ChildItem -LiteralPath (Join-Path $SrcRoot 'questions') -Filter '*.jpg'
$aSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
Get-ChildItem -LiteralPath (Join-Path $SrcRoot 'answers') -Filter '*.jpg' | ForEach-Object { [void]$aSet.Add($_.Name) }

$orphanAdded = 0
foreach ($qf in $qFiles) {
    if ($seenQ.Contains($qf.Name)) { continue }
    if ($qf.Name -match '_v\d+|__dup|_dup') { continue }
    $an = $qf.Name -replace '^q_', 'a_'
    if (-not $aSet.Contains($an)) { continue }
    $date = ''
    $examName = ''
    if ($qf.Name -match '_(\d{4}-\d{2}-\d{2})_(.+)_no\d+') {
        $date = $Matches[1]
        $examName = ($Matches[2] -replace '_', ' ')
    }
    $entries.Add([pscustomobject]@{
        questions = "questions/$($qf.Name)"
        answers   = "answers/$an"
        date      = $date
        exam      = $examName
    })
    [void]$seenQ.Add($qf.Name)
    $orphanAdded++
}
Write-Host ("Total unique pairs: {0} (orphans added: {1})" -f $entries.Count, $orphanAdded)

$questions = New-Object System.Collections.Generic.List[object]
$reportItems = New-Object System.Collections.Generic.List[object]
$i = 0
foreach ($e in $entries) {
    $i++
    $srcQ = Join-Path $SrcRoot $e.questions
    $srcA = Join-Path $SrcRoot $e.answers
    if (-not (Test-Path -LiteralPath $srcQ) -or -not (Test-Path -LiteralPath $srcA)) {
        Write-Host "MISSING $i $($e.questions)"
        continue
    }
    $qName = [IO.Path]::GetFileName($e.questions)
    $aName = [IO.Path]::GetFileName($e.answers)
    $dstQ = Join-Path $QDir $qName
    $dstA = Join-Path $ADir $aName
    if (-not (Test-Path -LiteralPath $dstQ)) { Copy-Item -LiteralPath $srcQ -Destination $dstQ -Force }
    if (-not (Test-Path -LiteralPath $dstA)) { Copy-Item -LiteralPath $srcA -Destination $dstA -Force }

    $qNum = Get-QNum $qName
    $subject = Get-Subject $qName
    $source = ("{0} {1} {2}" -f $e.date, $subject, $e.exam).Trim()
    if ([string]::IsNullOrWhiteSpace($source)) {
        $source = '9-' + $subject
    }

    $ocr = ''
    try { $ocr = Ocr-File $dstA } catch { $ocr = '' }
    $parsed = Extract-Answer $ocr $qNum
    $answerIdx = $null
    if ($null -ne $parsed.answer) { $answerIdx = [int]$parsed.answer - 1 }

    $qKey = "img::$qName"
    $item = [ordered]@{
        source     = $source
        q          = $qKey
        choices    = @([string][char]0x2460, [string][char]0x2461, [string][char]0x2462, [string][char]0x2463)
        answer     = $(if ($null -ne $answerIdx) { $answerIdx } else { -1 })
        explain    = ''
        visual     = ''
        caption    = ''
        q_image    = "exam_images/questions/$qName"
        a_image    = "exam_images/answers/$aName"
        image_mode = $true
        q_num      = $qNum
        subject    = $subject
    }
    $questions.Add($item)
    $ocrHead = if ($ocr.Length -gt 160) { $ocr.Substring(0, 160) } else { $ocr }
    $reportItems.Add([ordered]@{
        file       = $qName
        q_num      = $qNum
        answer     = $parsed.answer
        answer_idx = $answerIdx
        method     = $parsed.method
        confidence = $parsed.confidence
        ocr_head   = $ocrHead
    })
    if (($i % 25) -eq 0) { Write-Host ("OCR {0}/{1}" -f $i, $entries.Count) }
}

$parsedOk = @($reportItems | Where-Object { $null -ne $_.answer }).Count
$high = @($reportItems | Where-Object { $_.confidence -eq 'high' }).Count
$med = @($reportItems | Where-Object { $_.confidence -eq 'medium' }).Count
$low = @($reportItems | Where-Object { $_.confidence -eq 'low' }).Count
$none = @($reportItems | Where-Object { $_.confidence -eq 'none' }).Count

$payload = [ordered]@{
    interval_minutes = 3
    questions        = @($questions)
}
$utf8 = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($OutJson, ($payload | ConvertTo-Json -Depth 8), $utf8)
[System.IO.File]::WriteAllText($Report, (@($reportItems) | ConvertTo-Json -Depth 6), $utf8)

Write-Host "Wrote $OutJson ($($questions.Count) questions)"
Write-Host "Parsed: $parsedOk / $($questions.Count) (high=$high med=$med low=$low none=$none)"
Write-Host "Report: $Report"
