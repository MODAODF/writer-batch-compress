# 開發者文件

本檔案說明 Writer 批次壓縮圖片 extension 的原始碼結構與主要使用者操作在程式內的流程。

> 觀念：這個 extension 本體是一個註冊在 LibreOffice 內的 **UNO 服務**，由 Addons.xcu 把工具列按鈕、選單項目、Notebookbar 條目都指向同一個 service URL `service:org.ossii.WriterBatchCompress.do`。LibreOffice 拿到該 URL 後會建立 `main.py` 中的 `MainJob`，並呼叫它的 `trigger()`，從那裡進入 Python 邏輯。

---

## 檔案／目錄總覽

```
writer-batch-compress/
├── Addons.xcu                  ← UI 註冊：工具列、選單、Notebookbar、Image
├── description.xml             ← extension 中介資料（版本、identifier、授權）
├── META-INF/manifest.xml       ← OXT 內檔案的 media-type 註冊
├── Makefile                    ← 打包 .oxt、產生 .pot / 編譯 .mo
├── update_version.sh           ← Makefile 呼叫，自動把 VERSION 寫進 description.xml
├── VERSION                     ← 當前版本字串
├── README.md / developer.md    ← 使用者／開發者說明
├── icons/                      ← 工具列圖示（16x16, 26x26 bmp）
├── logo.png                    ← extension 管理員顯示用的圖
├── pkg-desc/                   ← 安裝時顯示的多語描述
├── registration/               ← 授權書（CeCILL）
├── locales/                    ← gettext 多語檔
│   ├── writer-batch-compress.pot           ← pygettext 抽出的 msgid 範本
│   └── zh_TW/
│       ├── writer-batch-compress.po        ← 繁中翻譯來源
│       └── LC_MESSAGES/writer-batch-compress.mo  ← msgfmt 編譯結果
├── main.py                     ← UNO 進入點：XJobExecutor
└── pythonpath/                 ← OXT 安裝後會自動加入 sys.path 的資料夾
    ├── easymacro/              ← 第三方輔助庫（vendored，GPLv3）
    ├── pixcompress.py          ← 流程協調 (run / _run / _analyze)
    ├── pixdialog.py            ← 選項對話框
    ├── pixi18n.py              ← gettext bootstrap，提供 `_()`
    ├── pixmeta.py              ← 從 odt zip 抽 picture 資訊（純 Python）
    ├── pixprogress.py          ← 非 modal 進度視窗
    └── pixresample.py          ← 單張圖片重採樣（呼叫 LibreOffice UNO）
```

### 每個關鍵檔案的職責

| 檔案 | 職責 |
|---|---|
| `Addons.xcu` | 在 LibreOffice 中註冊 UI 入口。`OfficeToolbarMerging`（注意 `bar` 小寫 b）、`OfficeMenuBarMerging`（注意 `Bar` 大寫 B）、`OfficeNotebookBar`、`Images` 四個節點。所有 URL 都指向同一個 service URL。 |
| `META-INF/manifest.xml` | 告訴 OXT 安裝器：`main.py` 是 Python UNO 元件；`Addons.xcu` 是設定資料；`pkg-desc/*` 是地區化描述。 |
| `main.py` | 22 行的小型入口：`MainJob.__init__` 接 ctx、`trigger(args)` 動態 import `pixcompress.run()`。`g_ImplementationHelper.addImplementation` 在 Python 元件載入時自動執行，把 `MainJob` 註冊為 `org.ossii.WriterBatchCompress.do` 服務。 |
| `pythonpath/pixcompress.py` | 整個 extension 的協調者。`run()` 是 trigger 進入點，把所有錯誤包進 try/except 顯示在 msgbox；`_run()` 跑真正的流程。 |
| `pythonpath/pixdialog.py` | 用 easymacro 建構選項對話框（listbox、DPI combobox、quality/compression spin、三顆按鈕）。本身**沒有壓縮邏輯**，只負責蒐集使用者選擇。 |
| `pythonpath/pixmeta.py` | 純 Python — 直接用 `zipfile` + `xml.etree` 讀 odt 內的 `content.xml` 與 `Pictures/`。**不依賴 UNO**。 |
| `pythonpath/pixprogress.py` | 用 UNO 直接組一個非 modal 的進度視窗（單一 ProgressBar）。仿 BASIC 的 `CreeBarre` helper。 |
| `pythonpath/pixresample.py` | 單張圖片的重採樣。呼叫 `com.sun.star.graphic.GraphicProvider.storeGraphic` 把圖縮到目標像素再用 `queryGraphic` 載回替換。`FilterData` 用 `easymacro.dict_to_property(uno_any=True)` 包成 `uno.Any('[]com.sun.star.beans.PropertyValue', ...)`，避免 PyUNO 把 nested PropertyValue 翻成 `[]any` 導致 LibreOffice 忽略屬性。 |
| `pythonpath/pixi18n.py` | 用 `gettext.translation(APPNAME, PATH_LOCALES, fallback=True)` 載入 mo 檔；對外 export `_`。語系偵測直接靠 gettext，靠的是 LibreOffice 啟動時注入的 `LANG`/`LC_*` 環境變數。 |
| `pythonpath/easymacro/` | 第三方輔助庫，提供 `app.active`（取目前文件）、`app.dialog.create()`（對話框）、`app.msgbox`、`app.paths`、`LODrawPage`、`UnoComboBox` 等 wrapper。 |
| `locales/*.po` / `*.mo` | gettext 翻譯。`.po` 為來源、`.mo` 為 LibreOffice 執行時讀取的編譯檔。 |
| `Makefile` | `make` 編譯 mo 後把所有檔案打包成 `.oxt`；`make pot` 從原始碼抽 msgid；`make mo` 編譯 zh_TW.po。 |

