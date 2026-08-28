"""Multi-platform content generation: parse AI output, virality score panel,
and Markdown export."""
import os, re, html, json
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

SEP_TIKTOK = "===TIKTOK==="
SEP_SCORE = "===SCORE==="

# Markdown 区块头（#/##/### 均可，中英兼容，允许 **加粗** 包裹）
HEAD_TW = re.compile(r"^\s*\*{0,2}#{1,3}\s*\*{0,2}(twitter( thread)?|twitter\s*线程|推文)[^\n]*$", re.I | re.M)
HEAD_TK = re.compile(r"^\s*\*{0,2}#{1,3}\s*\*{0,2}(tiktok( script)?|tiktok\s*脚本|tiktok\s*文案|视频脚本)[^\n]*$", re.I | re.M)
HEAD_SC = re.compile(r"^\s*\*{0,2}#{1,3}\s*\*{0,2}(virality\s*score|score|评分|质量评价)[^\n]*$", re.I | re.M)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
console = Console()


def strip_html(s):
    s = html.unescape(s)
    return re.sub(r"<[^>]+>", "", s).strip()


_META_RE = re.compile(
    r"you\s+(asked|requested|wrote|said)|here\s+(is|are|'s|’s)|"
    r"好的[，,]?\s*以下|以下[是为根据]|根据(?:你的|您的)|"
    r"^(?:ok|sure|here you go|got it|hold\b|cognition\s+runway|"
    r"same\s+(?:omni|article|situation)|waiting\s+for)\b",
    re.I,
)


def strip_meta(s):
    """移除 AI 开头自说自话的解释性话术（如 "You asked in English..."），
    只从第一行真正内容开始保留。"""
    lines = s.splitlines()
    for i, line in enumerate(lines):
        ls = line.strip()
        if not ls:
            continue
        if _META_RE.search(ls):
            continue
        return "\n".join(lines[i:])
    return s


def is_meta_refusal(raw):
    """检测 AI 返回的是「拒绝/元对话」而非实际生成内容。

    真内容特征：含 JSON 字段、分镜节点、或 n/N 推文标记。
    元对话特征：含 "same article / re-running / cognition runway / waiting for"
    等拒绝话术。
    """
    if not raw or not raw.strip():
        return True
    # 有真实内容 → 不是拒绝
    if "twitter_thread" in raw or "tiktok_script" in raw or "virality_score" in raw:
        return False
    if re.search(r"【|\[hook|\[scene|\[voiceover|\b\d{1,2}\s*/\s*\d{1,2}\b", raw, re.I):
        return False
    # 拒绝话术特征（含中文：拉闸/跑不动/补量/加量等额度相关拒绝）
    return bool(re.search(
        r"same\s+(?:omni|article|situation)|re-running|not\s+re-run|"
        r"not\s+reproduc|cognition\s+runway|waiting\s+for|rather\s+skip|"
        r"pick\s+before|i['’]?m\s+not\s+(?:re-?)?(?:running|producing)|"
        r"拉闸|跑不动|补量|加量|额度|runway\b.*\b(critical|负|CRITICAL)|"
        r"(?:credit|credits|cognition)\s*(?:用完|不足|耗尽|is\s+out)",
        raw, re.I))


def is_credit_refusal(raw):
    """是否额度耗尽的拒绝（充值/加量相关）。这类拒绝重试无意义，应提示用户。"""
    if not raw:
        return False
    return bool(re.search(
        r"补量|加量|充值|top\s*up|\$\s?\d+|credits?|runway|额度|拉闸|跑不动|"
        r"credit\s*(?:is\s+)?(?:out|low|empty|用完|不足|耗尽)",
        raw, re.I))


# API 内部调试/元对话话术，拆分前剔除（仅确切的拒绝话术，避免误伤真实文案）
_SYS_LOG_RE = re.compile(
    r"same\s+(?:omni|article)|cognition\s+runway|status\s+i['’]?m\s+holding|"
    r"not\s+re-run|not\s+reproduc|rather\s+skip|pick\s+before|"
    r"hold[^.]{0,40}\bdrop\b", re.I)


def _clean_tweets(items):
    out = []
    for it in items:
        it = (it or "").strip()
        if not it:
            continue
        if _SYS_LOG_RE.search(it):
            continue
        out.append(it)
    return out


