# poster-audio

論文ポスターの QR コードから、スマホで合成音声の発表を再生するためのページ。
QR に入っているのは固定の URL だけなので、**音声と原稿はあとから何度でも差し替えられる**（QR の刷り直し不要）。

- 再生ページ: https://w-udagawa.github.io/poster-audio/
- 中身: `docs/`（GitHub Pages で公開）

## 差し替え手順

Claude の普通のチャット（claude.ai）で原稿を作る場合は、[CHAT_INSTRUCTIONS.md](CHAT_INSTRUCTIONS.md) をプロジェクトの指示に貼り付けて使う。

### スマホ・別の PC から（ブラウザだけで完結）
GitHub で https://github.com/w-udagawa/poster-audio を開いて（スマホは GitHub アプリでも可）:

- **原稿を変える**: `docs/script.txt` を開く → 鉛筆アイコンで編集 → 「Commit changes」
  → GitHub 側で自動的に音声が作り直され、2〜3分で QR の先が新しい音声になる
- **タイトル・著者・声・話速を変える**: `docs/meta.json` を同じように編集
  （`voice` / `speed` / `lang` を変えると、その声で作り直される。声の名前は下の「声と話速の変更」を参照）
- **自分の mp3 に差し替える**: `docs` フォルダを開く → 「Add file」→「Upload files」で `audio.mp3` という名前のファイルをアップロード
  → 自動でキャッシュ対策（version 更新）もされる

進み具合は「Actions」タブで見られる（緑のチェックが付けば公開済み）。
音声を作り直したいだけのときは Actions タブ →「publish」→「Run workflow」。

**注意**: ブラウザで変更したあとに PC で作業するときは、先に `git pull` すること。

### PC で原稿から音声を作り直す
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

### PC で自分の mp3 に差し替える
1. `docs/audio.mp3` に上書きする（ファイル名は `audio.mp3` のまま）
2. commit して push する（version 更新は GitHub 側で自動）

この場合、長さが合わなくなるので段落のハイライトは自動で切れて、原稿の表示だけになる。

## 声と話速の変更

`docs/meta.json` の `voice` / `speed` / `lang` が既定値。コマンドで一時的に変えることもできる:

```
python tools/tts.py --list-voices              # 声の一覧
python tools/tts.py --voice am_michael         # 男性（米）
python tools/tts.py --voice bf_emma --lang en-gb   # 女性（英）
python tools/tts.py --speed 0.9                # 少しゆっくり
```

声の名前の先頭2文字: `a`=米国英語 / `b`=英国英語、`f`=女性 / `m`=男性。既定は `af_heart`。
コマンドで指定した声は meta.json には残らないので、GitHub 側で作り直すと meta.json の声に戻る。
ずっと使う声は meta.json に書くこと。

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
