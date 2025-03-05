# Use linuxserver/faster-whisper as the base image
FROM python:3.12.6

# Install mediainfo
RUN apt-get update && \
    apt-get install -y mediainfo && \
    apt-get clean && \
    pip install pymediainfo faster-whisper

# Set working directory
WORKDIR /app

# Copy the transcription script into the container
COPY transcribe.py /app/transcribe.py

# Set the default directory where the recordings will be located
# VOLUME ["/recordings"]

# Make the transcribe.py script executable
RUN chmod +x /app/transcribe.py

# Default command to run the transcription script
CMD [ "python3", "-u", "/app/transcribe.py" ]