---

## 啟動流程（按下任何一個入口都會走這一遍）

```
使用者按 Writer 工具列上的「批次壓縮圖片」按鈕
       │  （URL = service:org.ossii.WriterBatchCompress.do）
       ▼
LibreOffice JobExecutor 找到註冊在 main.py 的 MainJob
       │
       ▼
MainJob.trigger(args)
       │  import pixcompress
       ▼
pixcompress.run()              ← 全域 try/except 邊界
       │
       ▼
pixcompress._run()             ← 真正的流程
```

`_run()` 內部的順序：

1. **取得目前文件**：`doc = app.active`。
2. **前置檢查**：
   - 沒有開啟文件、或不是 Writer → 顯示 `Open a Writer document first.` 後 return。
   - `doc.path` 為空（未存檔）→ 顯示 `Save the document before compressing its pictures.` 後 return。`storeToURL` 需要原檔位置。
3. **分析階段** `_analyze(doc)`（見下方「分析動作」）。若回空 list → 顯示 `No pictures found in this document.` 後 return。
4. **偵測文件中選取的圖片** `_selected_picture_index(doc, pictures)` → 回傳 list 中對應的 index 或 -1。用來決定對話框預設按鈕（如果使用者在文件中已點了一張圖，預設按 *Compress selected*）。
5. **計算總大小** 分析快照中 `sum(pixmeta.picture_sizes(snapshot).values()) / 1000`（共用資源只計一次），傳給對話框顯示 `Total: ... KB (N pictures)`。
6. **彈出對話框** `pixdialog.ask_options(labels, sel_idx, total_kb)`（見下方「對話框互動」）。回 None 表示使用者按 Cancel。
7. **依使用者選擇決定壓縮對象**：
   - `action == "selected"` → `targets = [pictures[p] for p in list_positions]`
   - 其他（`"all"`） → `targets = pictures`
8. **壓縮迴圈**：
   - 開一個 `pixprogress.create(_("Compressing pictures..."), len(targets))`。
   - 每張呼叫 `pixresample.resample(...)`，內外都用 try/except 包，單張失敗計入 skipped 但不中斷。
   - 每張完成後 `progress.advance(i + 1)` 觸發 progress bar 更新與 `processEventsToIdle()`。
   - `finally:` `progress.close()` 確保視窗一定關閉。
9. **儲存壓縮版**：`_compressed_url(doc.obj.URL)` 在副檔名前插 `-compressed`，`doc.obj.storeToURL(new_url, ())`。**不會覆蓋原檔**。
10. **重新量測** 用 `pixmeta.picture_sizes(_url_to_path(new_url))` 對新 odt 加總，做出 before/after 對照。
11. **結果 msgbox** 三行：壓縮張數摘要 / 前後總大小 / 新檔路徑。

