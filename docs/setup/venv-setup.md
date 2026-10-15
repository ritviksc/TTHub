# Python virtual environment

The backend runs inside a virtual environment named `.venv` at the repo root (`Group_4/.venv`). Everyone should use that name: `scripts/dev.sh` looks for `.venv/bin/python`, and `.gitignore` already excludes `.venv/`.

## Requirements

Python 3.10 or newer, which Django 5.2 needs. Check with:

```bash
python --version      # Windows: py --version
```

## 1. Create the environment

Run this once, from the repo root:

```bash
# Linux/macOS
python3 -m venv .venv

# Windows
py -m venv .venv
```

## 2. Activate it

Activate it in every new terminal before running backend commands.

| Shell | Command |
| --- | --- |
| Linux/macOS (bash, zsh) | `source .venv/bin/activate` |
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| Git Bash on Windows | `source .venv/Scripts/activate` |

When it is active, the prompt starts with `(.venv)`. Type `deactivate` to leave.

If PowerShell says *running scripts is disabled on this system*, allow scripts for the current window only and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3. Install the dependencies

With the environment active:

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
```

`python -m pip` makes sure packages go into `.venv` and not a global Python. Run the install again whenever someone changes `backend/requirements.txt`.

## Troubleshooting

- **`ModuleNotFoundError: No module named 'django'`**: the environment is not active in this terminal, or the install step was skipped.
- **The environment stops working** after moving the repo folder or upgrading Python: delete `.venv` (`rm -rf .venv`, or `Remove-Item -Recurse -Force .venv` in PowerShell) and repeat steps 1 to 3.
- **VS Code uses the wrong Python**: run *Python: Select Interpreter* from the command palette and pick the one in `.venv`.

## Next steps

Continue with the backend setup in the [README](../../README.md), then [Celery setup](celery-setup.md) for background tasks.
