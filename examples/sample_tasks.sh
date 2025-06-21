#!/bin/bash

# Sample Browser Agent Tasks
# This file demonstrates various tasks the browser agent can perform

echo "Browser Agent - Sample Tasks"
echo "============================"
echo ""
echo "Make sure you have:"
echo "1. Docker installed and running"
echo "2. OpenRouter API key in config/.env"
echo ""

# Basic navigation
echo "1. Basic Navigation:"
echo "./run.sh task \"go to wikipedia.org and get the page title\""
echo ""

# Search task
echo "2. Search Task:"
echo "./run.sh task \"search for artificial intelligence on google and extract the first 3 results\""
echo ""

# Form interaction
echo "3. Form Interaction:"
echo "./run.sh task \"go to example.com and find all the links on the page\""
echo ""

# Data extraction
echo "4. Data Extraction:"
echo "./run.sh task \"navigate to hacker news and get the top 5 headlines\""
echo ""

# Multi-step task
echo "5. Multi-step Task:"
echo "./run.sh task \"go to github.com, search for langchain, and find the most starred repository\""
echo ""

echo "Run any of these commands to test the browser agent!"