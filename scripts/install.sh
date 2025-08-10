#!/bin/bash
# This script installs and setups the necessary environment for the project.

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Error: Access denied. Please, run this script with sudo." >&2
  exit 1
fi


# Output colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Pretty print function
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}


# Install necessary packages
print_status "Installing necessary packages..."
apt update
apt install -y python3 docker docker-compose git maven


# Define variables and paths
PROJECT_DIR=$(pwd)
SERVICE_NAME="autofuzz"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PYTHON_EXEC="${PROJECT_DIR}/venv/bin/python"
MAIN_SCRIPT="${PROJECT_DIR}/src/main.py"

# Set Virtual Environment
print_status "Setting up Python virtual environment..."
print_status "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists, skipping creation"
fi
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
$PYTHON_EXEC -m pip install --upgrade pip
$PYTHON_EXEC -m pip install -r requirements.txt
print_success "Python dependencies installed successfully."


# Generate java-analyzer package
print_status "Generating java-analyzer package..."
cd java-analyzer
mvn clean package -DskipTests
cd ..

# Install and setup Vexgen
# Verify if docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose not installed. Please install Docker Compose first."
    exit 1
fi

## Before this step, it is necessary to create a vexgen's .env file by modifying the template.env file.
## The only changes needed are the values for the variables: GIT_GRAPHQL_API_KEY and NVD_API_KEY
if [ ! -d "vexgen" ]; then
    print_status "Installing Vexgen..."
    git clone git@github.com:GermanMT/vexgen.git
    rm -rf vexgen/.git
    rm -rf vexgen/.github
    print_success "Vexgen cloned successfully."
    cd vexgen
    # Setup .env file
    print_status "Setting up .env file..."
    cp template.env .env
    
    # Prompt for API keys
    echo "Please provide the following API keys (if a change of key is needed, modify vexgen/.env file):"
    read -p "Enter your GitHub GraphQL API key: " git_api_key
    read -p "Enter your NVD API key: " nvd_api_key
    
    # Update .env file with the provided API keys
    sed -i "s/GIT_GRAPHQL_API_KEY='add_your_api_key'/GITHUB_GRAPHQL_API_KEY='$git_api_key'/" .env
    sed -i "s/NVD_API_KEY='add_your_api_key'/NVD_API_KEY='$nvd_api_key'/" .env
    
    print_success ".env file configured successfully."
    cd ..
else
    print_warning "Vexgen directory already exists, skipping clone."
fi
# Add pymongo dependency to requirements.txt
echo -e "\npymongo==4.7.0" >> vexgen/backend/requirements.txt 
#cd vexgen
#docker compose up -d --build
#d ..

# Create systemd service file
print_status "Creating systemd service file..."
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Autofuzz - Automated Fuzz Testing tool to detect vulnerable dependencies
Requires=docker.service
After=docker.service network.target
StartLimitIntervalSec=60
StartLimitBurst=4

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=${PROJECT_DIR}
Environment=COMPOSE_HTTP_TIMEOUT=120
Environment=DOCKER_CLIENT_TIMEOUT=120

# Script que maneja tanto Vexgen como la aplicación principal
ExecStart=${PROJECT_DIR}/scripts/autofuzz-service.sh start
ExecStop=${PROJECT_DIR}/scripts/autofuzz-service.sh stop
ExecReload=${PROJECT_DIR}/scripts/autofuzz-service.sh restart

# Configuración de usuario y permisos
User=${USER}
Group=docker

# Configuración de reinicio
Restart=on-failure
RestartSec=30

# Logs
StandardOutput=journal
StandardError=journal
SyslogIdentifier=autofuzz

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service file created at ${SERVICE_FILE}."


# Configure service management script
print_status "Configuring service management script..."
sed -i "s|^PROJECT_DIR=.*|PROJECT_DIR=\"$PROJECT_DIR\"|" scripts/autofuzz-service.sh
sed -i "s|^PYTHON_EXEC=.*|PYTHON_EXEC=\"$PYTHON_EXEC\"|" scripts/autofuzz-service.sh
sed -i "s|^MAIN_SCRIPT=.*|MAIN_SCRIPT=\"$MAIN_SCRIPT\"|" scripts/autofuzz-service.sh

chmod +x scripts/autofuzz-service.sh


# Enable the service
print_status "Configuring systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME


# Create CLI script
print_status "Creating CLI script..."


tee /usr/local/bin/autofuzz > /dev/null <<EOF
#!/bin/bash

SERVICE_NAME="${SERVICE_NAME}"
PROJECT_DIR="${PROJECT_DIR}"
PYTHON_EXEC="${PYTHON_EXEC}"
MAIN_SCRIPT="${MAIN_SCRIPT}"

show_help() {
    echo "Autofuzz - Automated Fuzz Testing tool to detect vulnerable dependencies"
    echo ""
    echo "Usage: autofuzz <command> [arguments]"
    echo ""
    echo "Execution commands:"
    echo "  run [args]    Run Autofuzz directly with optional arguments"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  autofuzz run --url http://example.com"
    echo "  autofuzz run --target /path/to/project"
    echo "  autofuzz run --verbose"
    echo ""
}

case "\$1" in
    run)
        shift  # Remove 'run' from arguments
        echo "🐍 Running Autofuzz..."
        cd "\$PROJECT_DIR"
        "\$PYTHON_EXEC" "\$MAIN_SCRIPT" "\$@"
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo "❌ Error: No command specified"
        echo ""
        show_help
        exit 1
        ;;
    *)
        echo "❌ Error: Unknown command '\$1'"
        echo ""
        show_help
        exit 1
        ;;
esac
EOF

chmod +x /usr/local/bin/autofuzz

# Start the service
print_status "Starting Autofuzz service..."
sudo systemctl start $SERVICE_NAME

print_success "Autofuzz service started successfully."
print_success "Installation and setup completed successfully."