#!/usr/bin/env sh

# Discord Bot Build Script - Updated for modern dependencies (August 2025)
# Supports Alpine Linux and Debian/Ubuntu systems

# Updated package lists for modern distributions (August 2025)
ALPINE_BUILD_PKGS="--virtual .voice-build-deps build-base libffi-dev libsodium-dev musl-dev"
ALPINE_REQUIRED_PKGS="libffi libsodium opus-dev ffmpeg gcc python3 python3-dev"

DEBIAN_BUILD_PKGS="build-essential libffi-dev libsodium-dev"
DEBIAN_REQUIRED_PKGS="libffi8 libsodium23 libopus-dev ffmpeg gcc python3 python3-dev python3-venv"

LOG_DIR="/var/log/discord_bot"
SYSTEM=$(grep "\bID=\b" /etc/os-release | grep -v "\"" | awk -F '=' '{print $2}')
VENV="venv"

install_TGABot(){
  if [ ! -d "$VENV" ]; then
    echo "Creating Virtual Environment"
    python3 -m venv "$VENV"
  fi

  # shellcheck disable=SC1091 # Don't follow source
  . venv/bin/activate

  # Upgrade pip to latest version
  pip install --upgrade pip
  
  # Install requirements
  pip install -r requirements.txt

  if [ -n "$SUDO_USER" ]; then
    chown -R "$SUDO_USER" "$VENV"
  fi

  # Create the logs directory
  if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    if [ -n "$SUDO_USER" ]; then
      chown -R "$SUDO_USER" "$LOG_DIR"
    fi
  fi
}

install_alpine(){
  apk update

  # shellcheck disable=SC2086 # Intended splitting of ALPINE_BUILD_PKGS
  apk add $ALPINE_BUILD_PKGS
  # shellcheck disable=SC2086 # Intended splitting of ALPINE_REQUIRED_PKGS
  apk add $ALPINE_REQUIRED_PKGS

  # Ensure python/pip are available
  if [ ! -f /usr/bin/python ]; then
    ln -sf python3 /usr/bin/python
  fi

  # Install the Bot
  install_TGABot
  
  # Delete build dependencies to save space
  apk del .voice-build-deps
}

install_debian(){
  apt update
  # shellcheck disable=SC2086 # Intended splitting of DEBIAN_BUILD_PKGS
  apt install -y $DEBIAN_BUILD_PKGS
  # shellcheck disable=SC2086 # Intended splitting of DEBIAN_REQUIRED_PKGS
  apt install -y $DEBIAN_REQUIRED_PKGS
  
  # Ensure python/pip are available
  if [ ! -f /usr/bin/python ]; then
    ln -sf python3 /usr/bin/python
  fi
  
  # Install the Bot
  install_TGABot

  # Clean up build dependencies
  # shellcheck disable=SC2086 # Intended splitting of DEBIAN_BUILD_PKGS
  apt remove -y $DEBIAN_BUILD_PKGS
  apt autoremove -y
}

# Check if running as root
if [ "$(whoami)" != "root" ]; then
  echo "Error: This script needs to be run as root."
  echo "Please run with sudo or as root user."
  exit 1
fi

# Detect system and install accordingly
echo "Detected system: $SYSTEM"

if [ "$SYSTEM" = "alpine" ]; then
  echo "Installing on Alpine Linux..."
  install_alpine
elif [ "$SYSTEM" = "ubuntu" ] || [ "$SYSTEM" = "debian" ]; then
  echo "Installing on Debian/Ubuntu system..."
  install_debian
else
  echo "Warning: Unknown system '$SYSTEM', attempting Debian/Ubuntu installation..."
  install_debian
fi

# Generate config file if it doesn't exist
CONFIG="config.yaml"
if [ ! -f "$CONFIG" ]; then
  if [ -f "defaults.yaml" ]; then
    cp defaults.yaml "$CONFIG"
    echo "Generated default configuration file: $CONFIG"
    if [ -n "$SUDO_USER" ]; then
      chown "$SUDO_USER" "$CONFIG"
    fi
  else
    echo "Warning: defaults.yaml not found, please create $CONFIG manually"
  fi
else
  echo "Configuration file $CONFIG already exists, skipping generation."
fi

echo "Installation completed successfully!"
echo "Virtual environment created in: $VENV"
echo "Log directory created at: $LOG_DIR"
echo ""
echo "To activate the virtual environment, run:"
echo "  source $VENV/bin/activate"
