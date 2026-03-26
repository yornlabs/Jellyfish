"""Tasks for the skills runtime."""

from app.core.tasks.video_generation_tasks import (
    ProviderConfig,
    VideoGenerationInput,
    VideoGenerationResult,
    VideoGenerationTask,
)
from app.core.tasks.image_generation_tasks import (
    ImageGenerationInput,
    ImageGenerationResult,
    ImageGenerationTask,
)

__all__ = [
    "ProviderConfig",
    "VideoGenerationInput",
    "VideoGenerationResult",
    "VideoGenerationTask",
    "ImageGenerationInput",
    "ImageGenerationResult",
    "ImageGenerationTask",
]
