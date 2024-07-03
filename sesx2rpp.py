import xml.etree.ElementTree as ET
import argparse
import math

# Function to parse command-line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Convert SESX to RPP")
    parser.add_argument('sesx_file', type=str, help='Path to the .sesx file')
    parser.add_argument('rpp_file', type=str, help='Path to save the .rpp file')
    return parser.parse_args()

# Load and parse the .sesx file
def load_sesx_file(sesx_file):
    tree = ET.parse(sesx_file)
    return tree.getroot()

# Extract file information into a dictionary
def extract_files(root):
    files = {}
    for file_element in root.findall('.//file'):
        file_id = file_element.get('id')
        relative_path = file_element.get('relativePath')
        files[file_id] = relative_path
    return files

# Convert dB volume to REAPER volume
def convert_db_to_reaper_volume(db_volume):
    return 10 ** (db_volume / 20)

# Extract track and clip information using the file dictionary
def extract_tracks_and_clips(root, file_dict):
    tracks = []
    for audio_track in root.findall('.//audioTrack'):
        track_name = audio_track.find('.//name').text if audio_track.find('.//name') is not None else "Unnamed Track"
        volume = 0.0  # Default volume in dB (unity gain)
        pan = 0.0  # Default pan (center)

        # Extract volume and pan from track parameters
        for param in audio_track.findall('.//parameter'):
            if param.get('name') == 'volume':
                volume = float(param.get('parameterValue'))
                print(f"Extracted volume (dB): {volume}")
            elif param.get('name') == 'Pan':
                pan = float(param.get('parameterValue'))
                print(f"Extracted pan: {pan}")

        # Convert volume to REAPER's scale
        reaper_volume = convert_db_to_reaper_volume(volume)
        print(f"Converted volume (REAPER): {reaper_volume}")

        clips = []
        for audio_clip in audio_track.findall('.//audioClip'):
            file_id = audio_clip.get('fileID')
            start_point = float(audio_clip.get('startPoint'))
            length = (float(audio_clip.get('sourceOutPoint')) - float(audio_clip.get('sourceInPoint'))) / 44100.0  # Convert to seconds
            if file_id in file_dict:
                filename = file_dict[file_id]
                clips.append((filename, start_point / 44100.0, length))
        tracks.append((track_name, reaper_volume, pan, clips))
    return tracks

# Create the .rpp file content manually
def create_rpp_file(rpp_file, tracks_and_clips):
    rpp_content = "<REAPER_PROJECT 0.1 \"6.56/OSX64\" 1627915580\n"
    for track_name, volume, pan, clips in tracks_and_clips:
        rpp_content += f"  <TRACK\n"
        rpp_content += f"    NAME \"{track_name}\"\n"
        rpp_content += f"    VOLPAN {volume} {pan} -1 -1 1\n"  # Set volume and pan
        for filename, start_time, length in clips:
            rpp_content += f"    <ITEM\n"
            rpp_content += f"      POSITION {start_time}\n"
            rpp_content += f"      LENGTH {length}\n"
            rpp_content += f"      LOOP 1\n"
            rpp_content += f"      ALLTAKES 0\n"
            rpp_content += f"      NAME \"{filename}\"\n"
            rpp_content += f"      <SOURCE WAVE\n"
            rpp_content += f"        FILE \"{filename}\"\n"
            rpp_content += f"      >\n"
            rpp_content += f"    >\n"
        rpp_content += f"  >\n"
    rpp_content += ">\n"

    # Save the .rpp file
    with open(rpp_file, 'w') as f:
        f.write(rpp_content)
    print(f".rpp file created: {rpp_file}")

def main():
    args = parse_args()
    root = load_sesx_file(args.sesx_file)
    file_dict = extract_files(root)
    tracks_and_clips = extract_tracks_and_clips(root, file_dict)
    create_rpp_file(args.rpp_file, tracks_and_clips)

if __name__ == '__main__':
    main()
