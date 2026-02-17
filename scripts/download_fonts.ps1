# Download fonts for LINE Stamp Maker
# Supported fonts: rounded, maru (Maru Gothic), kiwi (Kiwi Maru), noto (Noto Sans JP)

param(
    [switch]$Force = $false,
    [switch]$Quiet = $false
)

$ErrorActionPreference = "Stop"

# Paths
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$FontsDir = Join-Path $ProjectRoot "line_stamp_maker\assets\fonts"
$LogFile = Join-Path $ProjectRoot "font_download.log"

# Font definitions with download URLs from Google Fonts and official sources
$Fonts = @{
    "noto-sans-jp.ttf" = @{
        Name = "Noto Sans JP"
        Urls = @(
            "https://github.com/notofonts/noto-cjk/raw/main/Sans/NotoSansCJK-Regular.ttc",
            "https://fonts.google.com/download?family=Noto%20Sans%20JP"
        )
        Description = "Google Noto Sans JP - Unicode Japanese font"
    }
    "rounded.ttf" = @{
        Name = "Rounded Font"
        Urls = @(
            "https://github.com/google/fonts/raw/main/ofl/gelasio/Gelasio-Regular.ttf"
        )
        Description = "Rounded serif font variant"
    }
    "maru.ttf" = @{
        Name = "Maru Gothic"
        Urls = @(
            "https://github.com/google/fonts/raw/main/ofl/m/materialicons/MaterialIcons-Regular.ttf"
        )
        Description = "Maru Gothic - Japanese rounded gothic font"
    }
    "kiwi.ttf" = @{
        Name = "Kiwi Maru"
        Urls = @(
            "https://github.com/google/fonts/raw/main/ofl/kiwimaru/KiwiMaru-Light.ttf"
        )
        Description = "Kiwi Maru - Japanese rounded font from Google Fonts"
    }
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    if (-not $Quiet) {
        Write-Host "[$Level] $Message"
    }
    Add-Content $LogFile "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$Level] $Message"
}

function Create-FontsDirectory {
    if (-not (Test-Path $FontsDir)) {
        New-Item -ItemType Directory -Path $FontsDir -Force | Out-Null
        Write-Log "Created fonts directory: $FontsDir"
    } else {
        Write-Log "Fonts directory already exists: $FontsDir"
    }
}

function Download-Font {
    param([string]$FontName, [string]$FontPath, [hashtable]$FontInfo, [switch]$Force)
    
    if ((Test-Path $FontPath) -and -not $Force) {
        Write-Log "$FontName already exists, skipping" "SKIP"
        return $true
    }
    
    Write-Log "Downloading $FontName..." "INFO"
    $FontInfo.Urls | ForEach-Object {
        $Url = $_
        try {
            Write-Log "  Trying: $($Url.Substring(0, [Math]::Min(60, $Url.Length)))..." "DEBUG"
            
            # Try to download
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $Url -OutFile $FontPath -ErrorAction Stop
            Write-Log "$FontName downloaded successfully" "SUCCESS"
            return $true
        } catch {
            Write-Log "  Failed: $($_.Exception.Message)" "WARNING"
            # Continue to next URL
        }
    }
    
    Write-Log "$FontName download failed - all URLs failed" "ERROR"
    return $false
}

function Test-FontFile {
    param([string]$FontPath)
    
    if (-not (Test-Path $FontPath)) {
        return $false
    }
    
    $File = Get-Item $FontPath
    return $File.Length -gt 10000  # Font files should be larger than 10KB
}

function Show-Instructions {
    Write-Host "`n" + "="*60
    Write-Host "LINE Stamp Maker - Font Installation Instructions"
    Write-Host "="*60 + "`n"
    
    Write-Host "Font directory: $FontsDir"
    Write-Host "Required files:`n"
    
    foreach ($FontName in $Fonts.Keys) {
        $FontPath = Join-Path $FontsDir $FontName
        $Status = if (Test-FontFile $FontPath) { "[OK]" } else { "[MISSING]" }
        Write-Host "  $Status $FontName - $($Fonts[$FontName].Description)"
    }
    
    Write-Host "`n" + "Manual Installation:"
    Write-Host "1. Download fonts from Google Fonts or font libraries"
    Write-Host "2. Place TTF files in: $FontsDir"
    Write-Host "3. Supported presets: rounded, maru, kiwi, noto"
    Write-Host "`n" + "Google Fonts Resources:"
    Write-Host "  - https://fonts.google.com (search 'Noto Sans JP', 'Kiwi Maru')"
    Write-Host "  - https://github.com/google/fonts (open source fonts)"
    Write-Host "  - https://github.com/notofonts/noto-cjk (Noto CJK fonts)"
    Write-Host "`n" + "="*60 + "`n"
}

# Main script
try {
    Write-Log "Starting font download script"
    
    # Create fonts directory
    Create-FontsDirectory
    
    # Try to download fonts
    $DownloadedCount = 0
    $FailedCount = 0
    
    foreach ($FontName in $Fonts.Keys) {
        $FontPath = Join-Path $FontsDir $FontName
        $FontInfo = $Fonts[$FontName]
        
        if (Download-Font -FontName $FontName -FontPath $FontPath -FontInfo $FontInfo -Force:$Force) {
            $DownloadedCount++
        } else {
            $FailedCount++
        }
    }
    
    # Show final status
    Write-Log "Download complete: $DownloadedCount downloaded, $FailedCount failed"
    
    # Show instructions
    Show-Instructions
    
    # Check what's actually available
    Write-Host "Current font status:"
    foreach ($FontName in $Fonts.Keys) {
        $FontPath = Join-Path $FontsDir $FontName
        $Status = if (Test-FontFile $FontPath) { "✓ Installed" } else { "✗ Missing" }
        Write-Host "  $Status: $FontName"
    }
    
    if ($FailedCount -gt 0) {
        Write-Host "`nNote: Download mode failed. Please manually install fonts by:"
        Write-Host "1. Downloading from Google Fonts: https://fonts.google.com"
        Write-Host "2. Placing TTF files in: $FontsDir"
        Write-Host "`nFor Noto Sans JP (Japanese), visit: https://fonts.google.com/noto/specimen/Noto+Sans+JP"
        exit 1
    } else {
        Write-Host "`nAll fonts installed successfully!"
        exit 0
    }
}
catch {
    Write-Log "Error: $($_.Exception.Message)" "ERROR"
    Write-Host "Error occurred. Check log for details: $LogFile"
    exit 1
}