---

## 使用者動作對應的程式流程

### 動作 A：在文件中點一張圖再按按鈕

1. `pixcompress._run` 走到 `_selected_picture_index(doc, pictures)`。
2. `doc.obj.CurrentSelection` 取得目前選取物件。
3. 檢查 `ImplementationName` 必須是 `SwXTextGraphicObject` 或 `SwXShape`，否則回 -1。
4. 比對選取物件的 `Name`（例如 `影像 24`）與分析階段得到的 `pictures` 中每個 `_Picture.name`，找到符合的 index。
5. index 傳給 `pixdialog.ask_options` 的 `selected_index` 參數。
6. `pixdialog.ask_options` 內部設定：
   - `lst.selectItemPos(selected_index, True)` — listbox 預選那一列。
   - `dlg.cmd_selected.model.Enabled = True`
   - `dlg.cmd_selected.model.DefaultButton = True`（按 Enter 直接走 Compress selected）。

### 動作 B：在 listbox 內勾選一張或多張

1. `pixdialog.ask_options` 替 listbox 設 `MultiSelection: True`（可 Ctrl/Shift-click）。
2. 接上 `_ListboxListener(_Controller)`（實作 `XItemListener`）。
3. 使用者每改變選擇 → `itemStateChanged` 觸發 → `controller.on_listbox_change()` 被呼叫。
4. `on_listbox_change` 讀 `lst.getSelectedItemsPos()`（注意是 method，不是 `SelectedItems` 屬性 — 後者回傳 string 陣列），依長度啟用/停用 `cmd_selected` 按鈕。

### 動作 C：按下 *Compress all*

1. easymacro `EventsButton` 自動 dispatch 到 `_Controller.cmd_all_action(event)`。
2. controller 記下 `action = "all"`；`selected_positions = ()`。
3. `self.d.close(1)` 結束對話框 modal loop，返回值 1。
4. `ask_options` 結束 `dlg.open()`，讀 `dlg.events.action`，組回傳值 `(dpi, quality, compression, "all", ())`。
5. `_run` 收到 `action == "all"` → `targets = pictures`。
6. 進入壓縮迴圈，對每張呼叫 `pixresample.resample`。

### 動作 D：按下 *Compress selected*

1. `_Controller.cmd_selected_action(event)`：
   - 立刻讀 `self.d.lstImages.obj.getSelectedItemsPos()`，存進 `self.selected_positions`。**必須在 close 之前**，否則 listbox 可能被 dispose。
   - `action = "selected"`；`self.d.close(1)`。
2. `ask_options` 回 `(dpi, quality, compression, "selected", list_positions)`。
3. `_run` 用 `targets = [pictures[p] for p in list_positions if 0 <= p < len(pictures)]`。
4. 後續壓縮流程相同。

### 動作 E：按下 *Cancel* / 關閉對話框

1. `_Controller.cmd_cancel_action`（或對話框 X 按鈕）→ `self.d.close(0)`。
2. `ask_options` 回 `None`。
3. `_run` 立刻 return。**不會** 跑 storeToURL，不會建立 -compressed.odt。

### 動作 F：分析動作（`_analyze`）

1. 開 `pixprogress.create(_("Analyzing pictures..."), 2)` 顯示「正在分析圖片」對話框。
2. 用 `storeToURL` 與 `FilterName=writer8` 將目前記憶體中的文件匯出成暫存 ODT，包含尚未儲存的圖片修改，不讀磁碟上的舊原檔。暫存目錄在成功或發生例外時都會清除。
3. `pixmeta.picture_frames(snapshot)` 解析 `content.xml` 與 `styles.xml`（包含頁首頁尾）：以唯一的 `draw:frame/@draw:name` 對應 `draw:image/@xlink:href`，再從 ZIP entry 取得未壓縮的圖片檔案位元組數。
4. 走訪 DrawPage，使用圖片物件的 `Name` 查表。無須比對像素、格式或列舉順序，也不會消耗資源記錄，因此同一張圖片重複引用時每個物件都能顯示大小。
5. 外部連結、遺失資源、重複 frame 名稱或同一 frame 有多個圖片表示時，以 `None` 表示未知，清單顯示 `?`；實際 0 bytes 則顯示 `0.00 KB`。
6. 回傳 `(pictures, total)`。總計加總快照內的 `Pictures/` 資源，每個資源只計一次，與壓縮後對輸出 ODT 的統計方式相同。因此清單列的大小加總可能大於總計（多個物件共用圖片），外部連結則不納入內嵌資源總計。
7. `progress.close()`。

