# Writer 批次壓縮所有圖片

由 [PixCompress](https://extensions.libreoffice.org/en/extensions/show/1034) by Bidouille and O. Morelle 修改而來。

## 功能

- 批次壓縮 Writer 文件中的所有點陣圖（JPEG / PNG / BMP / GIF / TIFF）。
- 可指定壓縮時使用的解析度 (DPI)，預設 96，範圍 72–600。
- 可指定 JPEG 品質（1–99，預設 80）與 PNG 壓縮等級（1–9，預設 6），與 LibreOffice 內建「壓縮影像」對話框一致。
- 向量圖（SVG / EMF / WMF 等）會自動略過，避免破壞畫質。
- 於 Writer 標準工具列的「插入影像」按鈕後方提供快捷按鈕，亦可由「插入 → 影像」選單啟動。

## 已知限制

- 縮圖時的插補演算法目前由 LibreOffice 預設值決定（通常為 Lanczos）。UNO API 未暴露 `BmpScaleFlag`，因此無法像 LibreOffice 內建「壓縮影像」對話框那樣選擇 Bilinear / Bicubic / None。
