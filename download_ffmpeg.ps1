# PowerShell script to download and setup FFmpeg automatically

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FFmpeg Auto-Installer for Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ffmpegDir = "C:\ffmpeg"
$ffmpegBin = "$ffmpegDir\bin"
$downloadUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$zipFile = "$env:TEMP\ffmpeg.zip"

# Check if already installed
if (Test-Path "$ffmpegBin\ffmpeg.exe") {
    Write-Host "✅ FFmpeg is already installed at: $ffmpegBin" -ForegroundColor Green
    Write-Host ""
    & "$ffmpegBin\ffmpeg.exe" -version | Select-Object -First 1
    exit 0
}

Write-Host "📥 Downloading FFmpeg..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..."
Write-Host ""

try {
    # Download FFmpeg
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipFile -UseBasicParsing
    Write-Host "✅ Download complete!" -ForegroundColor Green
    Write-Host ""
    
    # Extract
    Write-Host "📦 Extracting files..." -ForegroundColor Yellow
    Expand-Archive -Path $zipFile -DestinationPath $env:TEMP -Force
    
    # Find the extracted folder
    $extractedFolder = Get-ChildItem "$env:TEMP\ffmpeg-*-essentials_build" | Select-Object -First 1
    
    if ($extractedFolder) {
        # Move to C:\ffmpeg
        Write-Host "📂 Installing to $ffmpegDir..." -ForegroundColor Yellow
        if (Test-Path $ffmpegDir) {
            Remove-Item $ffmpegDir -Recurse -Force
        }
        Move-Item $extractedFolder.FullName $ffmpegDir
        Write-Host "✅ Installation complete!" -ForegroundColor Green
        Write-Host ""
        
        # Add to PATH
        Write-Host "🔧 Adding to system PATH..." -ForegroundColor Yellow
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentPath -notlike "*$ffmpegBin*") {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$ffmpegBin", "User")
            $env:Path += ";$ffmpegBin"
            Write-Host "✅ Added to PATH!" -ForegroundColor Green
        } else {
            Write-Host "✅ Already in PATH" -ForegroundColor Green
        }
        Write-Host ""
        
        # Test
        Write-Host "🧪 Testing FFmpeg..." -ForegroundColor Yellow
        & "$ffmpegBin\ffmpeg.exe" -version | Select-Object -First 1
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  ✅ FFmpeg installed successfully!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "You can now run: python bot.py" -ForegroundColor Cyan
        Write-Host ""
        
    } else {
        throw "Could not find extracted folder"
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install FFmpeg manually:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Yellow
    Write-Host "2. Extract to C:\ffmpeg" -ForegroundColor Yellow
    Write-Host "3. Add C:\ffmpeg\bin to your PATH" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "See install_ffmpeg.md for detailed instructions" -ForegroundColor Yellow
} finally {
    # Cleanup
    if (Test-Path $zipFile) {
        Remove-Item $zipFile -Force
    }
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
