#!/bin/bash

# List all service directories
SERVICES=("alpr_api_image" "alpr_general_api" "alpr_web" "alpr_websocket_image" "alpr_websocket_video")

for SERVICE in "${SERVICES[@]}"; do
    echo "Starting $SERVICE..."
    (cd "$SERVICE" && docker-compose up -d)
done

cd "plate_recognizer" && docker-compose -f compose.cpu.yml up
echo "All services started!"
