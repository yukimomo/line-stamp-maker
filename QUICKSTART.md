# LINE Stamp Maker - Quick Start Guide

## インストール（実行）

```bash
# パッケージをインストール
pip install -r requirements.txt

# または手動で一個ずつ
pip install pillow mediapipe numpy opencv-python "typer[all]" pydantic python-dotenv
```

## 基本的な使い方

### ステップ 1: 画像を準備

`photos/` フォルダに JPG/PNG 画像を入れます。

```
line-stamp-maker/
└── photos/
    ├── photo1.jpg
    ├── photo2.jpg
    └── photo3.jpg
```

### ステップ 2: マッピングファイルを作成

`mapping.csv` を編集して、各画像に対応するテキストを指定します。

```csv
filename,text
photo1.jpg,こんにちは
photo2.jpg,元気ですか？
photo3.jpg,今日も頑張ろう
```

**テキストについて**:
- 最大 2 行まで対応（改行で区切る）
- 改行で複数行指定可能：`Line1\nLine2`

### ステップ 3: スタンプを生成

```bash
python -m line_stamp_maker process
```

### ステップ 4: 出力を確認

`out/` フォルダに結果が保存されます。

```
out/
├── stickers/
│   ├── 01.png        ← メインスタンプ
│   ├── 02.png
│   └── 03.png
├── main_01.png       ← ストア表示用 240x240
├── main_02.png
├── tab_01.png        ← タブアイコン 96x74
├── tab_02.png
├── upload.zip        ← LINE Creators Market 用
└── results.json      ← 処理結果
```

## よくあるオプション

### 1. 顔検出を無効にする

```bash
python -m line_stamp_maker process --no-face-detection
```

→ 背景を保持したい場合や、顔が自動クロップされたくない場合

### 2. セグメンテーション（背景透明化）を無効にする

```bash
python -m line_stamp_maker process --no-segmentation
```

→ 背景を含めてスタンプにしたい場合

### 3. カスタムサイズ

```bash
python -m line_stamp_maker process \
  --sticker-width 300 \
  --sticker-height 300 \
  --border 12 \
  --font-size 32
```

### 4. 影を無効にする

```bash
python -m line_stamp_maker process --no-shadow
```

### 5. ZIP を作成しない

```bash
python -m line_stamp_maker process --no-zip
```

## 機能の詳細

### 📸 画像処理パイプライン

1. **EXIF 回転補正** - スマートフォンの縦向き撮影に対応
2. **顔検出とクロップ** - 顔を中心に自動クロップ（失敗時は中央クロップ）
3. **人物セグメンテーション** - MediaPipe で背景を透明化
4. **マスク整形** - モルフォロジ演算とぼかしで自然なエッジ
5. **白ふち取り** - 8px の白枠を追加（カスタマイズ可）
6. **影エフェクト** - 軽い影で奥行き表現（オプション）
7. **テキスト描画** - 下部に帯囲いと縁取り文字で焼き込み
8. **サイズ変換** - 3 種類のサイズで出力

### 📋 出力仕様

| 種類 | サイズ | フォーマット | 用途 |
|------|--------|----------|------|
| **Sticker** | 最大 370x320 | PNG 透過 | メインスタンプ |
| **Main** | 240x240 | PNG 透過 | ストア表示 |
| **Tab** | 96x74 | PNG 透過 | タブアイコン |

## 実行例

### 例 1: シンプルな使用

```bash
# デフォルト設定で実行
python -m line_stamp_maker process
```

### 例 2: カスタマイズした実行

```bash
python -m line_stamp_maker process \
  --photos ./myPhotos \
  --mapping ./config.csv \
  --output ./results \
  --border 10 \
  --font-size 28
```

### 例 3: 高品質モード

```bash
python -m line_stamp_maker process \
  --sticker-width 370 \
  --sticker-height 320 \
  --border 8 \
  --font-size 24
```

### 例 4: シンプルモード

```bash
python -m line_stamp_maker process \
  --no-face-detection \
  --no-shadow
```

## トラブルシューティング

### ❌ "File not found" エラー

- `photos/` フォルダが存在するか確認
- `mapping.csv` のファイル名が正確か確認

### ❌ MediaPipe エラー

```bash
pip install --upgrade mediapipe
```

### ❌ "No faces detected"

- `--no-face-detection` で顔検出をスキップ
- 画像に人物が写っているか確認

### ❌ テキストが見えない

- フォントサイズを大きくする：`--font-size 32`
- 背景の `--no-shadow` を試す

## 出力ファイル確認

```bash
# Windows
explorer out\

# macOS
open out/

# Linux
nautilus out/
```

## LINE Creator Market への提出

1. `out/upload.zip` をダウンロード
2. LINE Creators Market にログイン
3. スタンプを申請

## 次のステップ

- より多くの画像を処理してスタンプセットを作成
- テキストのスタイルをカスタマイズ
- 複数のセットを同時に処理

## ヘルプ

```bash
# ツール情報
python -m line_stamp_maker info

# コマンドヘルプ
python -m line_stamp_maker process --help

# 詳細ドキュメント
cat README.md
```

---

**楽しいスタンプ作成を！** 🎨 🎭 ✨
