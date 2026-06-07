#!/usr/bin/env bash
set -euo pipefail


SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ZIP_PATH="${1:-$SCRIPT_DIR/gaussian_surface_project_v0_1.zip}"
INSTALL_ROOT="${2:-$HOME/projects}"
PROJECT_DIR="$INSTALL_ROOT/gaussian_surface_project"
OPEN_SCRIPT="$SCRIPT_DIR/open_gaussian_surface_project.sh"

echo "Installing Boundary Gaussian Surface project"
echo "ZIP file:     $ZIP_PATH"
echo "Install root: $INSTALL_ROOT"
echo

if [[ ! -f "$ZIP_PATH" ]]; then
    echo "ERROR: ZIP file not found:"
    echo "  $ZIP_PATH"
    echo
    echo "Place gaussian_surface_project_v0_1.zip beside this installer,"
    echo "or pass its full WSL path as the first argument."
    exit 1
fi

if [[ ! -f "$OPEN_SCRIPT" ]]; then
    echo "ERROR: Open script not found:"
    echo "  $OPEN_SCRIPT"
    echo
    echo "Place open_gaussian_surface_project.sh beside this installer."
    exit 1
fi

if [[ -d "$PROJECT_DIR" ]]; then
    echo "ERROR: Project folder already exists:"
    echo "  $PROJECT_DIR"
    echo
    echo "Remove or rename that folder before reinstalling."
    exit 1
fi

echo "Checking system packages..."
if ! command -v python3 >/dev/null 2>&1 || \
   ! command -v unzip >/dev/null 2>&1 || \
   ! python3 -m venv --help >/dev/null 2>&1; then
    echo "Installing required Ubuntu packages..."
    sudo apt update
    sudo apt install -y python3 python3-venv python3-pip unzip
fi

mkdir -p "$INSTALL_ROOT"

echo "Extracting project..."
unzip -q "$ZIP_PATH" -d "$INSTALL_ROOT"

cp "$OPEN_SCRIPT" "$PROJECT_DIR/open_gaussian_surface_project.sh"
chmod +x "$PROJECT_DIR/open_gaussian_surface_project.sh"

cd "$PROJECT_DIR"

echo "Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"

echo "Running tests..."
pytest -q

echo
echo "Installation completed successfully."
echo
echo "To open the project later, run:"
echo "  source ~/projects/gaussian_surface_project/open_gaussian_surface_project.sh"
