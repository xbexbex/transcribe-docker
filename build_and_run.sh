#!/bin/bash

docker build . -t whisper &&
docker run --name=faster-whisper --rm \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/Helsinki \
  -e WHISPER_MODEL=large-v3 \
  -e WHISPER_COMPUTE_TYPE=int8 \
  -e WHISPER_BEAM_SIZE=5 \
  -p 10300:10300 \
  -v /home/xbexbex/git/transcribe-docker/config:/config \
  -v /home/xbexbex/git/transcribe-docker/recordings:/recordings \
  -v /home/xbexbex/git/transcribe-docker/transcriptions:/transcriptions \
  -v /home/xbexbex/git/transcribe-docker/logseq:/logseq \
  -v /home/xbexbex/git/transcribe-docker/models:/models \
  whisper