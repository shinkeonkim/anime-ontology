"""자막 파일의 바이트를 텍스트로 디코딩한다. 여러 자막 파서가 공유한다.

한국 팬섭 자막은 UTF-8, CP949/EUC-KR, 드물게 UTF-16(BOM 포함)까지 섞여 있다.
UTF-16 파일을 UTF-8로 잘못 디코딩하면 예외 없이 널 바이트가 섞인 문자열이 되어
버릴 수 있으므로(파싱은 "성공"하지만 결과가 텅 빔), BOM을 먼저 확인한다.
"""

from __future__ import annotations

_ENCODING_CANDIDATES = ("utf-8", "cp949", "euc-kr")


def decode_subtitle_bytes(raw: bytes) -> str:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")

    for encoding in _ENCODING_CANDIDATES:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    return raw.decode("utf-8", errors="replace")
