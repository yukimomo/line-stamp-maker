# LINE Stamp Maker

LINE スタンプを自動作成する Python CLI ツール。顔検出、人物セグメンテーション、テキスト処理により、写真から高品質なスタンプを生成します。

## 特徴

- 🎨 **顔検出とクロップ**: 顔を自動検出して最適に配置
- 🎭 **人物セグメンテーション**: MediaPipe で背景を透明化
- ✂️ **白ふち取り**: 標準 8px のカスタマイズ可能な白枠
- 🌑 **影エフェクト**: 薄い影で奥行き表現（オプション）
- 📝 **テキスト描画**: 2 行までのテキストを下部に帯囲いで焼き込み
- 📦 **自動ZIP生成**: LINE Creators Market 用の upload.zip を自動作成
- 🔄 **EXIF 回転補正**: 自動的に正しい向きに回転

## 仕様

### 出力画像フォーマット

| 種類 | サイズ | フォーマット | 用途 |
|------|--------|----------|------|
| Sticker | 最大 370x320 | PNG 透過 | メイン画像 |
| Main | 240x240 | PNG 透過 | ストア表示 |
| Tab | 96x74 | PNG 透過 | タブアイコン |

### ディレクトリ構造

```
line-stamp-maker/
├── photos/              # 入力画像フォルダ
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── ...
├── mapping.csv         # ファイル名とテキストの対応
├── out/               # 出力フォルダ
│   ├── stickers/
│   │   ├── 01.png
│   │   ├── 02.png
│   │   └── ...
│   ├── main_01.png
│   ├── main_02.png
│   ├── tab_01.png
│   ├── tab_02.png
│   ├── upload.zip     # LINE Creators Market 用
│   └── results.json
└── requirements.txt
```

## インストール

### 前提条件

- Python 3.11 以上
- pip

### セットアップ

```bash
# リポジトリをクローン
cd line-stamp-maker

# 必要なパッケージをインストール
pip install -r requirements.txt
```

## 使用方法

### 基本的な使用

```bash
python -m line_stamp_maker process \
  --photos photos \
  --mapping mapping.csv \
  --output out
```

### mapping.csv の形式

```csv
filename,text
photo1.jpg,こんにちは
photo2.jpg,元気ですか？
photo3.jpg,Line1
Line2
```

- `filename`: photos/ フォルダ内のファイル名
- `text`: スタンプに描画するテキスト（最大 2 行、改行で区切る）

### コマンドラインオプション

```bash
python -m line_stamp_maker process [OPTIONS]

Options:
  --photos PATH, -p PATH          入力画像フォルダ [default: photos]
  --mapping PATH, -m PATH         マッピング CSV ファイル [default: mapping.csv]
  --output PATH, -o PATH          出力フォルダ [default: out]
  --sticker-width INTEGER         ステッカー最大幅 [default: 370]
  --sticker-height INTEGER        ステッカー最大高さ [default: 320]
  --border INTEGER, -b INTEGER    白ふち幅（ピクセル） [default: 8]
  --font-size INTEGER, -f INT     フォントサイズ [default: 24]
  --no-segmentation              人物セグメンテーションをスキップ
  --no-face-detection            顔検出をスキップ
  --no-shadow                    影効果を無効化
  --zip / --no-zip               ZIP ファイルの作成 [default: --zip]
  --help                         ヘルプを表示
```

### 高度な使用例

```bash
# 顔検出なし、シャドウなし
python -m line_stamp_maker process \
  --no-face-detection \
  --no-shadow \
  --output out

# カスタムサイズ、大きいテキスト
python -m line_stamp_maker process \
  --sticker-width 300 \
  --sticker-height 300 \
  --font-size 32 \
  --border 12

# セグメンテーション無効（背景を保持）
python -m line_stamp_maker process \
  --no-segmentation \
  --output out
```

### 情報表示

```bash
python -m line_stamp_maker info
```

## 画像処理パイプライン

1. **EXIF 回転補正**: 自動的に正しい向きに補正
2. **顔検出と クロップ**: （有効時）顔を検出して最適に配置
3. **中央クロップ**: 顔が見つからない場合は画像中央を使用
4. **人物セグメンテーション**: MediaPipe で背景を透明化
5. **最大成分抽出**: 最も大きいオブジェクトのみを保持
6. **マスク整形**: モルフォロジ演算とぼかしで自然なエッジ
7. **白ふち取り**: 指定ピクセルの白い枠を追加
8. **影エフェクト**: 軽い影を追加（オプション）
9. **テキスト描画**: 下部に帯囲いと縁取り文字で焼き込み
10. **サイズ変換**: Sticker / Main / Tab 用に最適化

## 依存パッケージ

| パッケージ | 用途 |
|-----------|------|
| `pillow` | 画像処理（基本） |
| `mediapipe` | 人物セグメンテーション |
| `numpy` | 数値計算 |
| `opencv-python` | 高度な画像処理、連結成分抽出 |
| `typer` | CLI フレームワーク |
| `pydantic` | 設定管理・バリデーション |
| `python-dotenv` | 環境変数管理（オプション） |

## トラブルシューティング

### MediaPipe のエラー

```
ERROR: Could not load the fast pairwise face detection TFLite model
```

→ バージョンのミスマッチの可能性があります：

```bash
pip install --upgrade mediapipe
```

### 顔が検出されない

- `--no-face-detection` で中央クロップに切り替え
- 背景が複雑な場合、`--no-segmentation` を試す

### テキストが表示されない

- フォントファイルが見つからない場合はデフォルトフォントを使用
- フォントサイズを調整してみてください：`--font-size 20`

### メモリ不足エラー

- 入力画像の解像度を下げる
- バッチ処理の数を減らす

## 出力ファイル

### 成功時の出力

```
out/
├── stickers/
│   ├── 01.png          # ステッカー画像（最大 370x320）
│   ├── 02.png
│   └── ...
├── main_01.png         # ストア表示用 (240x240)
├── main_02.png
├── tab_01.png          # タブアイコン (96x74)
├── tab_02.png
├── upload.zip          # LINE Creators Market 用
└── results.json        # 処理結果サマリー
```

### results.json の例

```json
{
  "photo1.jpg": {
    "status": "success",
    "sticker": "out/stickers/01.png",
    "main": "out/main_01.png",
    "tab": "out/tab_01.png"
  },
  "photo2.jpg": {
    "status": "success",
    "sticker": "out/stickers/02.png",
    "main": "out/main_02.png",
    "tab": "out/tab_02.png"
  }
}
```

## LINE Creators Market への提出

作成した `upload.zip` は以下の構造を持ちます：

```
upload.zip
├── stickers/
│   ├── 01.png
│   ├── 02.png
│   ├── ...
│   └── 40.png        # MAX 40 stickers
├── main.png          # 240x240
└── tab.png           # 96x74
```

このファイルを LINE Creators Market にアップロードできます。

## ローカル処理

🔒 **重要**: このツールは完全にローカルで動作します。

- 外部 API を使用しません
- インターネット接続は不要です
- 画像データはローカルで処理されます
- プライバシー保護されています

## ライセンス

MIT License

## 作成者

LINE Stamp Maker Contributors

## 参考資料

- [LINE Creators Market](https://creators.line.me/)
- [MediaPipe Selfie Segmentation](https://google.github.io/mediapipe/solutions/selfie_segmentation.html)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [OpenCV Documentation](https://docs.opencv.org/)

---

**注**: このツールは個人使用を想定しています。商用利用の際は LINE の利用規約を確認してください。
