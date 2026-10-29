from __future__ import annotations

import json
import urllib.parse
import urllib.request

from .common import CaptureRun, run_single_capture


def capture(run: CaptureRun) -> dict[str, int]:
    api_state = run.state.setdefault("api", {})
    page = 1
    limit = 1_000
    count = 0
    previous_sequence = int(api_state.get("last_sequence", 0))
    maximum_sequence = previous_sequence
    output_dir = run.landing / "api" / "shipments"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"shipments_{run.run_id}.jsonl"

    # Gravação atômica: as páginas são escritas primeiro em um arquivo temporário,
    # fora da Landing. Se a API cair no meio da paginação, nenhum arquivo parcial
    # chega à Landing e a nova tentativa (retry do orquestrador) recomeça da mesma
    # watermark sem duplicar entregas.
    temp_dir = run.lake / "control" / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / output_path.name

    try:
        with temp_path.open("w", encoding="utf-8") as stream:
            while True:
                parameters = {
                    "page": page,
                    "limit": limit,
                    "after_sequence": previous_sequence,
                }
                url = f"{run.api_url.rstrip('/')}/shipments?{urllib.parse.urlencode(parameters)}"
                with urllib.request.urlopen(url, timeout=30) as response:
                    payload = json.load(response)
                for item in payload["items"]:
                    stream.write(json.dumps(item, ensure_ascii=False) + "\n")
                    source_sequence = int(
                        item.get("source_sequence")
                        or item["shipment_id"].rsplit("-", 1)[-1]
                    )
                    maximum_sequence = max(maximum_sequence, source_sequence)
                    count += 1
                if not payload["has_more"]:
                    break
                page += 1
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise

    if count == 0:
        temp_path.unlink()
    else:
        temp_path.replace(output_path)  # o arquivo aparece na Landing completo, de uma vez
        if maximum_sequence:
            api_state["last_sequence"] = maximum_sequence
    return {"rows": count, "pages": page if count else 0}


def main() -> None:
    run_single_capture(
        "api",
        capture,
        "Captura incremental das entregas pela API paginada.",
        api_url_required=True,
    )


if __name__ == "__main__":
    main()