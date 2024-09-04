import argparse
import os
import wave

import numpy as np


def stereo_to_mono(input_wav: str, output_wav: str) -> None:
    """
    Convert a stereo WAV file to mono.

    Args:
        input_wav (str): Path to the input stereo WAV file.
        output_wav (str): Path to save the output mono WAV file.

    Raises:
        ValueError: If the input file is not a stereo file.
    """
    with wave.open(input_wav, 'rb') as wav:
        params = wav.getparams()
        n_channels, sampwidth, framerate, n_frames = params[:4]

        if n_channels != 2:
            raise ValueError(f"{input_wav} is not a stereo file")

        frames = wav.readframes(n_frames)
        stereo_audio = np.frombuffer(frames, dtype=np.int16)
        stereo_audio = np.reshape(stereo_audio, (-1, 2))
        mono_audio = np.mean(stereo_audio, axis=1).astype(np.int16)

    with wave.open(output_wav, 'wb') as wav:
        wav.setparams((1, sampwidth, framerate, n_frames // 2, 'NONE', 'not compressed'))
        wav.writeframes(mono_audio.tobytes())


def convert_folder_to_mono(folder_path: str) -> None:
    """
    Convert all stereo WAV files in a folder to mono.

    Args:
        folder_path (str): Path to the folder containing WAV files.
    """
    for filename in os.listdir(folder_path):
        if filename.endswith(".wav"):
            input_wav = os.path.join(folder_path, filename)
            output_wav = os.path.join(folder_path, f"mono_{filename}")
            try:
                stereo_to_mono(input_wav, output_wav)
                print(f"Converted {input_wav} to {output_wav}")
            except ValueError as e:
                print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert stereo WAV files to mono.")
    parser.add_argument('folder_path', type=str, help="Path to the folder containing WAV files.")
    args = parser.parse_args()

    convert_folder_to_mono(args.folder_path)