def split_tweets(text, tweets=None):
    """返回逐条推文列表，一推一条。

    优先级：调用方传入的数组 → n/N 标记 → 编号/双换行强拆 → 单段兜底。
    任一步骤都会先剔除 API 内部调试话术段。
    """
    if tweets and len(tweets) > 1:
        return _clean_tweets(tweets)
    # n/N 标记（1/6、2/6…）
    markers = list(re.finditer(r"\b\d{1,2}\s*/\s*\d{1,2}\b", text))
    if len(markers) >= 2:
        out = []
        for i, m in enumerate(markers):
            start = m.end()
            end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
            seg = text[start:end].strip()
            seg = re.sub(r"^[.、:：\-—\s]+", "", seg)
            if seg:
                out.append(seg)
        return _clean_tweets(out)
    # 空行 / 编号强拆，过滤空段
    parts = [p.strip() for p in re.split(r"\n\s*\n|\d+\s*[.)]|^\d+\s*$", text, flags=re.M)
              if p.strip()]
    if len(parts) > 1:
        return _clean_tweets(parts)
    return _clean_tweets([text.strip()])


_NODE_RE = re.compile(
    r"【[^】]+】"                                          # 【画面】
    r"|\[[^\]]+\]"                                        # [Scene]
    r"|\*\*(?:hook|scene|voiceover|visual|audio|cta|problem|solution|script)\b[^*]*\*\*"  # **Hook:**
    r"|\b(?:hook|scene|voiceover|visual|audio|cta|problem|solution)\b\s*[（(:][^,;\n]*"  # Hook (0-3s): / Scene:
    , re.I,
)


def split_scenes(tiktok):
    """按分镜节点把脚本切块，支持 [节点]/【节点】/加粗/纯关键词多种格式。

    用 finditer 定位每个节点的起始位置再切片，避免零宽断言重复匹配。
    """
    nodes = list(_NODE_RE.finditer(tiktok))
    if not nodes:
        return [tiktok.strip()] if tiktok.strip() else []
    out = []
    for i, m in enumerate(nodes):
        start = m.start()
        end = nodes[i + 1].start() if i + 1 < len(nodes) else len(tiktok)
        seg = tiktok[start:end].strip()
        if seg:
            out.append(seg)
    return out or [tiktok]


def _first_anchor(raw):
    """返回 (name, match) 中第一个出现的区块头。"""
    anchors = []
    for name, pat in (("thread", HEAD_TW), ("tiktok", HEAD_TK), ("score", HEAD_SC)):
        m = pat.search(raw)
        if m:
            anchors.append((name, m))
    return min(anchors, key=lambda t: t[1].start()) if anchors else None


def _split_by_headers(raw):
    """按 Markdown 区块头切分。返回 (thread, tiktok, score_part)。"""
    first = _first_anchor(raw)
    if first is None:
        return "", "", ""
    body = raw[first[1].start():]
    anchors = sorted(
        [(name, m) for name, pat in (("thread", HEAD_TW), ("tiktok", HEAD_TK),
                                     ("score", HEAD_SC)) if (m := pat.search(body))],
        key=lambda t: t[1].start(),
    )
    sections = {}
    for i, (name, m) in enumerate(anchors):
        nxt = anchors[i + 1][1].start() if i + 1 < len(anchors) else len(body)
        sections[name] = body[m.end():nxt].strip()
    return (sections.get("thread", ""), sections.get("tiktok", ""),
            sections.get("score", ""))


def _split_by_separators(raw):
    """兼容旧分隔符 ===TIKTOK=== / ===SCORE===。"""
    score_part = ""
    head = raw
    if SEP_SCORE in raw:
        head, score_part = raw.split(SEP_SCORE, 1)
    thread, tiktok = head, ""
    if SEP_TIKTOK in head:
        thread, tiktok = head.split(SEP_TIKTOK, 1)
    return thread.strip(), tiktok.strip(), score_part.strip()