回歸測試：`python3 -m unittest discover -s tests -v`。測試不需 UNO，涵蓋格式與大小獨立、重複引用、未知與零位元組、頁首頁尾、未儲存內容的快照及例外清理。實際 UNO 整合測試：`/opt/libreoffice26.8/program/python tests/verify_libreoffice.py`（請視安裝位置調整路徑）。此測試以獨立 headless instance 驗證同尺寸 PNG、JPG、共用資源、未儲存替換、原檔保留，以及真實重採樣後輸出與快照總計一致；已在 LibreOffice 26.8.1.1 通過。互動對話框仍需人工確認。

### 動作 G：單張圖片重採樣（`pixresample.resample`）

1. 取 `oImg.Graphic`、檢查 `MimeType`。
   - JPEG → 維持 JPEG。
   - PNG/BMP/GIF/TIFF/x-ms-bmp → 統一轉 PNG（保留可能的透明）。
   - 其他（向量 SVG/EMF/WMF/未知）→ 回 `False`，跳過。
2. 從 `oImg.Size`（1/100 mm）算目標像素：`pixel = size_mm100 * dpi / 2540`。
3. 組 `FilterData` dict：`PixelWidth`, `PixelHeight`，再加 JPEG `Quality` 或 PNG `Compression`。`dict_to_property(..., uno_any=True)` 包成 `uno.Any('[]com.sun.star.beans.PropertyValue', ...)`。
4. 建立 `tempfile.mkstemp` 拿到 system path → `uno.systemPathToFileUrl()` 轉成 file URL。
5. 取得 `com.sun.star.graphic.GraphicProvider` service。
6. **`provider.storeGraphic(graphic, props)`** 把 graphic 縮到指定像素並編碼成 PNG/JPEG 寫到 temp file。LibreOffice 內部走 `ImplApplyFilterData → ImplApplyBitmapScaling → BitmapEx::Scale`，這條路徑會真的縮放 bitmap（不像 `GraphicExportFilter` 對 Writer raster shape 會略過縮放）。
7. **`provider.queryGraphic({"URL": tmp_url})`** 把 temp file 讀回成新的 `XGraphic` 物件。
8. **`img.Graphic = new_graphic`** 取代原來的 graphic。**這一步必須在刪 temp 檔之前**，否則某些 LibreOffice 版本對 lazy-load 的 XGraphic 會失效。
9. `finally:` `os.remove(tmp_path)` 清理 temp。

### 動作 H：另存壓縮版

1. `_compressed_url(doc.obj.URL)`：找最後一個 `.`，若在最後一個 `/` 之後就插 `-compressed` 進副檔名前；否則直接尾綴。
2. `doc.obj.storeToURL(new_url, ())` 用 empty args（讓 LibreOffice 依副檔名選 filter）。
3. **記憶體中的文件已被改過**（圖片是壓縮後的 XGraphic）。如果使用者後續按一般的「儲存」會把壓縮版蓋回原檔；想保留原檔就關閉時選「不要儲存」。

### 動作 I：i18n 字串解析

1. `pythonpath/pixi18n.py` 在 module load 時呼叫 `gettext.translation('writer-batch-compress', '<ext>/locales', fallback=True)`，回 `GNUTranslations` 或 `NullTranslations`。
2. `_ = t.gettext`。
3. 各模組 `from pixi18n import _` 並用 `_("...")` 包字串。`{kw}` 占位符仍用 Python `.format(**kw)`，因此單純語意化的字串（不嵌入動態內容）即可被 pygettext 正確抽出。
4. `make pot` 用 `pygettext3` 掃所有 `_()` 取得 msgid 寫進 `locales/writer-batch-compress.pot`。
5. 翻譯者複製到 `locales/<lang>/writer-batch-compress.po` 填 `msgstr`。
6. `make mo` 用 `msgfmt` 編成 `.mo`，安裝到 OXT 後 LibreOffice 啟動時依 `LANG` 自動選用。

