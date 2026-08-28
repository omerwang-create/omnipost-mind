"""Language control: bilingual UI (i18n) + system prompt injection.

Minds messaging has no system-role field, so the "system prompt" is injected
by prepending it to every request; the conversation itself is the memory node.
"""

LANG = "zh"

SYSTEM_PROMPTS = {
    "zh": "你是一个顶级的跨平台内容重构专家。从现在起，你的所有思考过程、生成的 Twitter 推文、TikTok 视频脚本、以及对内容的爆款打分和优化建议，必须严格使用简体中文，并符合中文互联网的阅读习惯。",
    "en": "You are a top-tier cross-platform content repurposing expert. From now on, all your outputs, including Twitter threads, TikTok scripts, virality scores, and optimization suggestions, must be strictly in English, maintaining native-level fluency and internet culture relevance.",
}

CONVERT_PROMPTS = {
    "zh": """将下面文字转成以下 JSON。严格输出纯 JSON，不要用 ``` 代码块包裹，不要任何开场白、解释或复述：

{
  "twitter_thread": ["推文1", "推文2", "推文3"],
  "tiktok_script": "【Hook 0-3s】...\\n\\n【画面】...\\n\\n【台词】...",
  "virality_score": 82,
  "feedback": "优化建议..."
}

要求：
- twitter_thread：拆成 3-8 条推文组成的数组，每条 ≤280 字，不要带序号。
- tiktok_script：用【Hook】/【画面】/【台词】等节点标注，保留段落空行（\\n\\n）。
- virality_score：0-100 的整数。严禁无脑给 100，绝大多数普通文本 70-85，只有结构极精妙、极具爆款潜质才 90+。
- feedback：1-2 句扣分原因与优化建议。
- 严格遵守你已记住的偏好设置。

【格式硬性要求】：在输出的最开头，必须单独写一行评分，格式必须严格为：Score: XX（XX为70-95之间的数字），紧接着换行输出内容。不要添加任何Markdown加粗或额外前缀。

原文：
""",
    "en": """Convert the text below into this JSON. Output pure JSON only, no ``` code fences, no preamble, explanation, or repetition:

{
  "twitter_thread": ["tweet1", "tweet2", "tweet3"],
  "tiktok_script": "[Hook 0-3s]...\\n\\n[Scene]...\\n\\n[Voiceover]...",
  "virality_score": 82,
  "feedback": "improvement suggestion..."
}

Requirements:
- twitter_thread: an array of 3-8 tweets, each ≤280 chars, no numbering.
- tiktok_script: annotate with [Hook] / [Scene] / [Voiceover] nodes, keep paragraph breaks (\\n\\n).
- virality_score: integer 0-100. Never blindly give 100; most ordinary text 70-85, only exceptionally crafted content 90+.
- feedback: 1-2 sentences of deduction reasons and suggestions.
- Follow any remembered preferences.

【Format hard requirement】: At the very start of your output, write a single score line in the exact format: Score: XX (XX is a number between 70-95), followed immediately by a newline and the content. No Markdown bold or extra prefixes.

Source text:
""",
}

UI = {
    "zh": {
        "sidebar_title": "🧠 记忆控制台",
        "lang_label": "语言 / Language",
        "profile_label": "品牌人设 / Brand Profile",
        "active_profile": "当前人设",
        "active_lang": "输出语言",
        "profile_switched": "已切换人设 → {name}",
        "logo_sub": "长文本 → Twitter Thread + TikTok 脚本 · 爆款打分 · 一键导出",
        "input_label": "粘贴长文",
        "input_placeholder": "在这里粘贴你的文章、笔记或想法……",
        "generate": "✨ 生成",
        "empty_warning": "请先粘贴内容。",
        "mind_fail": "Minds 连接失败，请检查 MINDS_API_KEY。",
        "connecting": "连接 Minds...",
        "generating": "生成中...",
        "score_title": "爆款评分",
        "score_missing": "AI 未返回有效分数，请重试或换一段文本。",
        "fallback_note": "⚠️ 解析兜底已启用：AI 返回格式不规范，已按段落智能切分并采用默认评分。",
        "thread": "🐦 Twitter Thread",
        "tiktok": "🎬 TikTok 脚本",
        "exported": "✅ 已导出到 {path}",
        "timeout": "⏱ Mind 未在 300 秒内回复，请重试。新会话首次生成需冷启动，通常较慢，稍后再次点击会快很多。",
        "no_profile": "未选择人设",
        "mode_label": "当前模式",
        "download": "下载",
        "ws_label": "项目工作区",
        "ws_new_ph": "新文件夹名称",
        "ws_new_btn": "➕ 新建",
        "ws_new_empty": "请输入文件夹名称",
        "ws_delete": "🗑 删除当前文件夹",
        "ws_delete_confirm": "确定删除「{name}」？此操作不可撤销。",
        "ws_history": "📜 当前文件夹历史生成记忆",
        "ws_del_rec": "🗑 删除",
        "ws_empty": "暂无历史记录",
        "ws_path": "当前工作区",
        "lang_zh": "中文",
        "lang_en": "English",
    },
    "en": {
        "sidebar_title": "🧠 Memory Console",
        "lang_label": "语言 / Language",
        "profile_label": "Brand Profile",
        "active_profile": "Active Profile",
        "active_lang": "Output Language",
        "profile_switched": "Switched to {name}",
        "logo_sub": "Long text → Twitter Thread + TikTok script · Virality score · Export",
        "input_label": "Paste your long text",
        "input_placeholder": "Paste your article, notes or ideas here…",
        "generate": "✨ Generate",
        "empty_warning": "Please paste some content first.",
        "mind_fail": "Minds connection failed. Check MINDS_API_KEY.",
        "connecting": "Connecting to Minds...",
        "generating": "Generating...",
        "score_title": "Virality Score",
        "score_missing": "AI did not return a valid score. Please retry or use different text.",
        "fallback_note": "⚠️ Fallback parsing active: the AI response format was irregular; text was split heuristically and a default score was applied.",
        "thread": "🐦 Twitter Thread",
        "tiktok": "🎬 TikTok Script",
        "exported": "✅ Exported to {path}",
        "timeout": "⏱ Mind did not reply within 300s, please retry. A new conversation is slow on first run (cold start); retrying will be much faster.",
        "no_profile": "No profile selected",
        "mode_label": "Mode",
        "download": "Download",
        "ws_label": "Workspaces",
        "ws_new_ph": "New folder name",
        "ws_new_btn": "➕ New",
        "ws_new_empty": "Please enter a folder name",
        "ws_delete": "🗑 Delete current folder",
        "ws_delete_confirm": "Delete \"{name}\"? This cannot be undone.",
        "ws_history": "📜 Current workspace generation history",
        "ws_del_rec": "🗑 Delete",
        "ws_empty": "No history yet",
        "ws_path": "Current Workspace",
        "lang_zh": "中文",
        "lang_en": "English",
    },
}


def t(key, **kw):
    s = UI[LANG].get(key, key)
    return s.format(**kw) if kw else s


def system_prompt():
    return SYSTEM_PROMPTS[LANG]


def convert_prompt():
    return CONVERT_PROMPTS[LANG]


def set_lang(code):
    global LANG
    LANG = "en" if code == "en" else "zh"
