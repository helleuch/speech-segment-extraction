import argparse
import multiprocessing
import os
from functools import partial

from process_output import VADOUtputProcessor
from report import Report
from silero import process_wav_files


def process_wav_files_wrapper(args: dict[str, str | list[str], int]) -> None:
    """Wrapper function to call process_wav_files with the necessary arguments."""
    process_wav_files(
        folder=args['folder'],
        file_list=args['file_list'],
        data_split=args['data_split'],
        log_folder=args['log_folder'],
        device=args['device']
    )


def split_list(lst, n):
    """Split list into n sub-lists."""
    k, m = divmod(len(lst), n)
    return (lst[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


def parse_exclusions(exclusions: str | os.PathLike | list[str]) -> list[str]:
    """
    Parse a list of exclusion files or a single exclusion file to extract filenames.
    Args:
        exclusions (Union[str, List[str]]): A single file path or a list of file paths containing filenames to exclude.
    Returns:
        List[str]: A list of filenames extracted from the exclusion files.
    Raises:
        ValueError: If the exclusions parameter is not a string, list of strings, or os.PathLike.
    """
    filenames = []
    print(f"Exclusion files: {exclusions}")

    def read_file(file_path: str) -> list[str]:
        """Helper function to read lines from a file and strip newline characters."""
        with open(file_path, "r") as file:
            return [line.strip() for line in file]

    if isinstance(exclusions, list):
        for file in exclusions:
            filenames.extend(read_file(file))
    elif isinstance(exclusions, (str, os.PathLike)):
        filenames = read_file(exclusions)
    else:
        raise ValueError(f"Invalid value for parameter exclusions: {exclusions}")

    return filenames


def main(data_folder: str | os.PathLike,
         exclusions: str | os.PathLike | list[str],
         log_folder: str,
         device: str,
         num_processes: int = multiprocessing.cpu_count()) -> None:
    """
    Main function to process WAV files in parallel.

    Args:
        data_folder (str | os.PathLike): Path to the folder containing WAV files.
        exclusions (str | os.PathLike | list[str]): Path to the exclusion file or a list of exclusion files.
        log_folder (str): Path to the folder where logs will be stored.
        device (str): Device to use for processing.
        num_processes (int, optional): Number of processes to use for parallel processing. Defaults to the number of CPU cores.

    Returns:
        None
    """

    exclusions = parse_exclusions(exclusions)
    print(f"{len(exclusions)} files excluded.")

    files = [f for f in os.listdir(data_folder) if f.endswith('.wav') and f not in exclusions]

    # Split the files into sub-lists
    sub_lists = list(split_list(files, num_processes))

    # Create a pool of workers
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(partial(process_wav_files_wrapper),
                 [{'file_list': sub_list,
                   'folder': data_folder,
                   'data_split': idx,
                   'log_folder': log_folder,
                   'device': device}
                  for idx, sub_list in enumerate(sub_lists)])

    output_processor = VADOUtputProcessor(directory_path=log_folder, output_folder="./output")
    output_processor()

    report = Report(
        original_folder=args.data_folder,
        csv_file=os.path.join("./output", 'speech_segments.csv'),
        report_file=os.path.join("./output", 'report.txt'),
        log_folder=args.log_folder,
    )
    report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process WAV files in parallel.")
    parser.add_argument('data_folder', type=str, help='Path to the data folder containing WAV files.')
    parser.add_argument('exclusions', nargs='+', type=str, help='Path to the exclusion file or list of files.')
    parser.add_argument('log_folder', type=str, help='Path to the log folder.')
    parser.add_argument('device', type=str, help='Device to use for processing.')
    parser.add_argument('--num_processes', type=int, default=multiprocessing.cpu_count(),
                        help='Number of processes to use.')

    args = parser.parse_args()

    main(
        data_folder=args.data_folder,
        exclusions=args.exclusions,
        log_folder=args.log_folder,
        device=args.device,
        num_processes=args.num_processes
    )

    # Example call:
    # python
    # corpus_vad.py..\youtube - downloader\audio\.\global_output\processed_files.log.\global_output\warning_files.log
    # logs
    # cpu