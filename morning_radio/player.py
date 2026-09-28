from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .audio import duration_seconds
from .models import EpisodePlan, SourceDocument


def _fmt_duration(seconds: float | None) -> str:
    if seconds is None:
        return ""
    minutes = int(seconds // 60)
    secs = int(round(seconds % 60))
    return f"{minutes}:{secs:02d}"


def build_player_site(
    plan: EpisodePlan,
    sources: list[SourceDocument],
    mp3_path: Path,
    public_dir: Path,
) -> Path:
    audio_dir = public_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    target_audio = audio_dir / "today.mp3"
    shutil.copy2(mp3_path, target_audio)

    duration = duration_seconds(target_audio)
    metadata = {
        "date": plan.date,
        "title": plan.title,
        "teaser": plan.teaser,
        "duration_seconds": duration,
        "watchpoints": plan.watchpoints,
        "sources": [
            {"source": item.source, "status": item.status, "captured_at": item.captured_at.isoformat()}
            for item in sources
        ],
    }
    (public_dir / "episode.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    segment_items = "".join(
        f"<li><strong>{html.escape(segment.title)}</strong></li>" for segment in plan.segments
    )
    watch_items = "".join(f"<li>{html.escape(item)}</li>" for item in plan.watchpoints)
    duration_label = _fmt_duration(duration)
    page = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#111827">
<title>{html.escape(plan.title)} · MORNING RADIO</title>
<style>
:root {{ color-scheme: dark; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
body {{ margin:0; background:#0b0f19; color:#f8fafc; }}
main {{ max-width:720px; margin:0 auto; padding:40px 20px 80px; }}
.eyebrow {{ color:#94a3b8; font-size:12px; letter-spacing:.14em; font-weight:700; }}
h1 {{ font-size:34px; line-height:1.16; margin:10px 0 12px; }}
.teaser {{ color:#cbd5e1; font-size:17px; line-height:1.7; }}
.player {{ margin:28px 0; padding:20px; background:#151b2a; border-radius:18px; }}
audio {{ width:100%; }}
.meta {{ color:#94a3b8; font-size:13px; margin-top:10px; }}
section {{ margin-top:34px; }}
h2 {{ font-size:17px; }}
li {{ margin:10px 0; line-height:1.55; color:#dbe4f0; }}
.note {{ margin-top:34px; color:#64748b; font-size:12px; line-height:1.6; }}
</style>
</head>
<body>
<main>
<div class="eyebrow">MORNING RADIO · {html.escape(plan.date)}</div>
<h1>{html.escape(plan.title)}</h1>
<p class="teaser">{html.escape(plan.teaser)}</p>
<div class="player">
<audio controls preload="metadata" playsinline src="audio/today.mp3"></audio>
<div class="meta">{html.escape(duration_label)} · AI-generated two-host podcast</div>
</div>
<section><h2>오늘 이야기</h2><ol>{segment_items}</ol></section>
<section><h2>오늘 볼 것</h2><ul>{watch_items}</ul></section>
<p class="note">WORLD BRIEFING, MORNING BRIEFING, PTIS 결과를 바탕으로 생성됩니다. 사실과 AI의 해석·가설은 구분해서 말하도록 설계되어 있습니다.</p>
</main>
</body>
</html>"""
    index_path = public_dir / "index.html"
    index_path.write_text(page, encoding="utf-8")
    return index_path
