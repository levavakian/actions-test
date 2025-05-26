#!/bin/bash

# Check if submission name is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <submission_name>"
    echo "Example: $0 your_submission_folder"
    echo ""
    echo "Available submissions:"
    ls -1 submissions/ 2>/dev/null | grep -E '^submission_' || echo "No submissions found in submissions/ directory"
    exit 1
fi

SUBMISSION_NAME=$1
SUBMISSION_FOLDER_PATH="submissions/$SUBMISSION_NAME"

# Check if submission folder exists
if [ ! -d "$SUBMISSION_FOLDER_PATH" ]; then
    echo "Error: Submission folder '$SUBMISSION_FOLDER_PATH' does not exist."
    echo ""
    echo "Available submissions:"
    ls -1 submissions/ 2>/dev/null | grep -E '^submission_' || echo "No submissions found in submissions/ directory"
    exit 1
fi

echo "Running submission: $SUBMISSION_NAME"
echo "Submission folder: $SUBMISSION_FOLDER_PATH"
echo "=================================="

# Export the submission folder name (not full path) for docker-compose
export SUBMISSION_FOLDER=$SUBMISSION_NAME

# Run docker-compose
echo "Starting docker-compose..."
docker compose up --build --abort-on-container-exit

echo "Docker-compose execution completed."

# Get logs from all services
echo "=== FINAL LOGS FROM ALL SERVICES ==="
docker compose logs

# Clean up
echo "Cleaning up containers and volumes..."
docker compose down -v

echo "=================================="
echo "Submission '$SUBMISSION_NAME' execution completed."
