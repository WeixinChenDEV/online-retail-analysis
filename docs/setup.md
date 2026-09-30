# Opening the report｜開啟報表

## Local copy｜本機版本

Open `powerbi/OnlineRetail.pbix` in the local working folder. Data is already loaded.
The PBIX is not included on GitHub because its refresh settings contain a local path.

在本機工作資料夾直接開啟 `powerbi/OnlineRetail.pbix`，數據已載入。
PBIX 的重新整理設定包含本機路徑，因此未上傳至 GitHub。

## Downloaded from GitHub｜從 GitHub 下載

1. Install the standard Power BI Desktop application.／安裝標準版 Power BI Desktop。
2. Run `python scripts/setup_paths.py` from the project root.／在專案根目錄執行此命令，設定 CSV 路徑。
3. Open `powerbi/OnlineRetail.pbip`.／開啟此專案檔案。
4. Apply pending changes if prompted, then refresh.／按提示套用變更，再重新整理。

Prepared CSVs are in `data/processed`. You do not need to download the original
Excel workbook just to view the report. To rebuild the data, follow the README commands.

整理好的 CSV 位於 `data/processed`；只查看報表不需要下載原始 Excel。
如要重新整理原始數據，請按 README 的命令執行。

## First refresh｜初次重新整理

| Issue／問題 | Action／處理方式 |
| --- | --- |
| Relationships need refreshing／關聯需要重新整理 | Use the prompt's Refresh now button／按提示中的「立即重新整理」 |
| Circular reference prompt／循環參照提示 | Close the prompt, apply pending changes and refresh／關閉提示，套用變更後再重新整理 |
| CSV not found／找不到 CSV | Check `DataFolder` points to this copy's `data/processed`／確認路徑指向目前專案的資料夾 |
| Pages do not appear／看不到頁面 | Check `definition/version.json` uses `2.0.0`／確認版本值為 `2.0.0` |

Before committing source changes, run `python scripts/setup_paths.py --portable`
to remove the local path from the source model.

提交源碼前執行 `python scripts/setup_paths.py --portable`，移除模型中的本機路徑。

## Numbers to check｜可核對的數字

With overview filters cleared: Gross Sales £10,666,684.54, Recorded Credits
£896,812.49, Net Recorded Sales £9,769,872.05 and Sales Orders 19,960.
The customer page has 4,338 purchasing customers, including 2,845 with multiple orders.

清除概覽頁的篩選後：銷售總額 £10,666,684.54、貸記金額 £896,812.49、銷售淨額 £9,769,872.05，
銷售訂單 19,960 筆。客戶頁有 4,338 名購買客戶，其中 2,845 名曾下多筆訂單。

Customer groups are a snapshot as of 10 December 2011. Cohorts use complete months
through November 2011. Their scope differs from overview filters; see the
[English notes](notes.md) or [繁體中文筆記](notes.zh-Hant.md).

客戶分群採用截至 2011 年 12 月 10 日的快照；購買群組只使用截至 2011 年 11 月的完整月份。
這些頁面的範圍與概覽頁的篩選不同，詳見上述分析筆記。
