"""docs/script.txt を Kokoro (ONNX) で英語音声にして docs/audio.mp3 を作る。

使い方:
    python tools/tts.py                       # 既定の声 af_heart, 速度 1.0
    python tools/tts.py --voice am_michael --speed 0.95
    python tools/tts.py --list-voices

script.txt は空行で段落を区切る。段落の間には --pause 秒の無音が入る。
実行後に docs/meta.json の version を +1 し（スマホ側のキャッシュ回避用）、
段落ごとの開始秒を書き込む（再生ページのハイライト用）。
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
MODELS = Path(__file__).resolve().parent / "models"
MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"

logger = logging.getLogger("tts")


def load_kokoro():
    from kokoro_onnx import Kokoro

    model = MODELS / "kokoro-v1.0.onnx"
    voices = MODELS / "voices-v1.0.bin"
    missing = [p.name for p in (model, voices) if not p.exists()]
    if missing:
        sys.exit(
            f"モデルがありません: {', '.join(missing)}\n"
            f"{MODEL_URL}/ から tools/models/ にダウンロードしてください（README 参照）"
        )
    return Kokoro(str(model), str(voices))


def read_paragraphs(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    paragraphs = [" ".join(p.split()) for p in text.split("\n\n")]
    return [p for p in paragraphs if p]


def update_meta(meta_path: Path, starts: list[float], duration: float) -> int:
    """version を +1 し、段落ごとの開始秒と全体の長さを書き込む。

    再生ページはこれで「今読んでいる段落」をハイライトする。
    mp3 を手で差し替えて長さが合わなくなった場合、ページ側でハイライトを自動で無効にする。
    """
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta["version"] = int(meta.get("version", 0)) + 1
    meta["duration"] = round(duration, 2)
    meta["segments"] = [round(s, 2) for s in starts]
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta["version"]


def mark_manual_audio(meta_path: Path) -> int:
    """mp3 を手で差し替えたとき用。version を +1 し、合わなくなった段落の開始秒を消す。"""
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta["version"] = int(meta.get("version", 0)) + 1
    meta.pop("duration", None)
    meta.pop("segments", None)
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta["version"]


def main() -> None:
    meta_path = DOCS / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

    # 声・話速・言語は meta.json の値を既定にする（ブラウザで meta.json を編集するだけで変えられるように）
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--script", type=Path, default=DOCS / "script.txt")
    parser.add_argument("--out", type=Path, default=DOCS / "audio.mp3")
    parser.add_argument("--voice", default=meta.get("voice", "af_heart"), help="声の名前（--list-voices で一覧）")
    parser.add_argument("--speed", type=float, default=float(meta.get("speed", 1.0)), help="話速 0.5〜2.0")
    parser.add_argument("--lang", default=meta.get("lang", "en-us"), help="en-us（米）/ en-gb（英）")
    parser.add_argument("--pause", type=float, default=0.6, help="段落間の無音（秒）")
    parser.add_argument("--bitrate", default="80k", help="mp3 のビットレート")
    parser.add_argument("--list-voices", action="store_true")
    parser.add_argument("--manual-audio", action="store_true", help="合成せず、手で差し替えた mp3 用に meta.json だけ更新する")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")

    if args.manual_audio:
        logger.info("手動差し替えの mp3 として meta.json を更新（version=%d）", mark_manual_audio(meta_path))
        return

    # 合成に必要なライブラリはここで読み込む（--manual-audio は依存なしで動くように）
    import numpy as np
    import soundfile as sf

    # phonemizer が段落ごとに出す "words count mismatch" は読み上げに影響しないので抑える
    # （phonemizer は呼ばれるたびに自分のロガーのレベルを戻すので、ルートのハンドラで落とす）
    for handler in logging.getLogger().handlers:
        handler.addFilter(lambda r: not (r.name.startswith("phonemizer") and r.levelno < logging.ERROR))
    kokoro = load_kokoro()
    logger.info("声=%s 話速=%.2f 言語=%s", args.voice, args.speed, args.lang)

    if args.list_voices:
        print("\n".join(sorted(kokoro.get_voices())))
        return

    paragraphs = read_paragraphs(args.script)
    if not paragraphs:
        sys.exit(f"原稿が空です: {args.script}")

    chunks: list[np.ndarray] = []
    starts: list[float] = []
    sample_rate = 24000
    for i, para in enumerate(paragraphs, 1):
        logger.info("合成中 %d/%d（%d文字）", i, len(paragraphs), len(para))
        samples, sample_rate = kokoro.create(para, voice=args.voice, speed=args.speed, lang=args.lang)
        starts.append(sum(len(c) for c in chunks) / sample_rate)
        chunks.append(samples)
        if i < len(paragraphs):
            chunks.append(np.zeros(int(sample_rate * args.pause), dtype=samples.dtype))
    audio = np.concatenate(chunks)

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "out.wav"
        sf.write(wav, audio, sample_rate)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-ac", "1", "-b:a", args.bitrate, str(args.out)],
            check=True,
        )

    duration = len(audio) / sample_rate
    version = update_meta(meta_path, starts, duration)
    logger.info("書き出し完了: %s（%.1f秒, version=%d）", args.out, duration, version)


if __name__ == "__main__":
    main()