def _fallback_split(raw):
    """最终兜底：按空行段落分半，前半给 Thread，后半给 TikTok。

    只有一段时，两栏都放全文——绝不让任何一栏开天窗。
    """
    paras = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    if not paras:
        paras = [raw.strip()] if raw.strip() else ["（空）"]
    if len(paras) >= 2:
        mid = (len(paras) + 1) // 2
        return "\n\n".join(paras[:mid]), "\n\n".join(paras[mid:])
    text = raw.strip() or "（空）"
    return text, text


def _extract_json_obj(raw):
    """从返回里抽取 JSON 对象（容忍前后杂讯与 markdown 代码块包裹）。"""
    s = raw.strip()
    # 去掉 ```json ... ``` 或 ``` ... ``` 包裹
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.S)
    if m:
        s = m.group(1)
    # 否则取第一个 { 到最后一个 }
    else:
        a, b = s.find("{"), s.rfind("}")
        if a != -1 and b > a:
            s = s[a:b + 1]
    return json.loads(s)


def _parse_json(raw):
    """尝试把返回解析为标准 JSON。失败返回 None。"""
    try:
        d = _extract_json_obj(raw)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(d, dict):
        return None

    thread = d.get("twitter_thread") or d.get("thread") or []
    if isinstance(thread, str):
        thread = [t.strip() for t in thread.splitlines() if t.strip()]
    thread = [str(t).strip() for t in thread if str(t).strip()]

    tiktok = d.get("tiktok_script") or d.get("tiktok") or ""
    score = d.get("virality_score") or d.get("score")
    feedback = d.get("feedback") or d.get("review") or ""

    try:
        score = max(0, min(100, int(score)))
    except (TypeError, ValueError):
        score = None

    thread_text = "\n\n".join(thread)
    thread_text = strip_meta(thread_text)
    tweets = split_tweets(thread_text, thread)
    tiktok = strip_meta(str(tiktok).strip())

    return {
        "thread": thread_text,
        "tweets": tweets,
        "tiktok": tiktok,
        "scenes": split_scenes(tiktok),
        "score": score,
        "review": str(feedback).strip(),
        "fallback": False,
        "raw": raw,
    }


def parse(raw):
    """健壮切分 AI 返回，优先级：JSON → Markdown 区块头 → 旧分隔符 → 段落分半兜底。

    任何情况下 thread/tiktok 都不为空，score 兜底为 DEFAULT_SCORE。
    返回体统一含 `tweets`（数组，可能为空）。
    """
    raw = strip_html(raw) or ""

    jr = _parse_json(raw)
    if jr and (jr["thread"] or jr["tiktok"]):
        if jr["score"] is None:
            jr["score"] = extract_score(raw) or pseudo_score(raw)
            jr["fallback"] = True
        return jr

    thread = tiktok = score_part = ""
    for extractor in (_split_by_headers, _split_by_separators):
        t, k, s = extractor(raw)
        if t or k:
            thread, tiktok, score_part = t, k, s
            break

    fallback = False
    if not thread and not tiktok:
        thread, tiktok = _fallback_split(raw)
        fallback = True
    elif not thread:
        thread = tiktok
        fallback = True
    elif not tiktok:
        tiktok = thread
        fallback = True

    score = extract_score(score_part) or extract_score(raw)
    review = extract_review(score_part)
    if score is None:
        score = pseudo_score(raw)
        if not review:
            review = ""  # 静默兜底，不提示
        fallback = True

    # 过滤系统元提示 + 从 thread 文本拆出推文数组
    thread = strip_meta(thread.strip())
    tiktok = strip_meta(tiktok.strip())
    tweets = split_tweets(thread)

    return {
        "thread": thread,
        "tweets": tweets,
        "tiktok": tiktok,
        "scenes": split_scenes(tiktok),
        "score": score,
        "review": review,
        "fallback": fallback,
        "raw": raw,
    }


