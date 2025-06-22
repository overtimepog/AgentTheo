#!/bin/bash

# Rebuild the Docker image
echo "Rebuilding Docker image..."
docker build -t browser-agent -f docker/Dockerfile .

# Test with the news gathering task
echo -e "\n\nTesting with news gathering task..."
docker run --rm \
  -e TASK_DESCRIPTION="find me the latest AI news from a bunch of different sources, read their full articles so you can give me a summary on each different one" \
  -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  -e LLM_MODEL="anthropic/claude-3-sonnet" \
  browser-agent