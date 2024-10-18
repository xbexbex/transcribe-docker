import os
import shutil
from faster_whisper import WhisperModel
from pymediainfo import MediaInfo
from datetime import datetime

# Get model size and type from WHISPER_MODEL environment variable
# Example value for WHISPER_MODEL: "large-v2-float16" or "tiny-int8"
model_size = os.getenv("WHISPER_MODEL", "large-v3")
compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float32")

# Initialize the Whisper model
model = WhisperModel(model_size, device="cpu", compute_type=compute_type, download_root="/models")

# Define directories for recordings, transcriptions, and logseq-transcribe
recordings_dir = "/recordings"
transcriptions_dir = "/transcriptions"
recordings_backup_dir = "/recordings_backup"
logseq_dir = "/logseq"

# Ensure the transcription and logseq-transcribe directories exist
os.makedirs(transcriptions_dir, exist_ok=True)
os.makedirs(recordings_dir, exist_ok=True)
os.makedirs(recordings_backup_dir, exist_ok=True)
# os.makedirs(logseq_dir, exist_ok=True)
os.makedirs(os.path.join(logseq_dir, "pages"), exist_ok=True)
os.makedirs(os.path.join(logseq_dir, "assets"), exist_ok=True)

# Function to get the media duration in (XhYmZs) format
def get_duration(file_path):
    media_info = MediaInfo.parse(file_path)
    for track in media_info.tracks:
        if track.track_type == 'Audio':
            duration_in_ms = track.duration
            duration_in_seconds = int(duration_in_ms / 1000)
            hours = duration_in_seconds // 3600
            minutes = (duration_in_seconds % 3600) // 60
            seconds = duration_in_seconds % 60
            if hours > 0:
                return f"{hours}h{minutes}m{seconds}s"
            else:
                return f"{minutes}m{seconds}s"
    return ""

def get_renamed_file_dir_and_name(file_path):
    file_dir, file_name = os.path.split(file_path)
    name, ext = os.path.splitext(file_name)
    new_name = f"{name} (transcribed){ext}"

    return file_dir, new_name

# Function to rename the original audio file by appending (transcribed)
def rename_file_as_transcribed(file_path):
    file_dir, file_name = get_renamed_file_dir_and_name(file_path)
    new_file_path = os.path.join(file_dir, file_name)
    os.rename(file_path, new_file_path)
    return new_file_path, file_name

# Function to transcribe audio files
def transcribe_audio(file_path, output_file):
    try:
        segments, info = model.transcribe(file_path, beam_size=5, patience=1.5, best_of=7)
        print(f"Detected language '{info.language}' with probability {info.language_probability}")
        
        file_dir, new_file_name = get_renamed_file_dir_and_name(file_path)
        # Write the transcription to the markdown file
        with open(output_file, 'w') as f:
            f.write(f"- ![2024-09-25_18-50-33.m4a](../assets/{new_file_name})\n")
            f.write(f"- _metadata_\n")
            f.write(f"  collapsed:: true\n")
            f.write(f"    - Detected language: {info.language}\n")
            f.write(f"    - Language probability: {info.language_probability}\n")
            f.write(f"    - Model: {model_size}\n")
            f.write(f"- #unprocessed\n")
            f.write(f"-\n")
            
            f.write("- ")
            for segment in segments:
                line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
                f.write(line)
    except Exception as e:
        print(f"Error transcribing {file_path}: {e}")

# Loop through files in the /recordings folder
def transcribe_files_in_directory():
    for root, dirs, files in os.walk(recordings_dir):
        for file in files:
            # Ignore hidden files and already transcribed files
            if file.startswith(".") or "(transcribed)" in file:
                continue
            
            # Process supported audio files
            if file.endswith((".mp3", ".wav", ".flac", ".m4a")):  
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                file_base_name = os.path.splitext(file)[0]
                file_date_str, file_time_str = file_base_name.split("_")
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                # Generate new file name with "r___" prefix and duration suffix
                duration = get_duration(file_path)
                new_file_name = f"r___{os.path.splitext(file)[0]}{duration}.md"

                year = file_date.year
                month = f"{file_date.month:02d}"  # Ensure two digits for month
                day = f"{file_date.day:02d}"

                time_part = file_time_str.replace("-", ".")
                new_file_name = f"r___{year}___{month}___{day}  {time_part}  ({duration}).md"
                output_file_path = os.path.join(transcriptions_dir, new_file_name)

                # Check if the file already exists in /transcriptions
                if os.path.exists(output_file_path):
                    print(f"Skipping {file_path}, transcription already exists.")
                    continue

                # Transcribe and save the output to the .md file
                transcribe_audio(file_path, output_file_path)

                # Copy the file to /logseq-transcribe
                logseq_output_file_path = os.path.join(logseq_dir, "pages", new_file_name)
                shutil.copyfile(output_file_path, logseq_output_file_path)
                print(f"Copied transcription to {logseq_output_file_path}")

                # Rename the original file by appending (transcribed)
                new_file_path, new_file_name = rename_file_as_transcribed(file_path)
                print(f"Renamed original file to {new_file_path}")
                shutil.copyfile(new_file_path, os.path.join(logseq_dir, "assets", new_file_name))
                shutil.copyfile(new_file_path, os.path.join(recordings_backup_dir, new_file_name))

if __name__ == "__main__":
    transcribe_files_in_directory()
