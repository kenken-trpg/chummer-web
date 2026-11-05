"""Reads the walkthrough's narration with Irodori-TTS, loading the model once.

The lines come from ``record-walkthrough.mjs --narration``; the clips go where
``record-walkthrough.mjs --voice-dir`` looks for them. Run it inside an
Irodori-TTS checkout's environment (https://github.com/Aratako/Irodori-TTS),
which brings torch and the model code:

    uv run --project ~/mydevelop/Irodori-TTS python scripts/irodori_narration.py \\
        narration.jsonl voices/ --caption "落ち着いた女性の声で、はっきりと読み上げてください。"

With ``--candidates N`` each line is read N times (``<name>_001.wav`` ...);
copy the take you like to ``<name>.wav``. ``--only`` re-reads some lines and
leaves the rest alone, e.g. after adding a word to READINGS.irodori.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

VOICE_DESIGN = "Aratako/Irodori-TTS-500M-v2-VoiceDesign"
BASE = "Aratako/Irodori-TTS-500M-v2"


def read_lines(path: Path, only: set[str]) -> list[dict[str, str]]:
    lines = [json.loads(row) for row in path.read_text(encoding="utf-8").splitlines() if row]
    unknown = only - {line["name"] for line in lines}
    if unknown:
        raise SystemExit(f"not in {path}: {', '.join(sorted(unknown))}")
    return [line for line in lines if not only or line["name"] in only]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("narration", type=Path, help="JSON Lines from --narration")
    parser.add_argument("out", type=Path, help="directory for <name>.wav")
    voice = parser.add_mutually_exclusive_group(required=True)
    voice.add_argument("--caption", help=f"describe the voice ({VOICE_DESIGN})")
    voice.add_argument("--ref-wav", help=f"clone the voice in this clip ({BASE})")
    parser.add_argument("--checkpoint", help="Hugging Face repo id or local file")
    parser.add_argument("--seed", type=int, default=1, help="same seed, same take")
    parser.add_argument("--candidates", type=int, default=1)
    parser.add_argument("--num-steps", type=int, default=40)
    parser.add_argument("--device", default=None, help="mps, cuda or cpu (default: auto)")
    parser.add_argument("--only", default="", help="comma-separated names, e.g. 05-attributes")
    args = parser.parse_args()

    only = {name.strip() for name in args.only.split(",") if name.strip()}
    lines = read_lines(args.narration, only)
    args.out.mkdir(parents=True, exist_ok=True)

    # imported here: the module only exists inside the Irodori-TTS environment
    rt: Any = importlib.import_module("irodori_tts.inference_runtime")
    hub: Any = importlib.import_module("huggingface_hub")
    checkpoint = args.checkpoint or (VOICE_DESIGN if args.caption else BASE)
    if not Path(checkpoint).is_file():
        checkpoint = hub.hf_hub_download(repo_id=checkpoint, filename="model.safetensors")
    device = args.device or rt.default_runtime_device()
    runtime = rt.InferenceRuntime.from_key(
        rt.RuntimeKey(checkpoint=checkpoint, model_device=device, codec_device=device)
    )
    for line in lines:
        result = runtime.synthesize(
            rt.SamplingRequest(
                text=line["text"],
                caption=args.caption,
                ref_wav=args.ref_wav,
                no_ref=args.ref_wav is None,
                num_candidates=args.candidates,
                num_steps=args.num_steps,
                seconds=30.0,
                seed=args.seed,
            ),
            log_fn=None,
        )
        if args.candidates == 1:
            rt.save_wav(args.out / f"{line['name']}.wav", result.audio, result.sample_rate)
        else:
            for i, audio in enumerate(result.audios, start=1):
                rt.save_wav(args.out / f"{line['name']}_{i:03d}.wav", audio, result.sample_rate)
        print(f"{line['name']}: {line['text']}", flush=True)


if __name__ == "__main__":
    main()
