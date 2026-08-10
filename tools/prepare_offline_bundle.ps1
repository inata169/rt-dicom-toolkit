<#
.SYNOPSIS
Build a Windows x64 offline-installation ZIP for RT DICOM Toolkit.

.DESCRIPTION
Run on an internet-connected Windows PC. The script downloads the official
CPython 3.12.10 x64 installer and Windows wheels, builds the application wheel,
creates a SHA-256 inventory, and writes the USB-transfer ZIP under dist/.
#>

[CmdletBinding()]
param(
    [Parameter()]
    [string]$PythonExe,

    [Parameter()]
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$PythonVersion = "3.12.10"
$PythonInstallerName = "python-$PythonVersion-amd64.exe"
$PythonInstallerUrl = "https://www.python.org/ftp/python/$PythonVersion/$PythonInstallerName"
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$LockPath = Join-Path $RepoRoot "requirements\offline-win64-py312.txt"
$DistRoot = Join-Path $RepoRoot "dist"

function Resolve-ProducerPython {
    $Candidates = @()
    if ($PythonExe) {
        $Candidates += [pscustomobject]@{ Executable = $PythonExe; Prefix = @() }
    }
    else {
        $Py = Get-Command "py.exe" -ErrorAction SilentlyContinue
        if ($null -ne $Py) {
            $Candidates += [pscustomobject]@{ Executable = $Py.Source; Prefix = @("-3.12") }
        }
        $Python = Get-Command "python.exe" -ErrorAction SilentlyContinue
        if ($null -ne $Python) {
            $Candidates += [pscustomobject]@{ Executable = $Python.Source; Prefix = @() }
        }
    }

    foreach ($Candidate in $Candidates) {
        $OldPythonHome = $env:PYTHONHOME
        $OldPythonPath = $env:PYTHONPATH
        $Probe = $null
        $ProbeExitCode = -1
        try {
            $env:PYTHONHOME = $null
            $env:PYTHONPATH = $null
            try {
                $Probe = & $Candidate.Executable @($Candidate.Prefix) -I -c "import pip,setuptools,struct,sys,wheel; print('ok' if sys.version_info[:2] == (3,12) and struct.calcsize('P')*8 == 64 else 'unsupported')" 2>$null
                $ProbeExitCode = $LASTEXITCODE
            }
            catch {
                $ProbeExitCode = -1
            }
        }
        finally {
            $env:PYTHONHOME = $OldPythonHome
            $env:PYTHONPATH = $OldPythonPath
        }
        if ($ProbeExitCode -eq 0 -and ($Probe | Select-Object -Last 1) -eq "ok") {
            return $Candidate
        }
    }
    throw "CPython 3.12 x64 with pip, setuptools, and wheel is required to prepare the bundle."
}

function Invoke-ProducerPython {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter()]
        [switch]$Capture
    )

    $OldPythonHome = $env:PYTHONHOME
    $OldPythonPath = $env:PYTHONPATH
    $Output = $null
    try {
        $env:PYTHONHOME = $null
        $env:PYTHONPATH = $null
        if ($Capture) {
            $Output = & $script:ProducerPython.Executable @($script:ProducerPython.Prefix) -I @Arguments
        }
        else {
            & $script:ProducerPython.Executable @($script:ProducerPython.Prefix) -I @Arguments
        }
        $ExitCode = $LASTEXITCODE
    }
    finally {
        $env:PYTHONHOME = $OldPythonHome
        $env:PYTHONPATH = $OldPythonPath
    }
    if ($ExitCode -ne 0) {
        throw "Producer Python command failed with exit code $ExitCode."
    }
    if ($Capture) {
        return $Output
    }
}

