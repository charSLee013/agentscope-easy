# -*- coding: utf-8 -*-
"""Real runtime validation for the browser fallback public API."""
from __future__ import annotations

import json
from pathlib import Path
import time

from agentscope.browser import BrowserPageService


URLS = [
    (
        "openai_agents_guide",
        "https://openai.com/business/guides-and-resources/"
        "a-practical-guide-to-building-ai-agents/",
    ),
    (
        "anthropic_multi_agent",
        "https://www.anthropic.com/engineering/"
        "built-multi-agent-research-system",
    ),
]


def main() -> None:
    """Fetch real webpages and persist a machine-readable summary."""
    summary_path = (
        Path(__file__).resolve().parents[2]
        / "artifacts"
        / "browser_runtime_validation"
        / "summary.json"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    service = BrowserPageService()
    started = time.perf_counter()
    records = []
    for label, url in URLS:
        fetch_started = time.perf_counter()
        result = service.fetch_page(url)
        records.append(
            {
                "label": label,
                "url": url,
                "status_code": result.status_code,
                "fetch_mode": result.fetch_mode,
                "backend": result.backend,
                "challenge_detected": result.challenge_detected,
                "title": result.title,
                "text_preview": result.text[:240],
                "elapsed_s": round(time.perf_counter() - fetch_started, 3),
            },
        )

    payload = {
        "ok": True,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "total_elapsed_s": round(time.perf_counter() - started, 3),
        "records": records,
    }
    summary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(summary_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
