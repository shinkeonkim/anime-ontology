"""자막이 없는 영상에서 음성인식(STT)으로 대사를 확보하는 패키지."""

from anime_ontology.transcription.audio import extract_audio
from anime_ontology.transcription.base import TranscriptionProvider, TranscriptionProviderError
from anime_ontology.transcription.cache import load_cached_transcript, save_transcript_cache
from anime_ontology.transcription.proxy import TranscriptionProviderProxy

__all__ = [
    "TranscriptionProvider",
    "TranscriptionProviderError",
    "TranscriptionProviderProxy",
    "extract_audio",
    "load_cached_transcript",
    "save_transcript_cache",
]
