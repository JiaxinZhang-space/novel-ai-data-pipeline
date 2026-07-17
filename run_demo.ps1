param(
    [string]$Python = "python",
    [string]$OutputDir = "artifacts"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Push-Location $RepoRoot
try {
    & $Python ".\scripts\run_demo.py" --output-dir $OutputDir
    if ($LASTEXITCODE -ne 0) {
        throw "Demo pipeline failed with exit code $LASTEXITCODE."
    }

    & $Python -m unittest discover -s ".\tests" -v
    if ($LASTEXITCODE -ne 0) {
        throw "Test suite failed with exit code $LASTEXITCODE."
    }

    & $Python ".\scripts\check_public_repo.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Public repository safety check failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
