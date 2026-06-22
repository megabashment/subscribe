from __future__ import annotations

import os
import psutil
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


def _gpu_stats() -> dict | None:
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        name = pynvml.nvmlDeviceGetName(handle)
        return {
            "name": name if isinstance(name, str) else name.decode(),
            "load": util.gpu,
            "vram_used_mb": mem.used // 1_048_576,
            "vram_total_mb": mem.total // 1_048_576,
        }
    except Exception:
        return None


@router.get("/stats")
async def get_stats() -> JSONResponse:
    proc = psutil.Process(os.getpid())

    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    proc_ram_mb = proc.memory_info().rss // 1_048_576

    return JSONResponse({
        "cpu_load": cpu,
        "ram_used_gb": round(ram.used / 1_073_741_824, 1),
        "ram_total_gb": round(ram.total / 1_073_741_824, 1),
        "proc_ram_mb": proc_ram_mb,
        "gpu": _gpu_stats(),
    })
