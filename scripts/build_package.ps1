Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

python run_council.py --mode mock_test --idea-file examples\project_idea.txt --output outputs\demo_run
python final_check.py
python create_submission_package.py
