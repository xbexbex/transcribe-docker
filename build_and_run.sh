#!/bin/bash

docker build . -t whisper &&
docker run --name=faster-whisper --rm \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e WHISPER_MODEL=tiny-int8 \
  -p 10300:10300 \
  -v /home/xbexbex/git/transcribe-docker/config:/config \
  -v /home/xbexbex/git/transcribe-docker/recordings:/recordings \
  -v /home/xbexbex/git/transcribe-docker/transcriptions:/transcriptions\
  whisper