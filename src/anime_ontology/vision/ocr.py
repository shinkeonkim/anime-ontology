"""특정 시점의 프레임을 캡처해 화면에 찍힌 텍스트를 OCR로 읽는다.

`pip install -e ".[vision]"`로 pytesseract/Pillow를 설치하고, 시스템에 tesseract(+
한국어 언어팩)가 있어야 한다.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from anime_ontology.vision.models import VisualCue


class OcrError(RuntimeError):
    """프레임 캡처 또는 OCR이 실패했을 때 발생한다."""


def _capture_frame(video_path: Path, timestamp_ms: int, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{timestamp_ms / 1000:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise OcrError(f"프레임 캡처 실패({video_path}, {timestamp_ms}ms): {result.stderr[-500:]}")


def extract_text_at(video_path: Path, timestamp_ms: int, *, lang: str = "kor+eng") -> str:
    """timestamp_ms 시점의 프레임에서 OCR로 텍스트를 읽는다."""

    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise OcrError(
            'pytesseract/Pillow가 설치되어 있지 않습니다. `uv pip install -e ".[vision]"`로 설치하세요.'
        ) from exc

    with tempfile.TemporaryDirectory() as tmp_dir:
        frame_path = Path(tmp_dir) / "frame.png"
        _capture_frame(video_path, timestamp_ms, frame_path)
        try:
            text = pytesseract.image_to_string(Image.open(frame_path), lang=lang)
        except pytesseract.TesseractNotFoundError as exc:
            raise OcrError(
                "tesseract 실행 파일을 찾을 수 없습니다. 시스템에 tesseract(+kor 언어팩)를 설치하세요."
            ) from exc

    return text.strip()


def detect_onscreen_text(
    video_path: Path, timestamps_ms: list[int], *, lang: str = "kor+eng", min_chars: int = 2
) -> list[VisualCue]:
    """여러 시점에서 OCR을 돌려, 의미 있는 길이의 텍스트만 VisualCue로 반환한다."""

    cues = []
    for timestamp_ms in timestamps_ms:
        cleaned = " ".join(extract_text_at(video_path, timestamp_ms, lang=lang).split())
        if len(cleaned) >= min_chars:
            cues.append(VisualCue(timestamp_ms=timestamp_ms, text=cleaned))
    return cues
