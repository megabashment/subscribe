import logging

logger = logging.getLogger(__name__)


def detect_device(override: str | None = None) -> str:
    if override and override != "auto":
        logger.info("Device override: %s", override)
        return override

    try:
        import torch

        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    except ImportError:
        device = "cpu"

    logger.info("Detected device: %s", device)
    return device
