# Repository Maintenance

This document captures routine cleanup and hygiene steps to keep the repo tidy and free of runtime artifacts.

## One-time: Ignore common artifacts
Already configured in `.gitignore`:
- logs/ and *.log
- __pycache__/ and *.pyc
- virtualenv folders (venv/, env/, ENV/)
- test caches and coverage (.pytest_cache/, .mypy_cache/, .coverage*, htmlcov/)

## Clean working tree (Windows PowerShell)
```powershell
# Remove Python caches
Get-ChildItem -Recurse -Directory -Force -Filter __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Include *.pyc,*.pyo | Remove-Item -Force -ErrorAction SilentlyContinue

# Remove logs created locally
if (Test-Path .\bot.log) { Remove-Item .\bot.log -Force }
if (Test-Path .\logs) { Get-ChildItem .\logs -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue }

# Optional: remove coverage artifacts
if (Test-Path .\.coverage) { Remove-Item .\.coverage -Force }
if (Test-Path .\htmlcov) { Remove-Item .\htmlcov -Recurse -Force }
```

## Clean working tree (Linux/macOS)
```bash
# Remove Python caches
find . -type d -name '__pycache__' -prune -exec rm -rf {} +
find . -type f -name '*.py[co]' -delete

# Remove logs
rm -f bot.log
rm -rf logs/*

# Optional: coverage artifacts
rm -f .coverage .coverage.*
rm -rf htmlcov/
```

## Deployment files
Service unit files now live under `deploy/`:
- `deploy/anti-ad-bot.service`
- `deploy/anti-ad-portal.service`

Refer to `deploy/README.md` for installation instructions.
