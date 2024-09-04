# Speech Segment Extraction Script

This script processes WAV files to extract and merge speech segments using the Silero VAD model. It generates various reports and exports the detected speech segments into separate WAV files. The script also logs the processing details and statistics.

## Table of Contents

- Installation
- Usage
- Arguments
- Output
- Logging
- Reports

## Installation

1. **Clone the repository**:
    ```sh
    git clone github URL here
    cd repo folder here
    ```

2. **Create and activate the conda environment**:
    ```sh
    conda env create -f environment.yaml -n vad
    conda activate vad
    ```

## Usage

To run the script, use the following command:

```sh
python script_name.py /path/to/your/folder [--log_folder /path/to/log/folder] [--threshold 0.250] [--min_duration 0.5] 
```
Example:
```sh
python script_name.py /path/to/your/folder --log_folder /path/to/log/folder --threshold 0.250 --min_duration 0.5
```

## Output
The script generates the following outputs:

1. Processed WAV files: New WAV files containing only the speech segments (if --export_segments is specified).
2. Log files: Detailed logs of the processing steps.
3. Reports: Summary of the processing statistics.
4. CSV file: A CSV file containing details of the detected speech segments.

## Logging
The script logs the processing details into the specified log folder. The following log files are generated:

- process.log: General processing logs.
- processed_files.log: List of successfully processed files.
- error_files.log: List of files that encountered errors during processing.
- warning_files.log: List of files without detected speech segments.

## Reports
The script generates a report.txt file in the log folder, containing the following statistics:

- Total Audio Duration
- Total Speech Duration
- Percentage of Speech
- Percentage of Non-Speech
- Total Number of Speech Segments
- Maximum Segment Duration
- Segment Duration Quartiles
- Mean Segment Duration
- Standard Deviation of Segment Durations
- Total Number of Files
- Number of Files Without Speech
- Additionally, a histogram of segment durations is saved as segment_durations_histogram.png in the log folder.

## CSV File
The script generates a speech_segments.csv file in the log folder, containing details of the detected speech segments with the following columns:

- filename: Name of the original WAV file.
- segment_id: Unique ID for the segment (format: fileID_start_end).
- start: Start time of the segment.
- end: End time of the segment.
- duration: Duration of the segment.

## License
TBD.

## Acknowledgements
This script uses the [Silero VAD model](https://github.com/snakers4/silero-vad) for voice activity detection. Special thanks to the developers of Silero VAD.


