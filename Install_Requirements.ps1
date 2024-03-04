# Check and install Chocolatey if not present
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Set-ExecutionPolicy Bypass -Scope Process -Force;
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'));
}

# Update Chocolatey
choco upgrade chocolatey -y

# Install Python 3
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    echo "Installing Python 3..."
    choco install python -y
} else {
    echo "Python 3 is already installed."
}

# Install ffmpeg
if (!(Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    echo "Installing ffmpeg..."
    choco install ffmpeg -y
} else {
    echo "ffmpeg is already installed."
}

# Install yt-dlp
if (!(Get-Command yt-dlp -ErrorAction SilentlyContinue)) {
    echo "Installing yt-dlp..."
    choco install yt-dlp -y
} else {
    echo "yt-dlp is already installed."
}

echo "All prerequisite components are installed."
