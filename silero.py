import argparse
import csv
import logging
import os
import sys
from typing import Any
from typing import List, Dict

import torch
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


def process_wav_files(folder: str | os.PathLike,
                      file_list: list[str] = None,
                      data_split: str = "",
                      log_folder: str = "logs",
                      threshold: float = 0.250,
                      min_duration: float = 0.5,
                      device: str = "cpu") -> None:
    """
    Process all WAV files in the given folder, merge segments, and optionally export new WAV files.
    If a list of files is not provided, all the folder contents will be used instead.
    Args:
        folder (str): Location of the WAV files.
        file_list (list): A list of WAV file paths.
        data_split (str): If using a file list, it is useful to keep track of the subset ID.
        log_folder (str): Path to the folder for log files.
        threshold (float): Time threshold to merge segments.
        min_duration (float): Minimum duration of segments to keep.
        device: device used for computation. In practice, using a GPU isn't proven to speed-up processing.
    """
    model = load_silero_vad().to(device)
    all_durations = []
    total_audio_duration = 0
    total_speech_duration = 0
    total_segments = 0
    files_without_speech = 0

    if file_list and data_split != "":
        log_folder = os.path.join(log_folder, str(data_split))
        os.makedirs(log_folder, exist_ok=True)
    elif file_list and data_split == "":
        logging.warning("No data split provided for this list of files. Exiting program.")
        exit(1)
    else:  # file_list is None whatever the value of the split:
        print("Scanning folder contents...")

    processed_log = os.path.join(log_folder, 'processed_files.log')
    error_log = os.path.join(log_folder, 'error_files.log')
    warning_log = os.path.join(log_folder, 'warning_files.log')
    speech_segments_file = os.path.join(log_folder, 'speech_segments.csv')

    processed_files = set()
    if os.path.exists(processed_log):
        with open(processed_log, 'r') as f:
            processed_files = set(f.read().splitlines())

    if file_list:
        wav_files = [f for f in file_list if f.endswith('.wav') and f not in processed_files]
    else:
        wav_files = [f for f in os.listdir(folder) if f.endswith('.wav') and f not in processed_files]

    with open(speech_segments_file, 'w', newline='') as csvfile:
        fieldnames = ['filename', 'segment_id', 'start', 'end', 'duration']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        try:
            for filename in tqdm(wav_files, desc="Processing files", unit="file"):
                file_path = os.path.join(folder, filename)
                tqdm.write(f"Processing {filename}")
                try:
                    wav = read_audio(file_path).to(device)
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
                    all_durations.extend([segment['duration'] for segment in cleaned])

                    with open(processed_log, 'a') as f:
                        f.write(f"{filename}\n")
                        f.flush()  # Flush data to disk immediately

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
                        csvfile.flush()  # Flush data to disk immediately

                except Exception as e:
                    with open(error_log, 'a') as f:
                        f.write(f"{filename}: {e}\n")
                    logging.error(f"Error processing file {filename}: {e}")

        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected. Cleaning up and exiting gracefully.")
            csvfile.close()
            sys.exit(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process WAV files to extract and merge speech segments.")
    parser.add_argument('folder', type=str, help="Path to the folder containing WAV files.")
    parser.add_argument('--log_folder', type=str, default="logs", help="Path to the folder for log files.")
    parser.add_argument('--threshold', type=float, default=0.250, help="Time threshold to merge segments.")
    parser.add_argument('--min_duration', type=float, default=0.5, help="Minimum duration of segments to keep.")
    parser.add_argument('--cuda', action='store_true', help="Use CUDA for GPU acceleration (if available).")

    args = parser.parse_args()

    setup_logging(args.log_folder)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    process_wav_files(
        args.folder,
        args.log_folder,
        args.threshold,
        args.min_duration,
        device
    )

    # Create an instance of the Report class and call it
    report = Report(
        original_folder=args.folder,
        csv_file=os.path.join(args.log_folder, 'speech_segments.csv'),
        report_file=os.path.join(args.log_folder, 'report.txt'),
        log_folder=args.log_folder,
    )
    report()
