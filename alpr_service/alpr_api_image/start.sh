#!/bin/bash

IMAGE_NAME="img_api_app"
CONTAINER_NAME="fastapi_image_container"

docker build -t $IMAGE_NAME .

if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

docker run -d -p 8089:8089 --network=alpr-network --name $CONTAINER_NAME -v //e//Final_Project/process-image:/app $IMAGE_NAME

echo "FastAPI app is running. Access it at http://localhost:8089"
