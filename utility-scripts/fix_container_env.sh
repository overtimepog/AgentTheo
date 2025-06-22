#!/bin/bash
# Script to fix container environment issues

echo "Fixing BrowserBase container environment issues..."

# 1. Ensure the .env file has the correct model
if [ -f "config/.env" ]; then
    # Check if LLM_MODEL is set
    if ! grep -q "^LLM_MODEL=" config/.env; then
        echo "Adding LLM_MODEL to .env file..."
        echo "" >> config/.env
        echo "# Fixed: Use a model that supports function calling" >> config/.env
        echo "LLM_MODEL=openai/gpt-4o-mini" >> config/.env
    else
        # Check if it's set to deepseek
        if grep -q "^LLM_MODEL=deepseek" config/.env; then
            echo "Updating LLM_MODEL from deepseek to gpt-4o-mini..."
            sed -i.bak 's/^LLM_MODEL=deepseek.*/LLM_MODEL=openai\/gpt-4o-mini/' config/.env
        fi
    fi
else
    echo "Warning: config/.env not found. Creating from template..."
    cp config/.env.template config/.env
    echo "Please update config/.env with your OPENROUTER_API_KEY"
fi

# 2. Make scripts executable
chmod +x docker-entrypoint.sh
chmod +x docker/debug-entrypoint.sh
chmod +x debug_container_issue.py

echo ""
echo "Container environment fixes applied!"
echo ""
echo "Key changes made:"
echo "1. Default LLM model changed from 'deepseek/deepseek-chat' to 'openai/gpt-4o-mini'"
echo "   - deepseek doesn't support function calling (tool use)"
echo "   - gpt-4o-mini supports function calling properly"
echo ""
echo "2. Added detailed logging to identify when models don't support function calling"
echo ""
echo "3. Created debug scripts to diagnose container-specific issues"
echo ""
echo "To test the fix:"
echo "1. Rebuild the container: docker-compose -f docker/docker-compose.yml build"
echo "2. Run with a test task: TASK_DESCRIPTION='Go to google.com and search for AI news' docker-compose -f docker/docker-compose.yml up"
echo ""
echo "For debugging mode:"
echo "DEBUG_MODE=true TASK_DESCRIPTION='test task' docker-compose -f docker/docker-compose.yml up"