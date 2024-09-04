import argparse
import csv
import logging
import os
from typing import List, Tuple, Set, Dict

import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

from utils import get_audio_duration, human_readable_duration


class Report:
    def __init__(self, original_folder: str, csv_file: str, report_file: str, log_folder: str):
        """
        Initialize the Report class with file paths and other necessary attributes.

        :param original_folder: Path to the folder containing original audio files.
        :param csv_file: Path to the CSV file containing segment data.
        :param report_file: Path to the output report file.
        :param log_folder: Path to the folder where logs and histograms will be saved.
        """
        self.original_files = None
        self.original_folder = original_folder
        self.csv_file = csv_file
        self.report_file = report_file
        self.log_folder = log_folder
        self.all_durations = []
        self.total_speech_duration = 0
        self.total_audio_duration = 0
        self.total_files = 0
        self.files_without_speech = 0
        self.total_segments = 0
        self.files_with_speech: Set[str] = set()
        self.file_durations: Dict[str, float] = {}

    def parse_original_files(self) -> Tuple[float, int, Dict[str, float]]:
        """
        Parse the original audio files to calculate total audio duration and file durations.

        :return: Total audio duration, total number of files, and a dictionary of file durations.
        """
        self.total_audio_duration = 0
        self.original_files = [os.path.join(self.original_folder, f) for f in os.listdir(self.original_folder) if
                               f.endswith('.wav')]
        self.total_files = len(self.original_files)

        print("Calculating total audio duration...")
        for file in tqdm(self.original_files):
            duration = get_audio_duration(file)
            self.file_durations[file] = duration
            self.total_audio_duration += duration

        return self.total_audio_duration, self.total_files, self.file_durations

    def parse_csv(self) -> Tuple[List[float], float, int, Set[str]]:
        """
        Parse the CSV file to extract segment durations and other statistics.

        :return: List of all segment durations, total speech duration,
        total number of segments, and a set of files with speech.
        """
        print("Parsing CSV file...")
        with open(self.csv_file, 'r') as file:
            reader = csv.DictReader(file)
            for row in tqdm(reader):
                duration = float(row['duration'])
                self.all_durations.append(duration)
                self.total_speech_duration += duration
                self.files_with_speech.add(row['filename'])
                self.total_segments += 1

        return self.all_durations, self.total_speech_duration, self.total_segments, self.files_with_speech

    def generate_report(self):
        """
        Generate a report based on the parsed data and save it to a file.
        """
        print("Generating report...")
        self.files_without_speech = self.total_files - len(self.files_with_speech)

        if self.all_durations:
            max_duration = max(self.all_durations)
            quartiles = np.percentile(self.all_durations, [25, 50, 75])
            mean_duration = np.mean(self.all_durations)
            std_duration = np.std(self.all_durations)

            speech_percentage = (self.total_speech_duration / self.total_audio_duration) * 100
            non_speech_percentage = 100 - speech_percentage

            report_content = (
                f"Total Number of Files: {self.total_files}\n"
                f"Number of Files Without Speech: {self.files_without_speech}\n"
                f"Total Audio Duration: {self.total_audio_duration:.2f} seconds => {human_readable_duration(int(self.total_audio_duration))}\n"
                f"Total Speech Duration: {self.total_speech_duration:.2f} seconds => {human_readable_duration(int(self.total_speech_duration))}\n"
                f"Percentage of Speech: {speech_percentage:.2f}%\n"
                f"Percentage of Non-Speech: {non_speech_percentage:.2f}%\n"
                f"Total Number of Speech Segments: {self.total_segments}\n"
                f"Maximum Segment Duration: {max_duration:.2f} seconds\n"
                f"Segment Duration Quartiles: {quartiles}\n"
                f"Mean Segment Duration: {mean_duration:.2f} seconds\n"
                f"Standard Deviation of Segment Durations: {std_duration:.2f} seconds\n"
            )

            print(report_content)

            with open(self.report_file, 'w') as report:
                report.write(report_content)

            plt.hist(self.all_durations, bins=10, edgecolor='black')
            plt.title('Histogram of Segment Durations for All Files')
            plt.xlabel('Duration (seconds)')
            plt.ylabel('Frequency')
            histogram_path = os.path.join(self.log_folder, 'segment_durations_histogram.png')
            plt.savefig(histogram_path)
            plt.close()
        else:
            logging.warning("No valid segments found in any files.")

    def __call__(self):
        """
        Execute the report generation process.
        """
        self.parse_original_files()
        self.parse_csv()
        self.generate_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a report from audio segment data.")
    parser.add_argument("original_folder", help="Path to the folder containing original audio files.")
    parser.add_argument("csv_file", help="Path to the CSV file containing segment data.")
    parser.add_argument("report_file", help="Path to the output report file.")
    parser.add_argument("log_folder", help="Path to the folder where logs and histograms will be saved.")
    args = parser.parse_args()

    report = Report(args.original_folder, args.csv_file, args.report_file, args.log_folder)
    report()
