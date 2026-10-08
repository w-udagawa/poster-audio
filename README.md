# poster-audio

論文ポスターの QR コードから、スマホで合成音声の発表を再生するためのページ。
QR に入っているのは固定の URL だけなので、**音声と原稿はあとから何度でも差し替えられる**（QR の刷り直し不要）。

- 再生ページ: https://w-udagawa.github.io/poster-audio/
- 中身: `docs/`（GitHub Pages で公開）

## 差し替え手順

### 原稿から音声を作り直す（通常はこちら）
1. `docs/script.txt` を書き換える（空行で段落を区切る。段落ごとにページ上でハイライトされる）
2. 必要なら `docs/meta.json` の `title` / `authors` / `affiliation` / `venue` を書き換える
3. 音声を合成する
   ```
   python tools/tts.py
   ```
4. 公開する（1〜2分で反映）
   ```
   git add -A && git commit -m "update audio" && git push
   ```

### 自分で用意した mp3 に差し替える
1. `docs/audio.mp3` に上書きする（ファイル名は `audio.mp3` のまま）
2. `docs/meta.json` の `version` の数字を 1 増やす（スマホのキャッシュ対策）
3. commit して push する

この場合、長さが合わなくなるので段落のハイライトは自動で切れて、原稿の表示だけになる。

## 声と話速の変更

```
python tools/tts.py --list-voices              # 声の一覧
python tools/tts.py --voice am_michael         # 男性（米）
python tools/tts.py --voice bf_emma --lang en-gb   # 女性（英）
python tools/tts.py --speed 0.9                # 少しゆっくり
```

声の名前の先頭2文字: `a`=米国英語 / `b`=英国英語、`f`=女性 / `m`=男性。既定は `af_heart`。

## QR コード

```
python tools/make_qr.py
```

`qr/qr.png`（印刷用）と `qr/qr.svg`（拡大しても劣化しない）ができる。ポスターには 3cm 角以上で貼るのがおすすめ。

## 初回セットアップ（別の PC で使う場合）

```
pip install -r requirements.txt
```

ffmpeg が必要。モデル（約 350MB、git には含めない）を `tools/models/` に置く:
- https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
- https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin

ローカルでの確認: `python -m http.server -d docs` → http://localhost:8000/
