print("Loading imports...")
 
import os
import re
import shutil
from faster_whisper import WhisperModel
from pymediainfo import MediaInfo
from datetime import datetime

# Get model size and type from WHISPER_MODEL environment variable
# Example value for WHISPER_MODEL: "large-v2-float16" or "tiny-int8"
model_size = os.getenv("WHISPER_MODEL", "large-v3")
compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float32")
reprocess_unprocessed = os.getenv("REPROCESS_UNPROCESSED", "false").lower() in ["true", "1"]

# Initialize the Whisper model
model = WhisperModel(model_size, device="cpu", compute_type=compute_type, download_root="/models")

# Define directories for recordings, transcriptions, and logseq-transcribe
recordings_dir = "/recordings"
transcriptions_dir = "/transcriptions"
recordings_backup_dir = "/recordings_backup"
logseq_dir = "/logseq"
obsidian_dir = "/obsidian"

# Ensure the transcription and logseq-transcribe directories exist
os.makedirs(transcriptions_dir, exist_ok=True)
os.makedirs(recordings_dir, exist_ok=True)
os.makedirs(recordings_backup_dir, exist_ok=True)
# os.makedirs(logseq_dir, exist_ok=True)
os.makedirs(os.path.join(logseq_dir, "pages"), exist_ok=True)
os.makedirs(os.path.join(logseq_dir, "assets"), exist_ok=True)
os.makedirs(obsidian_dir, exist_ok=True)
os.makedirs(os.path.join(obsidian_dir, "r"), exist_ok=True)

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

    if "retranscribe" in file_name:
        file_name = remove_retranscribe_from_str(file_name)
        
    name, ext = os.path.splitext(file_name)
    new_name = f"{name} (transcribed){ext}"

    return file_dir, new_name

# Function to rename the original audio file by appending (transcribed)
def rename_file_as_transcribed(file_path, new_file_path):
    os.rename(file_path, new_file_path)

# Function to transcribe audio files
def transcribe_audio(file_path, output_file):
    try:
        segments, info = model.transcribe(file_path, beam_size=5, best_of=5, task="transcribe")
        probability = None
        if float(info.language_probability) < 0.9 and info.language != "en":
            print(f"Detected language '{info.language}' with probability {info.language_probability}. The detected language is likely wrong, transcribing again to english.")
            segments, info = model.transcribe(file_path, beam_size=5, best_of=5, task="transcribe", language="en")
            probability = "forced"
        else:
            print(f"Detected language '{info.language}' with probability {info.language_probability}")
            probability = info.language_probability
        
        file_dir, new_file_name = get_renamed_file_dir_and_name(file_path)
        # Write the transcription to the markdown file
        with open(output_file, 'w') as f:
            f.write(f"- ![{new_file_name}](../assets/{new_file_name})\n")
            f.write(f"- _metadata_\n")
            f.write(f"  collapsed:: true\n")
            f.write(f"    - Detected language: {info.language}\n")
            f.write(f"    - Language probability: {probability}\n")
            f.write(f"    - Model: {model_size}\n")
            f.write(f"- #unprocessed\n")
            f.write(f"-\n")
            
            f.write("- ")
            for segment in segments:
                line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
                f.write(line)
    except Exception as e:
        print(f"Error transcribing {file_path}: {e}")


def retranscribe_audio_to_language(file_path, language):
    try:
        segments, info = model.transcribe(file_path, beam_size=5, best_of=5, language=language, task="transcribe")
        # Build the transcription text
        transcription_lines = []
        transcription_lines.append("- ")
        for segment in segments:
            line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
            transcription_lines.append(line)
        transcription_text = ''.join(transcription_lines)
        return transcription_text, info
    except Exception as e:
        print(f"Error retranscribing {file_path}: {e}")
        return None, None
    
def remove_retranscribe_from_str(s):
    s = s.replace(" (retranscribe)", "").replace("(retranscribe)", "").replace(" (retranscribed)", "").replace("(retranscribed)", "")
    return s

