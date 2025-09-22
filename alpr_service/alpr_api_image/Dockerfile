# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables
# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    # If you need other system dependencies, install them here
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8091 available to the world outside this container
EXPOSE 8089

# Define environment variable
# Customize depending on your application's needs
ENV NAME World

# Run the application:
# Command to run the app using Uvicorn with live auto-reload enabled
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8089", "--reload"]
