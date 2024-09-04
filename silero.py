import argparse
import csv
import logging
import os
from typing import List, Dict, Any

import soundfile as sf
from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
from tqdm import tqdm

from report import Report


def setup_logging(log_folder: str) -> None:
    """
    Set up logging configuration and create log folder if it doesn't exist.

    Args:
        log_folder (str): Path to the folder for log files.
    """
    os.makedirs(log_folder, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_folder, 'process.log'))
        ]
    )


def merge_segments(segments: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    """
    Merge segments that are closer than the given threshold.

    Args:
        segments (List[Dict[str, Any]]): List of segments with 'start', 'end', and 'duration'.
        threshold (float): Time threshold to merge segments.

    Returns:
        List[Dict[str, Any]]: List of merged segments.
    """
    if not segments:
        return []

    merged_segments = []
    current_segment = segments[0]

    for next_segment in segments[1:]:
        if next_segment['start'] - current_segment['end'] < threshold:
            current_segment['end'] = next_segment['end']
            current_segment['duration'] = current_segment['end'] - current_segment['start']
        else:
            merged_segments.append(current_segment)
            current_segment = next_segment

    merged_segments.append(current_segment)
    return merged_segments


def process_wav_files(folder: str, log_folder: str, export_folder: str, threshold: float = 0.250,
                      min_duration: float = 0.5, export_segments: bool = False) -> None:
    """
    Process all WAV files in the given folder, merge segments, and optionally export new WAV files.

    Args:
        folder (str): Path to the folder containing WAV files.
        log_folder (str): Path to the folder for log files.
        export_folder (str): Path to the folder for exporting segments.
        threshold (float): Time threshold to merge segments.
        min_duration (float): Minimum duration of segments to keep.
        export_segments (bool): Whether to export new WAV files containing only the segments.
    """
    model = load_silero_vad()
    all_durations = []
    total_audio_duration = 0
    total_speech_duration = 0
    total_segments = 0
    files_without_speech = 0

    processed_log = os.path.join(log_folder, 'processed_files.log')
    error_log = os.path.join(log_folder, 'error_files.log')
    warning_log = os.path.join(log_folder, 'warning_files.log')
    speech_segments_file = os.path.join(log_folder, 'speech_segments.csv')

    processed_files = set()
    if os.path.exists(processed_log):
        with open(processed_log, 'r') as f:
            processed_files = set(f.read().splitlines())

    wav_files = [f for f in os.listdir(folder) if f.endswith('.wav') and f not in processed_files]

    with open(speech_segments_file, 'w', newline='') as csvfile:
        fieldnames = ['filename', 'segment_id', 'start', 'end', 'duration']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for filename in tqdm(wav_files, desc="Processing files", unit="file"):
            file_path = os.path.join(folder, filename)
            tqdm.write(f"Processing {filename}")
            try:
                wav = read_audio(file_path)
                total_audio_duration += len(wav) / 16_000  # Assuming 16kHz sample rate
                speech_timestamps = get_speech_timestamps(wav, model)
                if not speech_timestamps:
                    logging.warning(f"No speech in {filename}")
                    with open(warning_log, 'a') as f:
                        f.write(f"{filename}\n")
                    files_without_speech += 1
                    continue

                utterances = [{'start': utt['start'] / 16_000, 'end': utt['end'] / 16_000,
                               'duration': (utt['end'] - utt['start']) / 16_000} for utt in speech_timestamps]
                cleaned = merge_segments(utterances, threshold)
                cleaned = [utt for utt in cleaned if utt['duration'] >= min_duration]

                total_speech_duration += sum(utt['duration'] for utt in cleaned)
                total_segments += len(cleaned)

                if export_segments:
                    os.makedirs(export_folder, exist_ok=True)
                    for i, segment in enumerate(cleaned):
                        segment_wav = wav[int(segment['start'] * 16_000):int(segment['end'] * 16_000)]
                        segment_filename = f"{os.path.splitext(filename)[0]}_{segment['start']:.2f}_{segment['end']:.2f}.wav"
                        segment_path = os.path.join(export_folder, segment_filename)
                        sf.write(segment_path, segment_wav, 16_000)

                all_durations.extend([segment['duration'] for segment in cleaned])

                with open(processed_log, 'a') as f:
                    f.write(f"{filename}\n")

                logging.info(f"Processed file: {filename}")

                # Write speech segments to CSV file
                for segment in cleaned:
                    segment_id = f"{os.path.splitext(filename)[0]}_{segment['start']:.2f}_{segment['end']:.2f}"
                    writer.writerow({
                        'filename': filename,
                        'segment_id': segment_id,
                        'start': segment['start'],
                        'end': segment['end'],
                        'duration': segment['duration']
                    })

            except Exception as e:
                with open(error_log, 'a') as f:
                    f.write(f"{filename}: {e}\n")
                logging.error(f"Error processing file {filename}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process WAV files to extract and merge speech segments.")
    parser.add_argument('folder', type=str, help="Path to the folder containing WAV files.")
    parser.add_argument('--log_folder', type=str, default="logs", help="Path to the folder for log files.")
    parser.add_argument('--export_folder', type=str, default="export",
                        help="Path to the folder for exporting segments.")
    parser.add_argument('--threshold', type=float, default=0.250, help="Time threshold to merge segments.")
    parser.add_argument('--min_duration', type=float, default=0.5, help="Minimum duration of segments to keep.")
    parser.add_argument('--export_segments', action='store_true',
                        help="Whether to export new WAV files containing only the segments.")
    args = parser.parse_args()

    setup_logging(args.log_folder)
    process_wav_files(
        args.folder,
        args.log_folder,
        args.export_folder,
        args.threshold,
        args.min_duration,
        args.export_segments
    )

    # Define the paths
    report_file = 'path_to_your_report_file.txt'

    # Create an instance of the Report class and call it
    report = Report(
        original_folder=args.folder,
        csv_file=os.path.join(args.log_folder, 'speech_segments.csv'),
        log_folder=os.path.join(args.log_folder, 'report.txt'),
        report_file=args.log_folder
    )
    report()
