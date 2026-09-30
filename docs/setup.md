# 打开报表

## 本机

直接打开 `powerbi/OnlineRetail.pbix`。这份文件已包含数据，暂时不需要重新导入。

## 从 GitHub 下载后

1. 安装标准版 Power BI Desktop。
2. 在项目根目录运行 `python scripts/setup_paths.py`，设置 CSV 路径。
3. 打开 `powerbi/OnlineRetail.pbip`。
4. 如有“应用更改”提示，先点击它，再点击“刷新”。

数据文件已放在 `data/processed`，仅查看报表不需要重新下载原始 Excel。
如要从原始数据重跑，按 README 的命令执行下载、清洗和检查。

## 初次刷新遇到问题

- 提示关系需要刷新：点击该提示中的“立即刷新”。
- 提示循环引用：关闭提示，点击“应用更改”，然后再刷新。
- 找不到 CSV：检查 `DataFolder` 是否指向当前项目的 `data/processed`。
- 看不到页面：确认 `definition/version.json` 中的版本是 `2.0.0`。

提交源码前运行 `python scripts/setup_paths.py --portable`，避免上传本机路径。
PBIX 包含本机刷新路径，因此只保留在本地；GitHub 使用 PBIP 源码。

## 可以检查的数字

清除经营页的筛选后，Gross Sales 为 £10,666,684.54，Recorded Credits 为
£896,812.49，Net Recorded Sales 为 £9,769,872.05，Sales Orders 为 19,960。
客户页显示 4,338 名购买客户，其中 2,845 名下过多笔订单。

客户分群是截至 2011-12-10 的快照。队列页只使用完整月份，截止 2011-11。
这些页面与经营页的筛选范围不同，具体规则见 `notes.md`。