# Loop through files in the /recordings folder
def transcribe_files_in_directory():
    print("Transcribing files in the recordings directory...")
    for root, dirs, files in os.walk(recordings_dir):
        for file in files:
            # Ignore hidden files and already transcribed files
            if file.startswith(".") or "(transcribed)" in file:
                continue
            
            # Process supported audio files
            if file.endswith((".mp3", ".wav", ".flac", ".m4a")):  
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")

                retranscribe = False
                if "retranscribe" in file:
                    print("The file is going to be retranscribed")
                    retranscribe = True
                    file = remove_retranscribe_from_str(file)

                file_base_name = os.path.splitext(file)[0]
                file_date_str, file_time_str = file_base_name.split("_")
                file_date = datetime.strptime(file_date_str, "%Y-%m-%d")

                # Generate new file name with "r___" prefix and duration suffix
                duration = get_duration(file_path)

                transcription_file_name = f"r___{os.path.splitext(file)[0]}{duration}.md"


                year = file_date.year
                month = f"{file_date.month:02d}"  # Ensure two digits for month
                day = f"{file_date.day:02d}"

                time_part = file_time_str.replace("-", ".")
                transcription_file_name = f"r___{year}___{month}___{day}  {time_part}  ({duration}).md"
                transcription_file_path = os.path.join(transcriptions_dir, transcription_file_name)

                # Check if the file already exists in /transcriptions
                if os.path.exists(transcription_file_path) and not retranscribe:
                    print(f"Skipping {file_path}, transcription already exists.")
                else:
                    # Transcribe and save the output to the .md file
                    transcribe_audio(file_path, transcription_file_path)

                # Copy the file to /logseq-transcribe
                logseq_transcription_file_path = os.path.join(logseq_dir, "pages", transcription_file_name)
                if (not os.path.exists(logseq_transcription_file_path)) or retranscribe:
                    shutil.copyfile(transcription_file_path, logseq_transcription_file_path)
                else:
                    print(f"Transcription already exists in pages: {logseq_transcription_file_path}")

                # Mirror the transcription into the Obsidian vault using the same naming pattern
                obsidian_parent_dir = os.path.join(obsidian_dir, "r", str(year), month)
                os.makedirs(obsidian_parent_dir, exist_ok=True)

                obsidian_file_name = f"{day} {time_part} ({duration}).md"
                obsidian_file_path = os.path.join(obsidian_parent_dir, obsidian_file_name)

                if (not os.path.exists(obsidian_file_path)) or retranscribe:
                    shutil.copyfile(transcription_file_path, obsidian_file_path)
                else:
                    print(f"Transcription already exists in Obsidian: {obsidian_file_path}")
                
                new_recording_file_dir, new_recording_file_name = get_renamed_file_dir_and_name(file_path)
                new_recording_file_path = os.path.join(new_recording_file_dir, new_recording_file_name)

                # Rename the original file by appending (transcribed)
                if (not os.path.exists(new_recording_file_path)) or retranscribe:
                    rename_file_as_transcribed(file_path, new_recording_file_path)
                    print(f"Renamed original file to {new_recording_file_path}")
                
                # logseq_asset_file_path = os.path.join(logseq_dir, "assets", new_recording_file_name)
                # if (not os.path.exists(logseq_asset_file_path)) or retranscribe:
                #     shutil.copyfile(new_recording_file_path, logseq_asset_file_path)
                # else:
                #     print(f"File already exists in assets: {logseq_asset_file_path}")

                record_backup_file_path = os.path.join(recordings_backup_dir, new_recording_file_name)
                if (not os.path.exists(record_backup_file_path)) or retranscribe:
                    shutil.copyfile(new_recording_file_path, record_backup_file_path)
                else:
                    print(f"File already exists in backup folder: {record_backup_file_path}")

#Function to retranscribe files in the logseq directory based on #retranscribe/(language) tag
def extract_filename_from_markdown_line(line):
    # Line is expected to be in the format: '- ![alt_text](../assets/filename)'
    line = line.strip()
    if line.startswith('- ![') and '](' in line and line.endswith(')'):
        # Find positions of '![', ']', '](' and the last ')'
        start_alt = line.find('![') + 2
        end_alt = line.find(']', start_alt)
        start_link = line.find('](', end_alt) + 2
        end_link = line.rfind(')')
        link = line[start_link:end_link]
        # Now, extract filename from link
        if link.startswith('../assets/'):
            filename = link[len('../assets/'):]
        else:
            filename = link
        return filename
    else:
        return None  # or raise an error

