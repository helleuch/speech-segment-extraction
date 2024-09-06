import datetime as dt
import wave


def get_audio_duration(file: str) -> float:
    """
    Get the duration of an audio file.

    :param file: Path to the audio file.
    :return: Duration of the audio file in seconds.
    """
    with wave.open(file, 'rb') as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
        duration = frames / float(rate)
    return duration


def human_readable_duration(seconds: int) -> str:
    """
    Convert a duration in seconds into a human-readable format limited to hours, minutes, and seconds.

    Args:
        seconds (int): The duration in seconds.

    Returns:
        str: The duration formatted as 'X hours, Y minutes, Z seconds'.
    """
    # Convert seconds to a timedelta object
    delta = dt.timedelta(seconds=seconds)

    # Extract hours, minutes, and seconds
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # Format the output
    readable_duration = f"{hours} hours, {minutes} minutes, {seconds} seconds"
    return readable_duration
