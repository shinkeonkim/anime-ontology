"""ffmpeg로 영상에서 STT용 오디오(16kHz mono wav)를 추출한다."""

from __future__ import annotations

import subprocess
from pathlib import Path


class AudioExtractionError(RuntimeError):
    """ffmpeg 오디오 추출이 실패했을 때 발생한다."""


def extract_audio(video_path: Path, output_path: Path) -> Path:
    """video_path의 오디오 트랙을 output_path(wav, 16kHz mono)로 추출한다."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-vn",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise AudioExtractionError(f"ffmpeg 오디오 추출 실패({video_path}): {result.stderr[-2000:]}")
    return output_path