# Function to retranscribe files in the logseq directory based on #retranscribe/(language) tag
def retranscribe_files_in_logseq():
    pages_dir = os.path.join(logseq_dir, "pages")
    print(f"Checking for files to retranscribe in {pages_dir}")
    for file_name in os.listdir(pages_dir):
        if not file_name.startswith("r___") or not file_name.endswith(".md"):
            continue
        file_path = os.path.join(pages_dir, file_name)
        with open(file_path, 'r') as f:
            lines = f.readlines()
        # Check if file contains '#retranscribe/(language)'
        retranscribe_line_idx = None
        retranscribe_language = None
        unprocessed_line_idx = None

        for idx, line in enumerate(lines):
            if reprocess_unprocessed and '#unprocessed' in line:
                unprocessed_line_idx = idx
                retranscribe_language = "en"
            if '#retranscribe' in line:
                retranscribe_line = line.strip()
                retranscribe_line_idx = idx

                if '/' in retranscribe_line and len(retranscribe_line.split('#retranscribe/')[1].strip()) > 0:
                    retranscribe_language = retranscribe_line.split('#retranscribe/')[1].strip()
                else:
                    retranscribe_language = "en"
                    print(f"No language specified in retranscribe tag, defaulting to English (en)")

                break

        if retranscribe_language is not None and (retranscribe_line_idx is not None or unprocessed_line_idx is not None):
            language = retranscribe_language
            print(f"Retranscribing {file_name} to language '{language}'")
            # Remove the #retranscribe/ line

            if retranscribe_line_idx is not None:
                del lines[retranscribe_line_idx]
            # Update the metadata block
            for idx, line in enumerate(lines):
                if 'Detected language:' in line:
                    lines[idx] = f"    - Detected language: {language}\n"
                elif 'Language probability:' in line:
                    lines[idx] = f"    - Language probability: forced\n"
            # Find the audio file
            audio_file_line = None
            for idx, line in enumerate(lines):
                if '- ![' in line:
                    audio_file_line = line.strip()
                    break
            if audio_file_line:
                # Extract audio file name using the new function
                audio_file_name_in_path = extract_filename_from_markdown_line(audio_file_line)
                if audio_file_name_in_path:
                    # The audio file should be in recordings_backup_dir
                    audio_file_path = os.path.join(recordings_backup_dir, audio_file_name_in_path)
                    if not os.path.exists(audio_file_path):
                        print(f"Audio file {audio_file_path} not found in recordings backup directory. Trying the recordings directory.")
                        
                        audio_file_path = os.path.join(recordings_dir, audio_file_name_in_path)
                        if not os.path.exists(audio_file_path):
                            print(f"Audio file {audio_file_path} not found in recordings directory. Trying the logseq assets directory.")
                            audio_file_path = os.path.join(logseq_dir, "assets", audio_file_name_in_path)
                            if not os.path.exists(audio_file_path):
                                print(f"Audio file {audio_file_path} not found in logseq assets directory. Skipping {file_name}")
                                continue
                            else:
                                shutil.copyfile(audio_file_path, os.path.join(recordings_backup_dir, audio_file_name_in_path))
                                print(f"Copied {audio_file_path} to {os.path.join(recordings_backup_dir, audio_file_name_in_path)}")
                        else:
                            shutil.copyfile(audio_file_path, os.path.join(recordings_backup_dir, audio_file_name_in_path))
                            print(f"Copied {audio_file_path} to {os.path.join(recordings_backup_dir, audio_file_name_in_path)}")

                    # Retranscribe the audio file to the specified language
                    new_transcription, info = retranscribe_audio_to_language(audio_file_path, language)
                    if new_transcription is None:
                        print(f"Failed to retranscribe {audio_file_name_in_path}")
                        continue
                    # Find the start and end of the transcription block
                    # The transcription block starts with '- [' and ends when the pattern no longer matches
                    transcription_start_idx = None
                    for idx, line in enumerate(lines):
                        if re.match(r'- \[.*?\s->\s.*?\]', line.strip()):
                            transcription_start_idx = idx
                            break
                    if transcription_start_idx is None:
                        print(f"Could not find transcription block in {file_name}")
                        continue
                    # Find the end of the transcription block
                    transcription_end_idx = transcription_start_idx + 1
                    for idx in range(transcription_start_idx + 1, len(lines)):
                        if not re.match(r'\[.*?\s->\s.*?\]', lines[idx].strip()):
                            transcription_end_idx = idx
                            break
                    else:
                        transcription_end_idx = len(lines)
                    # Build the new content
                    new_lines = lines[:transcription_start_idx]
                    # Add the new transcription
                    new_lines.append(new_transcription)
                    # Add the remaining lines
                    new_lines.extend(lines[transcription_end_idx:])
                    # Write the updated content back to the file
                    with open(file_path, 'w') as f:
                        f.writelines(new_lines)
                    print(f"Updated transcription in {file_path}")
                    # Also update the corresponding file in the transcriptions directory
                    transcription_file_path = os.path.join(transcriptions_dir, file_name)
                    if os.path.exists(transcription_file_path):
                        # The code to update the transcription file is similar
                        with open(transcription_file_path, 'r') as f:
                            transcription_lines = f.readlines()
                        # Remove the #retranscribe/ line if it exists
                        retranscribe_line_idx_transcription = None
                        for idx, line in enumerate(transcription_lines):
                            if '#retranscribe/' in line:
                                retranscribe_line_idx_transcription = idx
                                break
                        if retranscribe_line_idx_transcription is not None:
                            del transcription_lines[retranscribe_line_idx_transcription]
                        # Update the metadata block
                        for idx, line in enumerate(transcription_lines):
                            if 'Detected language:' in line:
                                transcription_lines[idx] = f"    - Detected language: {language}\n"
                            elif 'Language probability:' in line:
                                transcription_lines[idx] = f"    - Language probability: forced\n"
                        # Find the transcription block
                        transcription_start_idx_transcription = None
                        for idx, line in enumerate(transcription_lines):
                            if re.match(r'- \[.*?\s->\s.*?\]', line.strip()):
                                transcription_start_idx_transcription = idx
                                break
                        if transcription_start_idx_transcription is not None:
                            # Find the end of the transcription block
                            transcription_end_idx_transcription = transcription_start_idx_transcription + 1
                            for idx in range(transcription_start_idx_transcription + 1, len(transcription_lines)):
                                if not re.match(r'\[.*?\s->\s.*?\]', transcription_lines[idx].strip()):
                                    transcription_end_idx_transcription = idx
                                    break
                            else:
                                transcription_end_idx_transcription = len(transcription_lines)
                            # Build the new content
                            new_transcription_lines = transcription_lines[:transcription_start_idx_transcription]
                            new_transcription_lines.append(new_transcription)
                            new_transcription_lines.extend(transcription_lines[transcription_end_idx_transcription:])
                            # Write the updated content back to the transcription file
                            with open(transcription_file_path, 'w') as f:
                                f.writelines(new_transcription_lines)
                            print(f"Updated transcription in {transcription_file_path}")
                        else:
                            print(f"Could not find transcription block in {transcription_file_path}")
                    else:
                        print(f"Corresponding transcription file {transcription_file_path} not found. Copying from pages directory.")
                        # Copy the pages file to the transcriptions directory
                        shutil.copyfile(file_path, transcription_file_path)
                        print(f"Copied {file_path} to {transcription_file_path}")
                else:
                    print(f"Could not parse audio file line in {file_name}")
            else:
                print(f"Audio file line not found in {file_name}")
        else:
            # No retranscribe tag found
            continue

if __name__ == "__main__":
    retranscribe_files_in_logseq()
    print("Starting transcription for new recordings...")
    transcribe_files_in_directory()
    print("Transcription complete.")
    print("Done.")
