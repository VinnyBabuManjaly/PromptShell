#!/usr/bin/env bash
# PromptShell — one-line installer
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/VinnyBabuManjaly/PromptShell/main/install.sh | bash
#
# What this does:
#   1. Installs system dependencies (portaudio, clipboard tools, libnotify)
#   2. Installs uv (if not present)
#   3. Installs Python 3.11 via uv (if no compatible version found)
#   4. Installs prompt-shell as a uv tool (isolated from the system Python)
#   5. Runs `prompt-shell init`  — creates ~/.prompt-shell/config.yaml
#   6. Runs `prompt-shell install-hook` — adds shell hook to your rc file

set -euo pipefail

PYPI_PACKAGE="prompt-shell"
GIT_REPO="https://github.com/VinnyBabuManjaly/PromptShell.git"

# ── Terminal colours (graceful no-op when piped or not a tty) ─────────────────
if [ -t 1 ] && command -v tput &>/dev/null; then
  BOLD=$(tput bold); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
  RED=$(tput setaf 1); CYAN=$(tput setaf 6); RESET=$(tput sgr0)
else
  BOLD=""; GREEN=""; YELLOW=""; RED=""; CYAN=""; RESET=""
fi

step() { echo ""; echo "${BOLD}${GREEN}==>${RESET} ${BOLD}$*${RESET}"; }
note() { echo "    ${CYAN}$*${RESET}"; }
warn() { echo "    ${YELLOW}warning:${RESET} $*"; }
die()  { echo "${BOLD}${RED}error:${RESET} $*" >&2; exit 1; }

# ── Detect OS ─────────────────────────────────────────────────────────────────
OS=$(uname -s)
ARCH=$(uname -m)

case "$OS" in
  Darwin) PLATFORM="macos" ;;
  Linux)  PLATFORM="linux" ;;
  *) die "Unsupported OS: $OS. PromptShell supports macOS and Linux." ;;
esac

echo ""
echo "${BOLD}Installing PromptShell${RESET} on $PLATFORM ($ARCH)"
echo "────────────────────────────────────────"

# ── 1. System dependencies ────────────────────────────────────────────────────

install_macos_deps() {
  if ! command -v brew &>/dev/null; then
    step "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # Bring brew into PATH on Apple Silicon
    if [ -f /opt/homebrew/bin/brew ]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
  fi

  step "Installing system dependencies via Homebrew..."
  # portaudio: required by sounddevice for microphone capture
  if brew list portaudio &>/dev/null 2>&1; then
    note "portaudio already installed"
  else
    brew install portaudio
  fi
}

install_linux_deps() {
  # Detect package manager
  if command -v apt-get &>/dev/null; then
    step "Installing system dependencies (apt)..."
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends \
      libportaudio2 portaudio19-dev \
      python3-dev build-essential \
      libnotify-bin \
      xclip

    # wl-clipboard for Wayland (non-fatal if unavailable)
    sudo apt-get install -y --no-install-recommends wl-clipboard 2>/dev/null || true

  elif command -v dnf &>/dev/null; then
    step "Installing system dependencies (dnf)..."
    sudo dnf install -y \
      portaudio portaudio-devel \
      python3-devel gcc \
      libnotify \
      xclip

  elif command -v pacman &>/dev/null; then
    step "Installing system dependencies (pacman)..."
    sudo pacman -S --noconfirm \
      portaudio \
      python \
      libnotify \
      xclip \
      wl-clipboard

  elif command -v zypper &>/dev/null; then
    step "Installing system dependencies (zypper)..."
    sudo zypper install -y \
      portaudio-devel \
      python3-devel gcc \
      libnotify-tools \
      xclip

  else
    warn "No recognised package manager (apt/dnf/pacman/zypper)."
    warn "Install these manually, then re-run:"
    warn "  libportaudio2 / portaudio-devel"
    warn "  xclip or wl-clipboard"
    warn "  libnotify / libnotify-bin"
  fi
}

