# 单个视频的清洗与抽取规范

输入（都在 `media/<id>/` 下）：
- `transcript.json`：Whisper 转写，`segments[{start,end,text}]`，**没有标点**，有同音错字
- `frames.json`：去重后的关键帧 `[{t, file, ocr}]`，ocr 是屏幕文字（教学视频是幻灯片，点评视频是 K 线图上的橙色标注框）
- `full.info.json`：标题、上传日期（`upload_date`）、简介

输出两个文件，写到同一目录：

## 1. `clean.md` —— 可读文稿

- 开头：标题、日期（YYYY-MM-DD）、视频链接、类型（teaching / weekly / daily）
- 按话题分节，用 `##` 小标题；每段开头标 `[mm:ss]`
- 加标点、分段；按上下文修正同音错字和股票名（例：Raino→Rhino，英伟达统一写“英伟达(NVDA)”首次出现时标代码）
- 屏幕文字：在对应时间点插入 `> 📺 屏幕：...`。渐进式幻灯片只保留**信息最全的那一帧**（后一帧 OCR 包含前一帧时，丢前一帧）。浏览器截图、评论区截图等噪声丢掉
- 删除：开场寒暄、结尾求点赞、会员推广、Q&A 帖子说明
- **不要总结、不要改写观点**，保留他的原意和口语里的关键措辞（“不见兔子不撒鹰”这类要留）

## 2. `extract.json` —— 结构化抽取

只抽**视频里真实说过的内容**，每条带时间戳 `t`（秒）。没有就给空数组。

```json
{
  "video_id": "", "date": "YYYY-MM-DD", "type": "teaching|weekly|daily", "title": "",
  "summary": "3-5 句，这期讲了什么",
  "principles": [
    {"category": "大盘|估值|技术|买点|卖点|仓位|风控|心态|选股|工具",
     "rule": "一句话规则，用他的口吻",
     "conditions": "什么情况下适用",
     "rationale": "他给的理由",
     "example": "他举的例子（股票/日期/数字）",
     "quote": "最关键的一句原话（≤40字）",
     "t": 0}
  ],
  "methods": [
    {"name": "方法名，如 ERP 估值比较 / 前瞻估值强支撑",
     "steps": ["步骤1", "步骤2"],
     "inputs": ["需要哪些数据、他说去哪查"],
     "output": "得出什么结论",
     "t": 0}
  ],
  "stock_cases": [
    {"ticker": "NVDA", "view": "看多/看空/中性/等待",
     "valuation": "估值数字与结论（如 前瞻PE、EPS 增速、合理区间）",
     "support": ["价位+理由"], "resistance": ["价位+理由"],
     "action": "建仓|加仓|减仓|清仓|持有|观望|无",
     "plan": "条件→动作，例：回到 X 出现止跌形态再买，跌破 Y 收盘价止损",
     "t": 0}
  ],
  "market_scenarios": [
    {"target": "SPY/SPX/QQQ/SOXX…", "condition": "守住/跌破/突破 X（以收盘价为准等）",
     "outcome": "后续走势判断", "action": "对应操作", "t": 0}
  ],
  "indicators": [
    {"name": "CTA 资金流 / VIX 期限结构 / EPS 修正 …", "how_to_read": "他怎么解读", "source": "数据从哪来（如提到）", "t": 0}
  ],
  "terms": [{"term": "", "definition": "他的定义"}]
}
```

判断标准：`principles` 和 `methods` 是**可以迁移到别的股票、别的日期**的东西；`stock_cases` 和 `market_scenarios` 是**这一天、这只股票**的具体判断。
