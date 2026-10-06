param(
    [string]$Presentation = "artifacts/pilot/Ordinance_Two_Model_Initial_Results.pptx",
    [switch]$Previews
)
$ErrorActionPreference = "Stop"
$path = (Resolve-Path $Presentation).Path
$folder = Split-Path $path
$app = New-Object -ComObject PowerPoint.Application
$hadOpenPresentations = $app.Presentations.Count -gt 0
$deck = $null
try {
    # Read-only, no visible editing window. Do not change any user's open deck.
    $deck = $app.Presentations.Open($path, -1, 0, 0)
    $pdf = [System.IO.Path]::ChangeExtension($path, ".pdf")
    # ppSaveAsPDF = 32; SaveAs avoids COM optional-argument marshalling issues.
    $deck.SaveAs($pdf, 32)
    Write-Output "PDF exported: $pdf"
    if ($Previews) {
        $previewPath = Join-Path $folder "previews"
        New-Item -ItemType Directory -Force -Path $previewPath | Out-Null
        foreach ($slide in $deck.Slides) {
            $name = "slide_{0:D2}.png" -f $slide.SlideIndex
            $slide.Export((Join-Path $previewPath $name), "PNG", 1600, 900)
        }
        Write-Output "Rendered $($deck.Slides.Count) slides: $previewPath"
    }
} finally {
    if ($null -ne $deck) { $deck.Close() }
    if (-not $hadOpenPresentations) { $app.Quit() }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
