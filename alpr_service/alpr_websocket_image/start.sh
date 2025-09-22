#!/bin/bash


IMAGE_NAME="image-websocket-image"
CONTAINER_NAME="image-websocket-container"


docker build -t $IMAGE_NAME .


if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi


docker run -d -p 8090:8090 --network=alpr-network --name $CONTAINER_NAME -v //e//Final_Project/image_websocket:/app $IMAGE_NAME


echo "FastAPI app is running. Access it at http://localhost:8090"
