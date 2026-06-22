from __future__ import annotations

import json
from pathlib import Path

from subscribe.models import Transcript


def export_json(transcript: Transcript, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "language": transcript.language,
        "duration": transcript.duration,
        "segments": [
            {
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text,
                "words": [
                    {
                        "text": w.text,
                        "start": w.start,
                        "end": w.end,
                        "confidence": w.confidence,
                    }
                    for w in seg.words
                ],
            }
            for seg in transcript.segments
        ],
    }

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path