function Copy-RequiredFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Source,

        [Parameter(Mandatory = $true)]
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "Required file is missing: $Source"
    }
    $Parent = Split-Path -Parent $Destination
    if (-not (Test-Path -LiteralPath $Parent)) {
        New-Item -ItemType Directory -Path $Parent -Force | Out-Null
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

if ($env:OS -ne "Windows_NT") {
    throw "Bundle preparation is supported only on Windows."
}
if (-not (Test-Path -LiteralPath $LockPath -PathType Leaf)) {
    throw "Offline dependency lock is missing: $LockPath"
}

$script:ProducerPython = Resolve-ProducerPython
$ProjectVersion = (Invoke-ProducerPython -Capture -Arguments @((Join-Path $RepoRoot "setup.py"), "--version") | Select-Object -Last 1).Trim()
if ($ProjectVersion -notmatch '^\d+\.\d+\.\d+$') {
    throw "Unexpected project version: $ProjectVersion"
}

New-Item -ItemType Directory -Path $DistRoot -Force | Out-Null
$OutputZip = Join-Path $DistRoot "rt-dicom-toolkit-offline-win64-$ProjectVersion.zip"
if (Test-Path -LiteralPath $OutputZip) {
    if (-not $Force) {
        throw "Output ZIP already exists: $OutputZip. Use -Force to replace it."
    }
    Remove-Item -LiteralPath $OutputZip -Force
}

$WorkRoot = Join-Path $DistRoot (".offline-bundle-work-" + [Guid]::NewGuid().ToString("N"))
$BundleRoot = Join-Path $WorkRoot "bundle"
$Wheelhouse = Join-Path $BundleRoot "wheelhouse"
$PythonDirectory = Join-Path $BundleRoot "python"
$PythonInstaller = Join-Path $PythonDirectory $PythonInstallerName

try {
    New-Item -ItemType Directory -Path $Wheelhouse -Force | Out-Null
    New-Item -ItemType Directory -Path $PythonDirectory -Force | Out-Null

    Write-Host "Downloading official CPython $PythonVersion x64 installer..."
    Invoke-WebRequest -UseBasicParsing -Uri $PythonInstallerUrl -OutFile $PythonInstaller
    $Signature = Get-AuthenticodeSignature -LiteralPath $PythonInstaller
    if ($Signature.Status -ne [System.Management.Automation.SignatureStatus]::Valid) {
        throw "Python installer Authenticode validation failed: $($Signature.Status)"
    }
    if ($null -eq $Signature.SignerCertificate -or [string]$Signature.SignerCertificate.Subject -notlike "*Python Software Foundation*") {
        throw "Python installer signer is not the Python Software Foundation."
    }
    Write-Host "Python installer signature: Valid"

    Write-Host "Downloading pinned CPython 3.12 Windows x64 wheels..."
    $OldDownloadConfig = $env:PIP_CONFIG_FILE
    try {
        $env:PIP_CONFIG_FILE = "nul"
        Invoke-ProducerPython -Arguments @(
            "-m", "pip", "--isolated", "download",
            "--disable-pip-version-check",
            "--index-url", "https://pypi.org/simple",
            "--no-cache-dir",
            "--dest", $Wheelhouse,
            "--only-binary=:all:",
            "--no-deps",
            "--platform", "win_amd64",
            "--python-version", "3.12",
            "--implementation", "cp",
            "--abi", "cp312",
            "--requirement", $LockPath
        )
    }
    finally {
        $env:PIP_CONFIG_FILE = $OldDownloadConfig
    }

    $NonWheels = @(Get-ChildItem -LiteralPath $Wheelhouse -File | Where-Object { $_.Extension -ne ".whl" })
    if ($NonWheels.Count -ne 0) {
        throw "A non-wheel dependency was downloaded: $($NonWheels[0].Name)"
    }

    Write-Host "Building RT DICOM Toolkit wheel without network access..."
    $OldNoIndex = $env:PIP_NO_INDEX
    $OldConfig = $env:PIP_CONFIG_FILE
    try {
        $env:PIP_NO_INDEX = "1"
        $env:PIP_CONFIG_FILE = "nul"
        Invoke-ProducerPython -Arguments @(
            "-m", "pip", "wheel",
            "--disable-pip-version-check",
            "--no-index",
            "--no-deps",
            "--no-build-isolation",
            "--wheel-dir", $Wheelhouse,
            $RepoRoot
        )
    }
    finally {
        $env:PIP_NO_INDEX = $OldNoIndex
        $env:PIP_CONFIG_FILE = $OldConfig
    }

    $ApplicationWheels = @(Get-ChildItem -LiteralPath $Wheelhouse -Filter "rt_dicom_toolkit-$ProjectVersion-*.whl" -File)
    if ($ApplicationWheels.Count -ne 1) {
        throw "Expected exactly one application wheel, found $($ApplicationWheels.Count)."
    }

    $InstallerTemplatePath = Join-Path $RepoRoot "offline\install_offline.bat"
    $InstallerDestination = Join-Path $BundleRoot "install_offline.bat"
    $VersionToken = "__RTDT_PROJECT_VERSION__"
    $InstallerText = [System.IO.File]::ReadAllText($InstallerTemplatePath)
    if (($InstallerText.Split(@($VersionToken), [System.StringSplitOptions]::None).Count - 1) -ne 1) {
        throw "Offline installer must contain exactly one project-version token."
    }
    $InstallerText = $InstallerText.Replace($VersionToken, $ProjectVersion)
    [System.IO.File]::WriteAllText($InstallerDestination, $InstallerText, [System.Text.UTF8Encoding]::new($false))
    Copy-RequiredFile (Join-Path $RepoRoot "offline\start_rt_dicom_toolkit.bat") (Join-Path $BundleRoot "start_rt_dicom_toolkit.bat")
    Copy-RequiredFile (Join-Path $RepoRoot "offline\smoke_test.bat") (Join-Path $BundleRoot "smoke_test.bat")
    Copy-RequiredFile (Join-Path $RepoRoot "tools\offline_smoke_test.py") (Join-Path $BundleRoot "tools\offline_smoke_test.py")
    Copy-RequiredFile (Join-Path $RepoRoot "docs\windows_offline_installation.md") (Join-Path $BundleRoot "docs\windows_offline_installation.md")
    Copy-RequiredFile $LockPath (Join-Path $BundleRoot "requirements\offline-win64-py312.txt")

    $SourceRoot = Join-Path $BundleRoot "source"
    foreach ($Name in @("setup.py", "README.md", "LICENSE")) {
        Copy-RequiredFile (Join-Path $RepoRoot $Name) (Join-Path $SourceRoot $Name)
    }
    $PackageRoot = Join-Path $RepoRoot "rt_dicom_toolkit"
    $SourceFiles = Get-ChildItem -LiteralPath $PackageRoot -Recurse -File | Where-Object {
        $_.Extension -eq ".py" -or $_.Name -eq "requirements.txt"
    }
    foreach ($File in $SourceFiles) {
        $Relative = $File.FullName.Substring($RepoRoot.Length).TrimStart('\')
        Copy-RequiredFile $File.FullName (Join-Path $SourceRoot $Relative)
    }

    $Commit = "unavailable"
    $Git = Get-Command "git.exe" -ErrorAction SilentlyContinue
    if ($null -ne $Git) {
        $CommitOutput = & $Git.Source -C $RepoRoot rev-parse HEAD 2>$null
        if ($LASTEXITCODE -eq 0) {
            $Commit = ($CommitOutput | Select-Object -Last 1).Trim()
        }
    }
    @(
        "project=rt-dicom-toolkit",
        "version=$ProjectVersion",
        "target_python=$PythonVersion",
        "target_platform=Windows x64",
        "source_commit=$Commit",
        "created_utc=$([DateTime]::UtcNow.ToString('o'))"
    ) | Set-Content -LiteralPath (Join-Path $BundleRoot "BUILD-INFO.txt") -Encoding UTF8

    $ChecksumPath = Join-Path $BundleRoot "SHA256SUMS.txt"
    $PayloadFiles = Get-ChildItem -LiteralPath $BundleRoot -Recurse -File | Where-Object {
        $_.FullName -ne $ChecksumPath
    } | Sort-Object FullName
    $ChecksumLines = foreach ($File in $PayloadFiles) {
        $Relative = $File.FullName.Substring($BundleRoot.Length).TrimStart('\').Replace('\', '/')
        $Hash = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$Hash *$Relative"
    }
    $ChecksumLines | Set-Content -LiteralPath $ChecksumPath -Encoding UTF8

    Write-Host "Creating offline ZIP..."
    Compress-Archive -Path (Join-Path $BundleRoot "*") -DestinationPath $OutputZip -CompressionLevel Optimal
    $ZipHash = (Get-FileHash -LiteralPath $OutputZip -Algorithm SHA256).Hash.ToLowerInvariant()
    Write-Host "Offline bundle created: $OutputZip"
    Write-Host "ZIP SHA-256: $ZipHash"
    Write-Host "Payload files: $($PayloadFiles.Count); wheels: $((Get-ChildItem -LiteralPath $Wheelhouse -Filter '*.whl' -File).Count)"
}
finally {
    if (Test-Path -LiteralPath $WorkRoot) {
        $ResolvedWork = [System.IO.Path]::GetFullPath($WorkRoot)
        $ExpectedPrefix = [System.IO.Path]::GetFullPath($DistRoot).TrimEnd('\') + '\'
        if (-not $ResolvedWork.StartsWith($ExpectedPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to clean work directory outside dist: $ResolvedWork"
        }
        Remove-Item -LiteralPath $ResolvedWork -Recurse -Force
    }
}
