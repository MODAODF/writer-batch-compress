# Writer Batch Compress Images

Adapted from [PixCompress](https://extensions.libreoffice.org/en/extensions/show/1034) (Bidouille / O. Morelle), originally a LibreOffice Basic macro. The current version is a complete Python rewrite and performs the actual resampling through `com.sun.star.graphic.GraphicProvider.storeGraphic`.

## Features

- Pressing the toolbar button first runs an *analysis* pass that lists every raster picture in the document (name, format, size in KB) so the user can pick which ones to compress.
- Batch-compress every raster picture in the Writer document, or only the rows selected in the list (JPEG / PNG / BMP / GIF / TIFF).
- Choose the target resolution (DPI presets 96 / 150 / 200 / 300 / 600 or a custom value in the range 72–600).
- Choose the JPEG quality (1–99, default 80) and the PNG compression level (1–9, default 6) — same knobs as LibreOffice's built-in *Compress Image* dialog.
- Vector graphics (SVG / EMF / WMF, …) are skipped on purpose to avoid rasterising them.
- The compressed result is **saved next to the original as `name-compressed.odt`**; the original file is left untouched.
- The UI follows the LibreOffice UI language. Traditional Chinese is bundled; other locales fall back to English.
- The compress button sits on the standard toolbar just before *Insert Chart*. The same action is also reachable from *Insert → Image*.

## Known Limitations

- The bitmap scaling interpolation is whatever LibreOffice defaults to (Lanczos in current builds). UNO does not expose `BmpScaleFlag`, so unlike the built-in *Compress Image* dialog this extension cannot offer a Bilinear / Bicubic / None choice.

## Development

Build the .oxt:

```bash
make            # produces writer-batch-compress-X.Y.Z.oxt
```

Translation workflow:

```bash
make pot        # regenerate locales/writer-batch-compress.pot
# edit locales/<lang>/writer-batch-compress.po
make mo         # compile .po to .mo
```

For a tour of the source layout and the control flow of each user action, see [developer.md](developer.md).

---

# Writer 批次壓縮所有圖片

原本由 [PixCompress](https://extensions.libreoffice.org/en/extensions/show/1034)（Bidouille / O. Morelle）的 LibreOffice Basic 巨集改寫而來；目前的版本已完全以 Python 重寫，並透過 `com.sun.star.graphic.GraphicProvider.storeGraphic` 取得實際的解析度。

## 功能

- 按下工具列按鈕後先「分析圖片」，列出文件中所有點陣圖（檔名、格式、大小 KB），讓使用者勾選要壓縮的圖片。
- 可批次壓縮 Writer 文件中所有或選取的點陣圖（JPEG / PNG / BMP / GIF / TIFF）。
- 可指定壓縮時使用的解析度（DPI 96 / 150 / 200 / 300 / 600 或自訂 72–600）。
- 可指定 JPEG 品質（1–99，預設 80）與 PNG 壓縮等級（1–9，預設 6），與 LibreOffice 內建「壓縮影像」對話框一致。
- 向量圖（SVG / EMF / WMF 等）會自動略過，避免破壞畫質。
- 壓縮結果**另存為 `原檔名-compressed.odt`**，不會覆蓋原檔。
- 介面語系跟隨 LibreOffice UI（目前提供繁體中文翻譯，其他語系自動 fallback 英文）。
- 於 Writer 標準工具列的「插入圖表」按鈕前提供按鈕，亦可由「插入 → 圖片」選單啟動。

## 已知限制

- 縮圖時的插補演算法由 LibreOffice 預設值決定（通常為 Lanczos）。UNO API 無法取得 `BmpScaleFlag`，因此無法像 LibreOffice 內建「壓縮影像」對話框那樣選擇 Bilinear / Bicubic / None。

## 開發

打包：`make` 會產生 `writer-batch-compress-X.Y.Z.oxt`。

翻譯：

```bash
make pot   # 從原始碼抽出 locales/writer-batch-compress.pot
# 編輯 locales/<lang>/writer-batch-compress.po
make mo    # 編譯成 .mo
```

關於原始碼結構與每個使用者動作的呼叫流程，請參閱 [developer.md](developer.md)。