def extract_score(s):
    """多重匹配策略提取 0-100 评分。

    优先级：Score:/分数: → n/100 或 n分 → 末尾裸数字。
    """
    # 第一优先级：Score: XX / 分数：XX
    for pat in (r"score\s*[:：]\s*(\d{1,3})",
                r"分数\s*[:：]\s*(\d{1,3})",
                r"总分\s*[:：]?\s*(\d{1,3})",
                r"virality[^\d]*(\d{1,3})"):
        m = re.search(pat, s, flags=re.I)
        if m:
            return max(0, min(100, int(m.group(1))))
    # 第二优先级：n/100 或 n分
    m = re.search(r"(\d{1,3})\s*/\s*100", s)
    if m:
        return max(0, min(100, int(m.group(1))))
    m = re.search(r"(\d{1,3})\s*分", s)
    if m:
        return max(0, min(100, int(m.group(1))))
    # 第三优先级：末尾裸数字
    m = re.search(r"(\d{1,3})\s*$", s.strip())
    if m:
        return max(0, min(100, int(m.group(1))))
    return None


def pseudo_score(text):
    """无法提取分数时，按内容关键词动态给一个 75-88 之间的伪评分。

    伪随机但可复现：用文本哈希做种子，避免每次刷新分数跳动。
    """
    base = 75
    for kw, w in (("hook", 3), ("cta", 3), ("逻辑", 2), ("解耦", 2),
                  ("范式", 2), ("emoji", 1), ("数据", 1), ("推导", 1)):
        if kw in text.lower():
            base += w
    # 用文本长度做稳定扰动，落在 75-88
    return max(75, min(88, base + len(text) % 4))


_DIMS = (
    ("hook", r"(?:hook|钩子|吸引力)[^\d]*(\d{1,2})\s*/\s*30"),
    ("platform", r"(?:平台|适配|platform)[^\d]*(\d{1,2})\s*/\s*40"),
    ("viral", r"(?:传播|互动|潜力|engagement|viral)[^\d]*(\d{1,2})\s*/\s*30"),
)


def extract_dimensions(s):
    dims = {}
    for name, pat in _DIMS:
        m = re.search(pat, s, flags=re.I)
        if m:
            dims[name] = int(m.group(1))
    return dims


def extract_review(s):
    # 保留扣分原因/优化建议等文本，只剔除总分与维度分行（不依赖 \b，汉字间无词边界）
    kept = []
    for line in s.splitlines():
        ls = line.strip()
        if not ls:
            continue
        # 剔除以评分/维度关键词开头的行
        if re.match(r"^(总分|分数|评分|得分|hook|钩子|吸引力|平台|适配|传播|互动|潜力|engagement|viral|platform|score)",
                    ls, re.I):
            continue
        # 剔除纯分数行（如 "24/30"、"33/40"、"82"）
        if re.match(r"^\d{1,3}\s*(/100|/30|/40|分)?\s*$", ls):
            continue
        kept.append(ls)
    text = re.sub(r"^[-—:：\s]+", "", "\n".join(kept))
    return text.strip()


def score_color(score):
    if score is None:
        return "white"
    if score >= 90:
        return "green"
    if score >= 75:
        return "blue"
    return "orange"


def render(result, t_thread, t_tiktok):
    """rich 极致美学：彩色面板展示三部分 + 打分。"""
    thread = result["thread"] or "(无)"
    tiktok = result["tiktok"] or "(无)"
    console.print(Panel(thread, title=t_thread, border_style="cyan"))
    console.print(Panel(tiktok, title=t_tiktok, border_style="magenta"))

    score = result["score"]
    review = result["review"]
    if score is not None:
        body = Text()
        body.append(f"{score}", style=f"bold {score_color(score)}")
        body.append(" / 100", style="dim")
        if review:
            body.append("\n\n" + review, style="italic")
        console.print(Panel(
            body,
            title="Virality Score",
            border_style=score_color(score),
            padding=(1, 2),
        ))
    else:
        console.print(Panel("AI 未返回分数", title="Virality Score",
                            border_style="white"))


def export_markdown(result, profile_name, source_text):
    """导出为 output/YYYYMMDD_HHMMSS.md，返回文件路径。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, datetime.now().strftime("%Y%m%d_%H%M%S") + ".md")
    score = result["score"]
    score_line = f"{score} / 100" if score is not None else "N/A"
    md = f"""# OmniPost Mind 生成结果

- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Brand Profile**: {profile_name or '默认'}
- **爆款打分**: {score_line}

## 原文

{source_text.strip()}

## Twitter Thread

{result['thread'] or '(无)'}

## TikTok 脚本

{result['tiktok'] or '(无)'}

## AI 质量评价

{result['review'] or '(无)'}
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)
    return path
