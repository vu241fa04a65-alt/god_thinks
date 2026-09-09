#!/usr/bin/env bash
set -e

echo "Deploying CropHealthAI..."
pip install -r backend/requirements.txt
pytest backend/tests/
echo "Deployment tests passed. Ready for containerization."
