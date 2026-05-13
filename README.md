# Writer 批次壓縮所有圖片

原本由 [PixCompress](https://extensions.libreoffice.org/en/extensions/show/1034)（Bidouille / O. Morelle）的 LibreOffice Basic 巨集改寫而來；目前的版本已完全以 Python 重寫，並透過 `com.sun.star.graphic.GraphicProvider.storeGraphic` 完成實際的解析度重採樣。

## 功能

- 按下工具列按鈕後先「分析圖片」，列出文件中所有點陣圖（檔名、格式、大小 KB），讓使用者勾選要壓縮的張數。
- 可批次壓縮 Writer 文件中所有或選取的點陣圖（JPEG / PNG / BMP / GIF / TIFF）。
- 可指定壓縮時使用的解析度（DPI 96 / 150 / 200 / 300 / 600 或自訂 72–600）。
- 可指定 JPEG 品質（1–99，預設 80）與 PNG 壓縮等級（1–9，預設 6），與 LibreOffice 內建「壓縮影像」對話框一致。
- 向量圖（SVG / EMF / WMF 等）會自動略過，避免破壞畫質。
- 壓縮結果**另存為 `原檔名-compressed.odt`**，不會覆蓋原檔。
- 介面語系跟隨 LibreOffice UI（目前提供繁體中文翻譯，其他語系自動 fallback 英文）。
- 於 Writer 標準工具列的「插入圖表」按鈕前提供快捷按鈕，亦可由「插入 → 圖片」選單啟動。

## 已知限制

- 縮圖時的插補演算法由 LibreOffice 預設值決定（通常為 Lanczos）。UNO API 未暴露 `BmpScaleFlag`，因此無法像 LibreOffice 內建「壓縮影像」對話框那樣選擇 Bilinear / Bicubic / None。

## 開發

打包：`make` 會產生 `writer-batch-compress-X.Y.Z.oxt`。

翻譯：

```bash
make pot   # 從原始碼抽出 locales/writer-batch-compress.pot
# 編輯 locales/<lang>/writer-batch-compress.po
make mo    # 編譯成 .mo
```
