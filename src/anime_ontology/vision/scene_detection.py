"""ffmpeg의 scene 필터로 장면 전환 시점을 찾는다.

별도 컴퓨터비전 라이브러리(OpenCV 등) 없이, 오디오 추출에도 쓰는 ffmpeg 하나로
"기본" 수준의 장면 분석을 하기 위한 선택이다.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_PTS_TIME = re.compile(r"pts_time:([\d.]+)")


class SceneDetectionError(RuntimeError):
    """ffmpeg 장면 감지가 실패했을 때 발생한다."""


def detect_scene_changes(video_path: Path, *, threshold: float = 0.3, max_scenes: int = 200) -> list[int]:
    """장면이 바뀌는 시점(ms) 목록을 시간순으로 반환한다."""

    command = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vf",
        f"select='gt(scene,{threshold})',showinfo",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(command, capture_output=True, text=True)

    timestamps_ms = [int(float(match) * 1000) for match in _PTS_TIME.findall(result.stderr)]
    if not timestamps_ms and result.returncode != 0:
        raise SceneDetectionError(f"ffmpeg 장면 감지 실패({video_path}): {result.stderr[-2000:]}")

    return timestamps_ms[:max_scenes]
