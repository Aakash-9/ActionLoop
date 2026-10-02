from functools import lru_cache

from faster_whisper import WhisperModel

from .config import settings


@lru_cache(maxsize=1)
def _model() -> WhisperModel:
    return WhisperModel(settings.whisper_model_size, compute_type="int8")


def transcribe(audio_path: str) -> str:
    segments, _ = _model().transcribe(audio_path)
    return " ".join(segment.text.strip() for segment in segments)