case "$PLATFORM" in
  macos) install_macos_deps ;;
  linux) install_linux_deps ;;
esac

# ── 2. Install uv ─────────────────────────────────────────────────────────────
step "Checking uv..."

if command -v uv &>/dev/null; then
  note "uv $(uv --version) already installed"
else
  note "uv not found — installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Bring uv into PATH for the remainder of this script
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

  if ! command -v uv &>/dev/null; then
    die "uv installation failed. Install manually: https://docs.astral.sh/uv/getting-started/installation/"
  fi
  note "uv $(uv --version) installed"
fi

# ── 3. Python 3.11+ ───────────────────────────────────────────────────────────
step "Checking Python..."

if uv python find "3.11" &>/dev/null 2>&1; then
  note "Python 3.11+ already available"
else
  note "Installing Python 3.11 via uv..."
  uv python install 3.11
fi

# ── 4. Install prompt-shell ───────────────────────────────────────────────────
step "Installing prompt-shell..."

# Upgrade if already installed, otherwise fresh install.
# Try PyPI first; fall back to git main if the package isn't published yet.
if uv tool install "$PYPI_PACKAGE" --upgrade 2>/dev/null; then
  note "Installed from PyPI"
else
  warn "PyPI package not found — installing from GitHub source..."
  uv tool install "git+$GIT_REPO" --upgrade || \
    die "Installation failed. Check your network connection and try again."
  note "Installed from GitHub"
fi

# Ensure the uv tool bin directory is on PATH for the rest of this script
UV_TOOL_BIN=$(uv tool bin 2>/dev/null || echo "$HOME/.local/bin")
export PATH="$UV_TOOL_BIN:$PATH"

command -v prompt-shell &>/dev/null || \
  die "prompt-shell installed but binary not in PATH. Add '$UV_TOOL_BIN' to your PATH and retry."

# ── 5. Initialise config ──────────────────────────────────────────────────────
step "Initialising config (~/.prompt-shell/config.yaml)..."
prompt-shell init

# ── 6. Install shell hook ─────────────────────────────────────────────────────
step "Installing shell hook..."
prompt-shell install-hook

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────"
echo "${BOLD}${GREEN}✓  PromptShell installed successfully!${RESET}"
echo "────────────────────────────────────────"
echo ""
echo "${BOLD}PATH — add this to your shell rc file if prompt-shell is not found:${RESET}"
note "export PATH=\"$UV_TOOL_BIN:\$PATH\""
echo ""
echo "${BOLD}Reload your shell (or open a new terminal):${RESET}"
if [ -n "${ZSH_VERSION:-}" ]; then
  note "source ~/.zshrc"
elif [ -n "${FISH_VERSION:-}" ]; then
  note "source ~/.config/fish/config.fish"
else
  note "source ~/.bashrc"
fi
echo ""
echo "${BOLD}Quick start:${RESET}"
echo ""
echo "  ${BOLD}1. Get a free Gemini API key${RESET} → https://aistudio.google.com/"
note "export GEMINI_API_KEY=your-key-here"
echo ""
echo "  ${BOLD}2. Test with a text prompt (no voice, no daemon needed):${RESET}"
note "prompt-shell enhance \"fix the build error\""
echo ""
echo "  ${BOLD}3. Start the daemon (global hotkeys — Ctrl+Shift+P to trigger):${RESET}"
note "prompt-shell start"
echo ""
echo "  ${BOLD}Offline / no-cloud mode${RESET} — works without a Gemini key:"
if [ "$PLATFORM" = "macos" ]; then
  note "brew install ollama && ollama pull llama3.2:8b"
else
  note "# Install Ollama: https://ollama.com/download"
  note "ollama pull llama3.2:8b"
fi
note "# Then edit ~/.prompt-shell/config.yaml: set  provider: ollama"
echo ""
echo "  ${BOLD}Full docs:${RESET} https://github.com/VinnyBabuManjaly/PromptShell"
echo ""
