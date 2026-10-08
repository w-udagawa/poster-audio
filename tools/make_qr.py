"""再生ページの URL から印刷用の QR コード（PNG と SVG）を作る。

使い方:
    python tools/make_qr.py                                  # 既定の URL
    python tools/make_qr.py https://example.github.io/xxx/   # URL を指定

出力: qr/qr.png（印刷用 約1500px）, qr/qr.svg（拡大しても劣化しない）
QR に入るのは URL だけなので、音声を差し替えても QR は作り直さなくてよい。
"""

from __future__ import annotations

import sys
from pathlib import Path

import qrcode
import qrcode.image.svg

DEFAULT_URL = "https://w-udagawa.github.io/poster-audio/"
OUT = Path(__file__).resolve().parent.parent / "qr"


def build(url: str) -> qrcode.QRCode:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    return qr


def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    OUT.mkdir(exist_ok=True)

    qr = build(url)
    modules = qr.modules_count + qr.border * 2
    qr.box_size = max(10, 1500 // modules)
    qr.make_image(fill_color="black", back_color="white").save(OUT / "qr.png")

    qr_svg = build(url)
    qr_svg.make_image(image_factory=qrcode.image.svg.SvgPathImage).save(OUT / "qr.svg")

    print(f"URL: {url}")
    print(f"QR バージョン {qr.version}（{qr.modules_count}x{qr.modules_count}）")
    print(f"→ {OUT / 'qr.png'}\n→ {OUT / 'qr.svg'}")


if __name__ == "__main__":
    main()
