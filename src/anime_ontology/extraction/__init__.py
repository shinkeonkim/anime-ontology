"""자막 -> 개체/관계 추출."""

from anime_ontology.extraction.cache import load_cached_extraction, save_extraction_cache
from anime_ontology.extraction.extractor import ExtractionError, extract_episode
from anime_ontology.extraction.schema import ExtractionResult

__all__ = [
    "ExtractionError",
    "ExtractionResult",
    "extract_episode",
    "load_cached_extraction",
    "save_extraction_cache",
]
