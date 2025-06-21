#!/bin/bash

# Quick setup for local testing (without Docker)

echo "Browser Agent - Quick Local Setup"
echo "================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required"
    exit 1
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Check environment
if [ ! -f "config/.env" ]; then
    echo "Error: config/.env not found"
    echo "Please copy config/.env.template to config/.env and add your OpenRouter API key"
    exit 1
fi

# Run test
echo ""
echo "Setup complete! Testing the agent..."
echo ""

# Set environment variables
export $(grep -v '^#' config/.env | xargs)
export PYTHONPATH=$(pwd):$PYTHONPATH

# Run test
python tests/test_agent.py

echo ""
echo "To run tasks locally:"
echo "source venv/bin/activate"
echo "export \$(grep -v '^#' config/.env | xargs)"
echo "export TASK_DESCRIPTION='your task here'"
echo "python entrypoint.py"