---

## 進度視窗的特殊處理

`pixprogress.create()` 不依賴 easymacro 對話框（easymacro 沒包進度條 control），自行用 UNO 組：

1. 建 `UnoControlDialogModel` + `UnoControlProgressBarModel`，後者 `insertByName("bar", ...)` 進 dialog model。
2. 設 `dlg_model.Closeable = False` — 避免使用者中途關閉進度視窗，否則下一輪 `advance()` 會打到已被 dispose 的 peer。
3. 建 `UnoControlDialog`，呼叫 `createPeer(toolkit, None)` + `setVisible(True)`（**非 modal**，沒呼叫 `execute()`）。
4. 立刻 `toolkit.processEventsToIdle()`。沒這一步，dialog 雖然 setVisible 但 LibreOffice 還沒處理 event queue 就讓 Python 進入 zip / loop，畫面一直不會 paint（特別是 *Analyzing pictures* 階段太短）。
5. `_Handle.advance(value)` 每張完成後呼叫，更新 `ProgressValue` 並再 `processEventsToIdle()`。內部有 `_closed` 旗標，已關閉就 no-op。
6. `_Handle.close()` 也有 `_closed` 旗標，避免重複關。

---

## PyUNO 踩過的坑（給後續維護者）

1. **`StringItemList` 等 sequence<string> 屬性**：若 setPropertyValues 傳 Python tuple，PyUNO 翻成 `[]any`，LibreOffice 拒收。改為構造後逐項 `addItem()` 處理，例如 `pixdialog.py` 對 DPI combobox 的處理。
2. **`uno.Any('[]string', ...)` 不能直接傳給 setPropertyValues**：會丟 `uno.Any instance not accepted during method call`。要傳給 `setPropertyValue`（單數）或在 method call 用 `uno.invoke`。**唯一例外是用在 PropertyValue.Value**（巢狀），這時 PyUNO 會正確識別，可參考 `pixresample.py` 的 FilterData。
3. **`Mid()` 在 LibreOffice Basic 對 long offset 有問題**：超過 16-bit Integer 就空回。這個專案已脫離 Basic，但若回頭看 BASIC commit 會看到 Split() workaround。
4. **`Closeable=False` 移除 X 按鈕**：是 `UnoControlDialogModel` 的標準屬性，不要漏。
5. **`SelectedItems` vs `getSelectedItemsPos()`**：前者回顯示文字字串，後者才回索引。多選邏輯吃過虧。
6. **`com.sun.star.drawing.GraphicExportFilter`** 對 Writer 內嵌 raster shape **不會**套 PixelWidth/PixelHeight（會直接撈原 graphic）。`com.sun.star.graphic.GraphicProvider.storeGraphic` 才是對的工具，內部走 `ImplApplyFilterData → BitmapEx::Scale`。

---

## 加新功能的常見路徑

| 需求 | 動哪些檔 |
|---|---|
| 新增一個對話框控制項 | `pixdialog.py` 加 `dlg.add_control(...)`、Controller 對應 method、回傳值多帶一個欄位；`pixcompress._run` 接收後傳給 `pixresample.resample` 或其他層 |
| 改變單張壓縮邏輯 | 只動 `pixresample.py`，介面不變 |
| 加新語系 | `make pot` → 複製到 `locales/<lang>/writer-batch-compress.po` 翻譯 → `make mo` |
| 改 toolbar / menu 位置 | `Addons.xcu`，記得 `OfficeToolbarMerging` 是小寫 `bar`、`OfficeMenuBarMerging` 是大寫 `Bar`（schema 規定，搞錯整段被忽略） |
| 加 README 多語版本 | `README.md` 直接編輯（兩個區塊以分隔線分開） |

---

## 版本與 tag

- **`basic-final`** — Python 重寫前最後一個可用的 BASIC 版本。完整保留 BASIC 程式碼，便於回溯比對。
- **`python-stage4`** — Python 重寫中段點，listbox 顯示 pixel 大小（尚未做 SizePixel + ext 對應）。

往後若再有破壞性改動，建議照同樣慣例打 tag 留 checkpoint。
