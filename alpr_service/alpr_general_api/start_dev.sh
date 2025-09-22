#!/bin/bash

# Define variables
IMAGE_NAME="my-fastapi-app"
CONTAINER_NAME="fastapi-container"

# Step 1: Build the Docker image
docker build -t $IMAGE_NAME .

# Step 2: Stop and remove any existing container with the same name
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container..."
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
fi

# Step 3: Run the Docker container
docker run -d -p 8092:8092 --network=alpr-network --name $CONTAINER_NAME -v //e//Final_Project/alpr_backend:/app $IMAGE_NAME

# Step 4: Output the status and access message
echo "FastAPI app is running. Access it at http://localhost:8092"
