from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Model sizes in GB (approximate download size)
MODEL_INFO: dict[str, dict] = {
    "tiny":     {"size_gb": 0.15, "repo": "Systran/faster-whisper-tiny"},
    "base":     {"size_gb": 0.29, "repo": "Systran/faster-whisper-base"},
    "small":    {"size_gb": 0.97, "repo": "Systran/faster-whisper-small"},
    "medium":   {"size_gb": 3.1,  "repo": "Systran/faster-whisper-medium"},
    "large-v3": {"size_gb": 6.2,  "repo": "Systran/faster-whisper-large-v3"},
}

HF_CACHE = Path.home() / ".cache" / "huggingface" / "hub"


def _is_cached(repo: str) -> bool:
    """Check if a HuggingFace repo snapshot is fully cached locally."""
    folder = HF_CACHE / f"models--{repo.replace('/', '--')}"
    if not folder.exists():
        return False
    snapshots = folder / "snapshots"
    if not snapshots.exists():
        return False
    # At least one snapshot directory with .bin/.ct2 files → cached
    for snap in snapshots.iterdir():
        files = list(snap.iterdir())
        if any(f.suffix in {".bin", ".ct2", ".json"} for f in files):
            return True
    return False


def _cached_size_gb(repo: str) -> float | None:
    """Return actual size on disk in GB, or None if not cached."""
    folder = HF_CACHE / f"models--{repo.replace('/', '--')}"
    if not folder.exists():
        return None
    total = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file())
    return round(total / 1_073_741_824, 2)


@router.get("/models")
async def list_models() -> JSONResponse:
    result = {}
    for name, info in MODEL_INFO.items():
        cached = _is_cached(info["repo"])
        result[name] = {
            "cached": cached,
            "size_gb": info["size_gb"],
            "disk_gb": _cached_size_gb(info["repo"]) if cached else None,
        }
    return JSONResponse(result)
