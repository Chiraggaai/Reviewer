# Start Reviewer API: fixes "No module named 'app'" when the shell cwd is not this folder.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
uvicorn app.main:app --reload --port 8001 @args
