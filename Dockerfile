# Use linuxserver/faster-whisper as the base image
FROM linuxserver/faster-whisper

# Install mediainfo
RUN apt-get update && \
    apt-get install -y mediainfo && \
    apt-get clean && \
    pip install pymediainfo

# Set working directory
WORKDIR /app

# Copy the transcription script into the container
COPY transcribe.py /app/transcribe.py

# Set the default directory where the recordings will be located
# VOLUME ["/recordings"]

# Make the transcribe.py script executable
RUN chmod +x /app/transcribe.py

# Default command to run the transcription script
CMD [ "python3", "/app/transcribe.py" ]
