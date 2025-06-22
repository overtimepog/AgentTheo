# Utility Scripts

This folder contains utility scripts for development and maintenance tasks.

## Scripts

### cleanup_test_files.sh
Removes temporary test files created during development:
- `test_*.py`
- `debug_*.py`
- `diagnose_*.py`
- `fix_*.py`
- `container_*.py`

### fix_container_env.sh
Fixes container environment issues:
- Ensures correct LLM model configuration in `.env`
- Updates from non-function-calling models to compatible ones
- Makes scripts executable
- Provides debugging guidance

### local_setup.sh
Quick setup for local testing (without Docker):
- Creates Python virtual environment
- Installs Python dependencies
- Installs Playwright browsers
- Runs initial test to verify setup

### rebuild_and_test.sh
Quick rebuild and test script:
- Rebuilds the Docker image
- Tests with a sample AI news gathering task
- Uses Claude Sonnet model for testing

## Usage

All scripts should be run from the project root:

```bash
# From project root
./utility-scripts/cleanup_test_files.sh
./utility-scripts/fix_container_env.sh
./utility-scripts/rebuild_and_test.sh
```