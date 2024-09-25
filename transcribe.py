import os
from faster_whisper import WhisperModel
from pymediainfo import MediaInfo

whisper_model_env = os.getenv("WHISPER_MODEL", "large-v3-int8")

# Initialize the model
model_size = os.getenv("WHISPER_MODEL_SIZE", "large-v3")
compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
model = WhisperModel(model_size, device="cpu", compute_type="int8")

# Define directories for recordings and transcriptions
recordings_dir = "/recordings"
transcriptions_dir = "/transcriptions"

# Ensure the transcriptions directory exists
os.makedirs(transcriptions_dir, exist_ok=True)

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
                return f"_{hours}h{minutes}m{seconds}s"
            else:
                return f"_{minutes}m{seconds}s"
    return ""

# Function to transcribe audio files
def transcribe_audio(file_path, output_file):
    try:
        segments, info = model.transcribe(file_path, beam_size=5)
        print(f"Detected language '{info.language}' with probability {info.language_probability}")

        # Write the transcription to the markdown file
        with open(output_file, 'w') as f:
            f.write(f"# Transcription for {file_path}\n")
            f.write(f"Detected language: {info.language}\n")
            f.write(f"Language probability: {info.language_probability}\n\n")
            
            for segment in segments:
                line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
                print(line)
                f.write(line)
    except Exception as e:
        print(f"Error transcribing {file_path}: {e}")

# Loop through files in the /recordings folder
def transcribe_files_in_directory():
    for root, dirs, files in os.walk(recordings_dir):
        for file in files:
            # Ignore hidden files (those starting with a dot)
            if file.startswith("."):
                continue

            # Process supported audio files
            if file.endswith((".mp3", ".wav", ".flac", ".m4a")):  
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                # Generate new file name with "r___" prefix and duration suffix
                duration = get_duration(file_path)
                new_file_name = f"r___{os.path.splitext(file)[0]}{duration}.md"
                output_file_path = os.path.join(transcriptions_dir, new_file_name)

                # Transcribe and save the output to the .md file
                transcribe_audio(file_path, output_file_path)

if __name__ == "__main__":
    transcribe_files_in_directory()
