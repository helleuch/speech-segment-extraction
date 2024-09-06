import glob
import os
from typing import Union, Dict, List

import pandas as pd


class VADOUtputProcessor:
    def __init__(self, directory_path: Union[str, os.PathLike], output_folder: str = "./global_output"):
        self.directory_path = directory_path
        self.output_folder = output_folder

    def _retrieve_output(self) -> Dict[str, List[str]]:
        """
        Retrieve the contents of a directory, including sub-folders and specified files.

        Returns:
            Dict[str, List[str]]: A dictionary where keys are file patterns and values are lists of file paths.
        """
        print("Retrieving contents...")

        # Get all sub-folders
        sub_folders = [f.path for f in os.scandir(self.directory_path) if f.is_dir()]

        # Define file patterns to search for
        file_patterns = ['processed_files.log', 'speech_segments.csv', 'warning_files.log']
        contents: Dict[str, List[str]] = {pattern: [] for pattern in file_patterns}

        # Search for files matching the patterns
        for pattern in file_patterns:
            results = glob.glob(os.path.join(self.directory_path, '**', pattern), recursive=True)
            contents[pattern].extend(results)

        # Print sub-folders
        print(f"Sub-folders: {' '.join(sub_folders)}")

        # Print specified files
        print("\nSpecified files:")
        for file_type, files in contents.items():
            print(f"\t{file_type}: {' '.join(files)}")

        return contents

    def _merge_vad_output(self, files: Dict[str, List[str]]) -> None:
        """
        Merge VAD output files into a single file for each file type.

        Args:
            files (Dict[str, List[str]]): A dictionary where keys are file types and values are lists of file paths.

        Returns:
            None
        """
        print("\nMerging files...")

        for file_type, file_list in files.items():
            if not file_type.endswith(".csv"):
                contents = []
                for file in file_list:
                    with open(file, "r") as f:
                        contents.extend(f.readlines())

                print(f"Files in {file_type} before duplicate removal: {len(contents)}")
                contents = list(set(contents))
                print(f"Files in {file_type} after duplicate removal: {len(contents)}")

                os.makedirs(self.output_folder, exist_ok=True)
                with open(os.path.join(self.output_folder, file_type), "w") as f:
                    f.writelines(contents)
            else:
                dataframes = []
                target_len = 0
                for file in file_list:
                    df = pd.read_csv(file)
                    dataframes.append(df)
                    target_len += len(df)
                print(f"Total number of generated segments: {target_len}")

                merged_df = pd.concat(dataframes, ignore_index=True)
                merged_df.drop_duplicates(keep="first", inplace=True)
                print(f"Total number of generated segments after duplication removal: {len(merged_df)}")

                os.makedirs(self.output_folder, exist_ok=True)
                merged_df.to_csv(os.path.join(self.output_folder, file_type), index=False)
                merged_df.to_parquet(os.path.join(self.output_folder, file_type.replace("csv", "parquet")), index=False)

    def __call__(self):
        """Process the VAD system output"""
        files = self._retrieve_output()
        self._merge_vad_output(files)
        print("\nDone.")
