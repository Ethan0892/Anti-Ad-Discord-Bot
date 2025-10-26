#!/bin/bash

# Anti-Ad Bot Launcher for Linux
# Starts both Discord bot and Admin Portal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Anti-Ad Bot v2.0 - Linux Launcher                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    echo "   Install with: sudo apt-get install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "${GREEN}✓ Python ${PYTHON_VERSION} detected${NC}"

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update dependencies
echo -e "${YELLOW}📚 Installing dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Check for .env file
if [ ! -f "config/.env" ]; then
    if [ -f "config/.env.example" ]; then
        echo -e "${YELLOW}⚙️  Creating .env from template...${NC}"
        cp config/.env.example config/.env
        echo -e "${YELLOW}⚠️  Please edit config/.env with your Discord settings${NC}"
        echo -e "${YELLOW}   Exiting for configuration...${NC}"
        exit 1
    else
        echo -e "${RED}❌ config/.env.example not found!${NC}"
        exit 1
    fi
fi

# Check if training data exists
if [ ! -d "Training-Data" ]; then
    echo -e "${YELLOW}📁 Creating Training-Data directory...${NC}"
    mkdir -p Training-Data
fi

if [ ! -f "config/.env" ]; then
    echo -e "${RED}❌ config/.env not found!${NC}"
    echo "   Run: cp config/.env.example config/.env"
    echo "   Then edit config/.env with your settings"
    exit 1
fi

# Parse command line arguments
START_BOT=true
START_PORTAL=true
BACKGROUND=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --bot-only)
            START_PORTAL=false
            shift
            ;;
        --portal-only)
            START_BOT=false
            shift
            ;;
        --background)
            BACKGROUND=true
            shift
            ;;
        --help)
            echo "Usage: ./START.sh [options]"
            echo ""
            echo "Options:"
            echo "  --bot-only       Start only Discord bot"
            echo "  --portal-only    Start only Admin Portal"
            echo "  --background     Run in background"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./START.sh                # Start both bot and portal"
            echo "  ./START.sh --bot-only     # Start only bot"
            echo "  ./START.sh --background   # Start in background"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}⏹️  Shutting down...${NC}"
    if [ ! -z "$BOT_PID" ]; then
        kill $BOT_PID 2>/dev/null || true
    fi
    if [ ! -z "$PORTAL_PID" ]; then
        kill $PORTAL_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✓ Shutdown complete${NC}"
}

trap cleanup EXIT INT TERM

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

# Start services
if [ "$START_BOT" = true ]; then
    echo -e "${YELLOW}🤖 Starting Discord Bot...${NC}"
    if [ "$BACKGROUND" = true ]; then
        python3 src/bot.py > logs/bot.log 2>&1 &
        BOT_PID=$!
        echo -e "${GREEN}✓ Bot started (PID: $BOT_PID)${NC}"
    else
        python3 src/bot.py &
        BOT_PID=$!
    fi
fi

if [ "$START_PORTAL" = true ]; then
    echo -e "${YELLOW}🌐 Starting Admin Portal (http://localhost:5000)...${NC}"
    if [ "$BACKGROUND" = true ]; then
        python3 web_server.py > logs/portal.log 2>&1 &
        PORTAL_PID=$!
        echo -e "${GREEN}✓ Portal started (PID: $PORTAL_PID)${NC}"
    else
        python3 web_server.py &
        PORTAL_PID=$!
    fi
fi

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$START_BOT" = true ]; then
    echo -e "${GREEN}✓ Discord Bot running${NC}"
fi

if [ "$START_PORTAL" = true ]; then
    echo -e "${GREEN}✓ Admin Portal: http://localhost:5000${NC}"
fi

echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Wait for processes
wait
