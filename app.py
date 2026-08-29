import time, re, os, json, threading
import streamlit as st
import minds, lang, brand, content


class _StopRender(Exception):
    """生成阶段发现无可渲染内容（额度拒绝等），中止本次渲染而不崩溃。"""


st.set_page_config(page_title="OmniPost Mind", page_icon="🧠", layout="wide")

# ---------- 设计系统：内容变形工坊（浅色主题 · 柔和灰白底 + 层次卡片流） ----------
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=LXGW+WenKai&family=Space+Grotesk:wght@400;500;700&display=swap');

  :root {
    --bg: #f8fafc;
    --ink: #1e293b;
    --dim: #64748b;
    --indigo: #4f6ef7;
    --pink: #ec4899;
    --gold: #f59e0b;
    --red: #ef4444;
    --surface: #ffffff;
    --border: #e2e8f0;
    --input-border: #cbd5e1;
  }

  html, body, [class*="css"] {
    font-family: 'LXGW WenKai', 'Kaiti SC', 'STKaiti', serif;
    color: var(--ink);
  }
  .num { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; }

  /* 背景：浅灰白 + 两道极淡柔光（保留分裂中轴的意境） */
  .stApp {
    background:
      linear-gradient(rgba(79,110,247,0.05), rgba(79,110,247,0.05)) center/1px 100% no-repeat,
      radial-gradient(1000px 700px at 80% -10%, rgba(79,110,247,0.07), transparent 60%),
      radial-gradient(900px 600px at -5% 40%, rgba(236,72,153,0.05), transparent 55%),
      var(--bg);
  }

  h1, h2, h3 { letter-spacing: -0.015em; line-height: 1.25; color: var(--ink); }

  /* 侧边栏：纯白 + 细腻浅灰描边 + 右侧轻投影，营造浮动层次 */
  [data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid var(--border);
    box-shadow: 2px 0 24px rgba(30,41,59,0.06);
  }
  [data-testid="stSidebar"] * { color: var(--ink); }
  [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: var(--dim); }

  /* 卡片：纯白底 + 浅灰描边 + 内阴影浮起感 */
  .omni-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow:
      inset 0 1px 0 rgba(255,255,255,0.9),
      0 1px 3px rgba(30,41,59,0.06),
      0 8px 24px rgba(30,41,59,0.06);
  }

  /* 品牌字标：靛蓝→品红渐变（左鸟右影，呼应分裂） */
  .omni-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.5rem; font-weight: 700; letter-spacing: -0.03em;
    background: linear-gradient(110deg, #1e293b 12%, var(--indigo) 55%, var(--pink) 92%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .omni-sub { color: var(--dim); }

  /* 按钮：主按钮靛蓝→品红，按压瞬间反馈 */
  div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--indigo), var(--pink));
    color: #fff; border: none; border-radius: 12px;
    font-weight: 700; padding: 0.55rem 2.2rem;
    box-shadow: 0 6px 20px rgba(79,110,247,0.30);
    transition: transform 0.12s ease, box-shadow 0.12s ease, filter 0.12s ease;
  }
  div.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 12px 28px rgba(79,110,247,0.40);
    filter: brightness(1.05);
  }
  div.stButton > button[kind="primary"]:active { transform: scale(0.97); }

  /* 次级按钮（删除等危险操作）：红色 + 白字 */
  div.stButton > button[kind="secondary"] {
    background: #fee2e2; border: 1px solid #fecaca; border-radius: 12px;
    color: #dc2626; font-weight: 700; padding: 0.4rem 1.4rem;
    transition: transform 0.12s ease, background 0.12s ease;
  }
  div.stButton > button[kind="secondary"]:hover {
    background: #fecaca; transform: translateY(-1px);
  }
  div.stButton > button[kind="secondary"]:active { transform: scale(0.97); }

  /* 分裂入场：Thread 左入 / TikTok 右入 / 分数弹出 */
  @keyframes splitLeft { from { opacity: 0; transform: translateX(-26px); } to { opacity: 1; transform: none; } }
  @keyframes splitRight { from { opacity: 0; transform: translateX(26px); } to { opacity: 1; transform: none; } }
  @keyframes popIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: none; } }
  .split-l { animation: splitLeft 0.5s cubic-bezier(0.22, 1, 0.36, 1) both; }
  .split-r { animation: splitRight 0.5s cubic-bezier(0.22, 1, 0.36, 1) 0.08s both; }
  .pop { animation: popIn 0.4s cubic-bezier(0.22, 1, 0.36, 1) both; }

  /* 爆款环形仪表：轨道改浅灰（浅色底） */
  .ring {
    position: relative; width: 116px; height: 116px; border-radius: 50%;
    background: conic-gradient(var(--c) calc(var(--p) * 1%), #eef2f7 0);
    -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 11px), #000 calc(100% - 10px));
    mask: radial-gradient(farthest-side, transparent calc(100% - 11px), #000 calc(100% - 10px));
    flex: none;
  }
  .ring b {
    position: absolute; inset: 0; display: grid; place-items: center;
    font-family: 'Space Grotesk'; font-size: 1.9rem; font-weight: 700; color: var(--c);
  }

  /* 进度条渐变 */
  .stProgress > div > div > div > div { background: linear-gradient(90deg, var(--indigo), var(--pink)); }

  /* 侧边栏胶囊分段控件 */
  [data-testid="stRadio"] > div { gap: 4px; }
  [data-testid="stRadio"] label {
    background: #f1f5f9;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 3px 14px;
  }
  [data-testid="stRadio"] label:has(input:checked) {
    background: rgba(79,110,247,0.12);
    border-color: rgba(79,110,247,0.55);
  }

  /* 输入框：纯白 + 深一档描边，光标文字清晰可见 */
  textarea {
    background: #ffffff !important;
    border: 1px solid var(--input-border) !important;
    border-radius: 12px !important;
    color: var(--ink) !important;
  }

  ::-webkit-scrollbar { width: 10px; height: 10px; }
  ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 999px; }
  ::-webkit-scrollbar-track { background: transparent; }

  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { transition: none !important; animation: none !important; }
  }

  /* 统一 stroke 图标 + 对齐行内文字 */
  .ic { width: 1.1em; height: 1.1em; stroke: currentColor; fill: none;
        stroke-width: 2; stroke-linecap: round; stroke-linejoin: round;
        vertical-align: -0.18em; }

  /* 单条推文卡片 */
  .tweet-card {
    background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
    padding: 16px; margin-bottom: 12px;
    box-shadow: 0 1px 3px rgba(30,41,59,0.05);
  }
  .tweet-idx { color: #64748b; font-family: 'Space Grotesk', sans-serif;
               font-size: 0.8rem; font-weight: 600; }

  /* TikTok 节点加粗 */
  .tk-node { font-weight: 700; color: #ec4899; }

  /* ===== 终检美化：全局节奏与细节 ===== */
  .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1180px; }
  .omni-logo { margin-bottom: 2px; }
  .omni-sub { margin-bottom: 18px; }

  /* 输入区：标签加重 + 聚焦光圈 */
  [data-testid="stTextArea"] label p { font-weight: 700; color: var(--ink); font-size: 1.02rem; }
  textarea:focus {
    border-color: var(--indigo) !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,0.18) !important;
    outline: none !important;
  }

  /* 侧边栏输入框同款描边与聚焦 */
  [data-testid="stSidebar"] input {
    background: #ffffff !important;
    border: 1px solid var(--input-border) !important;
    border-radius: 10px !important;
    color: var(--ink) !important;
  }
  [data-testid="stSidebar"] input:focus {
    border-color: var(--indigo) !important;
    box-shadow: 0 0 0 3px rgba(79,110,247,0.15) !important;
  }

  /* 下载按钮：幽灵样式，不抢主按钮 */
  div.stDownloadButton > button {
    background: #ffffff; border: 1px solid var(--border); border-radius: 10px;
    color: var(--dim); font-weight: 500; padding: 0.3rem 1rem; font-size: 0.9rem;
    transition: border-color 0.12s ease, color 0.12s ease;
  }
  div.stDownloadButton > button:hover { border-color: var(--indigo); color: var(--indigo); }

  /* 推文聊天气泡：白卡圆角微投影 */
  [data-testid="stChatMessage"] {
    background: #ffffff; border: 1px solid var(--border); border-radius: 14px;
    padding: 10px 14px; box-shadow: 0 1px 3px rgba(30,41,59,0.05);
  }

  /* Expander 卡片化 */
  [data-testid="stExpander"] {
    background: #ffffff; border: 1px solid var(--border); border-radius: 14px;
    box-shadow: 0 1px 3px rgba(30,41,59,0.05); overflow: hidden;
  }
  [data-testid="stExpander"] summary { font-weight: 600; }

  /* 分隔线更轻、更克制 */
  hr { border-color: var(--border); opacity: 0.7; }

  /* 分数环：随环形的柔和落影 */
  .ring { filter: drop-shadow(0 6px 14px rgba(30,41,59,0.10)); }

  /* 状态卡胶囊 */
  .ws-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: #f1f5f9; border: 1px solid var(--border); border-radius: 999px;
    padding: 4px 14px; color: var(--dim); font-size: 0.92rem;
  }
</style>
""", unsafe_allow_html=True)


def get_mind_guard():
    try:
        ms = minds.list_minds()
        # 优先选 mastermind（通用智力型，能遵守转换提示词）；
        # 预设人格 Mind（如 gtm/marketing 搭档）有强开场白会污染输出
        for m in ms:
            if "mastermind" in (m.get("name") or "").lower():
                return m
        return ms[0] if ms else None
    except Exception:
        return None


def system_context():
    parts = [lang.system_prompt()]
    tone = brand.tone(lang.LANG)
    if tone:
        parts.append(tone)
    return "\n\n".join(parts)


# 统一 stroke 图标（Lucide 风格路径），避免 emoji 当图标
_ICONS = {
    "brain": '<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44A2.5 2.5 0 0 1 2.5 17.5V14a2.5 2.5 0 0 1 2-4A2.5 2.5 0 0 1 9.5 6z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44A2.5 2.5 0 0 0 21.5 17.5V14a2.5 2.5 0 0 0-2-4A2.5 2.5 0 0 0 14.5 6z"/>',
    "bird": '<path d="M16 7h.01"/><path d="M3.4 18H12a8 8 0 0 0 8-8V7a4 4 0 0 0-7.28-2.3L2 20"/><path d="m20 7 2 .5-2 .5"/><path d="M10 18v3"/><path d="M14 17.75V21"/><path d="M7 18a6 6 0 0 0 3.84-10.61"/>',
    "video": '<path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "spark": '<path d="M12 3v3"/><path d="M12 18v3"/><path d="M3 12h3"/><path d="M18 12h3"/><path d="M5.6 5.6l2.1 2.1"/><path d="M16.3 16.3l2.1 2.1"/><path d="M5.6 18.4l2.1-2.1"/><path d="M16.3 7.7l2.1-2.1"/>',
}


def icon(name, color=None, size=None):
    style = f' style="color:{color};font-size:{size}"' if color or size else ""
    return (f'<svg class="ic" viewBox="0 0 24 24" aria-hidden="true"{style}>'
            f'{_ICONS[name]}</svg>')


def reply(alias, text, timeout=360):
    # 以本消息的 messageId 为基准：只认它之后出现的新 Mind 回复，
    # 彻底规避预热回复 / 旧回复被误当成生成结果（历史按最新在前排序）
    sent = minds.send_message(alias, text)
    sent_id = sent.get("messageId")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            for row in minds.get_history(alias, 20):
                if row["senderType"] == 0 and row["id"] != sent_id:
                    return content.strip_html(row["messageText"])
        except Exception:
            # 单次轮询失败（SSL/网络抖动）静默跳过，不中断等待
            pass
        time.sleep(2)
    raise TimeoutError(f"Mind did not reply within {timeout}s")


def active_alias():
    """按「工作区 key × 语言 × epoch」隔离 conversation。

    epoch 持久化在每个工作区字典里：一旦该文件夹的 conversation 被 AI
    「记住要拒绝」（meta-refusal），epoch+1 换全新会话并落盘，之后所有
    生成都走新会话——记忆既按文件夹物理隔离，又能干净重置。
    """
    ws_key = st.session_state.get("current_ws", "default")
    epoch = st.session_state.workspaces.get(ws_key, {}).get("epoch", 0)
    return f"omni-ws-{ws_key}-{lang.LANG}-e{epoch}"


def ensure_active_conversation():
    mind = st.session_state.get("mind")
    if mind:
        minds.ensure_conversation(active_alias(), mind["mindId"])


# ============ 冷启动预热 ============
# 新会话首次回复需 180-300s（cognition 冷启动）。预热 = 启动/切换工作区时
# 后台建会话并抛一句问候，让它先把首响烧掉；真正点击生成时基本秒回。
# 注意：预热只发消息、不等待回复。生成由 reply() 以本消息 messageId 为基准，
# 天然跳过预热回复，无需记录。
_WARMED = set()
_WARM_MSG = {
    "zh": "你好，OmniPost 会话已就绪。",
    "en": "Hello, OmniPost session is ready.",
}


def warm_conversation(alias, mind_id):
    if alias in _WARMED:
        return
    _WARMED.add(alias)
    try:
        minds.ensure_conversation(alias, mind_id)
        minds.send_message(alias, _WARM_MSG[lang.LANG])
    except Exception:
        _WARMED.discard(alias)  # 失败则下次再试


def start_warmup():
    if "mind" not in st.session_state:
        return
    threading.Thread(
        target=warm_conversation,
        args=(active_alias(), st.session_state["mind"]["mindId"]),
        daemon=True,
    ).start()


# ============ 工作区（Workspace）记忆隔离 ============
# 每个工作区是一个独立数据字典：
#   { name, profile(绑定人设), history([{ts, source, thread, tiktok, score, review}]) }
# 切换工作区 = 切换不同数据，历史对话记忆 / 人设 / 生成记录全部隔离。
# 数据落盘到 workspaces.json，浏览器刷新后依然保留。
WS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workspaces.json")

PRESET_WORKSPACES = [
    {"key": "tech", "name": "📁 极客技术专栏", "profile": "tech_geek"},
    {"key": "marketing", "name": "📁 品牌营销爆款", "profile": "marketing"},
]


def _load_workspaces():
    """从磁盘加载工作区；文件不存在或损坏时回退到预设。"""
    try:
        with open(WS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("workspaces"):
            # 兼容旧文件：补齐缺失的 epoch 字段
            for w in data["workspaces"].values():
                w.setdefault("epoch", 0)
            return data
    except (OSError, ValueError):
        pass
    ws = {p["key"]: {"name": p["name"], "profile": p["profile"], "history": [],
                     "epoch": 0}
          for p in PRESET_WORKSPACES}
    return {"workspaces": ws, "current_ws": PRESET_WORKSPACES[0]["key"]}


def _save_workspaces():
    """把当前工作区状态写回磁盘。"""
    try:
        with open(WS_FILE, "w", encoding="utf-8") as f:
            json.dump({"workspaces": st.session_state.workspaces,
                        "current_ws": st.session_state.current_ws},
                       f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def init_workspaces():
    if "workspaces" not in st.session_state:
        data = _load_workspaces()
        st.session_state.workspaces = data["workspaces"]
        st.session_state.current_ws = data["current_ws"]
        # 若 current_ws 指向不存在的 key（文件损坏），回退到第一个
        if st.session_state.current_ws not in st.session_state.workspaces:
            st.session_state.current_ws = list(st.session_state.workspaces)[0]


def current_workspace():
    return st.session_state.workspaces[st.session_state.current_ws]


def new_ws_key():
    """生成不冲突的新工作区 key。

    用现有 key 的最大序号 +1，避免时间戳在同一秒内撞出相同 key
    导致两个文件夹共用 conversation、记忆串乱。
    """
    nums = []
    for k in st.session_state.workspaces:
        m = re.search(r"ws(\d+)$", k)
        if m:
            nums.append(int(m.group(1)))
    return f"ws{max(nums) + 1}" if nums else "ws1"


init_workspaces()


# ---------- 侧边栏：记忆控制台中枢 ----------
with st.sidebar:
    st.markdown(f'<h2 style="display:flex;align-items:center;gap:8px;margin-top:0">'
                f'{icon("brain", "#4f6ef7")}{lang.t("sidebar_title")}</h2>',
                unsafe_allow_html=True)

    # ==== 工作区管理（顶部）====
    st.markdown(f"**{lang.t('ws_label')}**")
    ws_names = [w["name"] for w in st.session_state.workspaces.values()]
    ws_keys = list(st.session_state.workspaces.keys())
    cur_idx = ws_keys.index(st.session_state.current_ws)
    # key 绑定当前工作区：切换后 widget 重建，index 才能生效（否则 selectbox 会沿用旧值）
    ws_choice = st.selectbox(
        lang.t("ws_label"), ws_names, index=cur_idx,
        key=f"ws_select_{st.session_state.current_ws}")
    chosen_key = ws_keys[ws_names.index(ws_choice)]
    if chosen_key != st.session_state.current_ws:
        st.session_state.current_ws = chosen_key
        # 切换工作区 = 加载该文件夹绑定的独立人设
        st.session_state["_last_profile"] = st.session_state.workspaces[chosen_key]["profile"]
        brand.load(st.session_state["_last_profile"])
        _save_workspaces()  # 落盘当前选择
        st.rerun()

    # 新建文件夹（用 form 确保 text_input 值随提交一起送达，避免点按钮读到空值）
    with st.form("new_ws_form", clear_on_submit=True):
        new_name = st.text_input(lang.t("ws_new_ph"), key="ws_new_name")
        submitted = st.form_submit_button(lang.t("ws_new_btn"))
    if submitted:
        name = (new_name or "").strip()
        if name:
            key = new_ws_key()
            st.session_state.workspaces[key] = {
                "name": f"📁 {name}", "profile": "marketing", "history": [],
                "epoch": 0}
            st.session_state.current_ws = key
            st.session_state["_last_profile"] = "marketing"
            brand.load("marketing")
            st.session_state.pop("ws_new_name", None)
            _save_workspaces()  # 落盘，刷新后仍在
            st.rerun()
        else:
            st.warning(lang.t("ws_new_empty"))

    # 删除当前文件夹（仅自定义文件夹可删，预设两个保留）
    preset_keys = {p["key"] for p in PRESET_WORKSPACES}
    if st.session_state.current_ws not in preset_keys:
        if st.button(lang.t("ws_delete"), key="ws_delete_btn", type="secondary"):
            name = st.session_state.workspaces[st.session_state.current_ws]["name"]
            if st.session_state.get("ws_delete_confirm") is True:
                # 二次确认后执行删除
                del st.session_state.workspaces[st.session_state.current_ws]
                st.session_state.current_ws = PRESET_WORKSPACES[0]["key"]
                st.session_state["_last_profile"] = PRESET_WORKSPACES[0]["profile"]
                brand.load(PRESET_WORKSPACES[0]["profile"])
                st.session_state.pop("ws_delete_confirm", None)
                _save_workspaces()
                st.rerun()
            else:
                st.session_state["ws_delete_confirm"] = True
                st.warning(lang.t("ws_delete_confirm", name=name))

    st.markdown("---")

    lang_code = st.radio(
        lang.t("lang_label"),
        [lang.t("lang_zh"), lang.t("lang_en")],
        index=0 if lang.LANG == "zh" else 1,
        key="lang",
    )
    lang.set_lang("zh" if lang_code == lang.t("lang_zh") else "en")

    profiles = brand.list_profiles()
    label_map = {f"{brand.profile_meta(p, lang.LANG)[0]} — {brand.profile_meta(p, lang.LANG)[1]}": p
                 for p in profiles}

    # 工作区绑定的默认人设（进入该工作区时生效）
    ws_profile = current_workspace()["profile"]
    if st.session_state.get("_last_profile") is None:
        brand.load(ws_profile)
        st.session_state["_last_profile"] = ws_profile

    # key 绑定工作区：切换文件夹后 radio 重建，正确显示该工作区绑定的人设
    label = st.radio(
        lang.t("profile_label"),
        list(label_map.keys()),
        index=profiles.index(st.session_state.get("_last_profile", ws_profile)),
        key=f"profile_{st.session_state.current_ws}",
    )
    pid = label_map[label]
    if st.session_state.get("_last_profile") != pid:
        brand.load(pid)
        st.session_state["_last_profile"] = pid
        # 人设切换也更新当前工作区的绑定
        st.session_state.workspaces[st.session_state.current_ws]["profile"] = pid
        _save_workspaces()  # 落盘人设绑定
        st.toast(lang.t("profile_switched", name=brand.active_name()), icon="🎭")

    st.markdown("---")
    st.markdown(
        f'<div class="omni-card" style="padding:10px 16px">'
        f'<span style="color:#64748b;font-size:0.85rem">{lang.t("mode_label")}: </span>'
        f'<span style="color:#4f6ef7;font-weight:700">{brand.active_name() or lang.t("no_profile")}</span>'
        f'</div>', unsafe_allow_html=True)

    # 惰性连接 Minds（首次渲染才建会话）
    if "mind" not in st.session_state:
        with st.spinner(lang.t("connecting")):
            mind = get_mind_guard()
            st.session_state["mind"] = mind
    else:
        # 会话已连：后台预热当前工作区，烧掉冷启动
        start_warmup()

# ---------- 主工作区 ----------
st.markdown(
    f'<div class="omni-logo">{icon("brain", "#4f6ef7", "1.6rem")} OmniPost Mind</div>',
    unsafe_allow_html=True)
st.markdown(f'<div class="omni-sub">{lang.t("logo_sub")}</div>', unsafe_allow_html=True)

# 当前工作区 + 人设 + 语言的醒目状态卡
ws_name = current_workspace()["name"]
st.markdown(
    f'<div class="omni-card" style="padding:12px 20px;display:flex;gap:12px;'
    f'align-items:center;flex-wrap:wrap">'
    f'<span class="ws-chip">{lang.t("ws_path")} '
    f'<b style="color:#0f766e">{ws_name}</b></span>'
    f'<span class="ws-chip">{icon("user")} {lang.t("active_profile")} '
    f'<b style="color:#4f6ef7">{brand.active_name() or lang.t("no_profile")}</b></span>'
    f'<span class="ws-chip" style="margin-left:auto">{icon("globe")} {lang.t("active_lang")} '
    f'<b style="color:#ec4899">{lang_code}</b></span>'
    f'</div>', unsafe_allow_html=True)

source = st.text_area(
    lang.t("input_label"),
    height=220,
    placeholder=lang.t("input_placeholder"),
)
generate = st.button(lang.t("generate"), type="primary")

if generate:
    if not source.strip():
        st.warning(lang.t("empty_warning"))
    elif "mind" not in st.session_state:
        st.error(lang.t("mind_fail"))
    else:
        ensure_active_conversation()
        alias = active_alias()
        prompt = system_context() + "\n\n" + lang.convert_prompt() + source
        try:
            with st.spinner(lang.t("generating")):
                raw = reply(alias, prompt)
            # 额度拒绝话术（含充值推销）独立检测，不依赖元话术模式——优先拦截
            if content.is_credit_refusal(raw):
                st.error(lang.t("credit_refusal"))
                raise _StopRender()
            # 其他「拒绝/元对话」：换全新会话重试一次
            if content.is_meta_refusal(raw):
                ws = st.session_state.workspaces[st.session_state.current_ws]
                ws["epoch"] = ws.get("epoch", 0) + 1
                _save_workspaces()  # 落盘新的 epoch，记忆干净且持久
                minds.ensure_conversation(active_alias(),
                                          st.session_state["mind"]["mindId"])
                with st.spinner(lang.t("generating")):
                    raw = reply(active_alias(), prompt)
                if content.is_meta_refusal(raw) or content.is_credit_refusal(raw):
                    st.error(lang.t("credit_refusal")
                             if content.is_credit_refusal(raw) else lang.t("timeout"))
                    raise _StopRender()
            # 调试：终端打印 Minds API 原始返回
            print("=" * 60)
            print("[DEBUG] Minds API 原始返回 response_text:")
            print(raw)
            print("=" * 60)
            result = content.parse(raw)

            # 打分 + 建议
            score = result["score"]
            if score is not None:
                color = content.score_color(score)
                c = {"green": "#16a34a", "blue": "#2563eb", "orange": "#f97316"}[color]
                st.markdown(
                    f'<div class="omni-card pop" style="display:flex;align-items:center;gap:22px">'
                    f'<div class="ring" style="--c:{c};--p:{score}">'
                    f'<b>{score}</b></div>'
                    f'<div><h2 style="margin:0;display:flex;align-items:center;gap:8px">'
                    f'{icon("gauge", c)} {lang.t("score_title")}</h2>'
                    f'<div class="num" style="color:{c};font-weight:700">{score} / 100</div>'
                    f'<p style="color:#64748b;margin:8px 0 0">{result["review"] or ""}</p>'
                    f'</div></div>', unsafe_allow_html=True)
                st.progress(score / 100.0)
            else:
                st.markdown(
                    f'<div class="omni-card">'
                    f'<h3 style="margin:0">{icon("gauge", "#94a3b8")} {lang.t("score_title")}</h3>'
                    f'<p style="color:#64748b;margin:8px 0 0">'
                    f'{lang.t("score_missing")}</p></div>', unsafe_allow_html=True)

            # 左右分栏
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    f'<h3 style="margin:0 0 10px;color:#6c8cff;display:flex;'
                    f'align-items:center;gap:8px">{icon("bird")} {lang.t("thread")}</h3>',
                    unsafe_allow_html=True)
                # 强制拆分为逐条推文：数组 → n/N → 空行/编号，一推一卡片
                tweets = content.split_tweets(result["thread"] or "",
                                              result.get("tweets") or [])
                thread_txt = "\n\n".join(
                    f"{i}/{len(tweets)} {tw}" for i, tw in enumerate(tweets, 1)
                ) or (result["thread"] or "")
                st.download_button(
                    lang.t("download") + " .txt",
                    data=thread_txt.encode("utf-8"),
                    file_name="twitter_thread.txt",
                    mime="text/plain",
                    key="dl_thread",
                )
                for idx, tw in enumerate(tweets, 1):
                    st.markdown(
                        f'<div class="tweet-card">'
                        f'<span class="tweet-idx">Tweet #{idx}</span>'
                        f'<br><br>{tw}</div>',
                        unsafe_allow_html=True)
            with c2:
                st.markdown(
                    f'<h3 style="margin:0 0 10px;color:#ff4d8d;display:flex;'
                    f'align-items:center;gap:8px">{icon("video")} {lang.t("tiktok")}</h3>',
                    unsafe_allow_html=True)
                tiktok_txt = result["tiktok"] or ""
                st.download_button(
                    lang.t("download") + " .md",
                    data=tiktok_txt.encode("utf-8"),
                    file_name="tiktok_script.md",
                    mime="text/markdown",
                    key="dl_tiktok",
                )
                scenes = result.get("scenes") or []
                if len(scenes) >= 2:
                    for i, sc in enumerate(scenes, 1):
                        # 标题取首行节点，正文去掉该行，避免重复打印
                        lines = sc.splitlines()
                        label = lines[0][:40] if lines else f"分镜 {i}"
                        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
                        with st.expander(f"🎬 {label}", expanded=(i == 1)):
                            st.markdown(body or sc)
                else:
                    tk = scenes[0] if scenes else tiktok_txt
                    tk = re.sub(r"(【[^】]+】|\[[^\]]+\])",
                                r'<span class="tk-node">\1</span>', tk)
                    st.markdown(
                        f'<div class="omni-card" style="color:#334155;line-height:1.7">'
                        f'{tk.replace(chr(10), "<br>")}'
                        f'</div>', unsafe_allow_html=True)

            # 导出
            path = content.export_markdown(result, brand.active_name(), source)

            # ==== 工作区隔离：把本次生成记录存入当前文件夹的独立 history ====
            current_workspace()["history"].append({
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source": source.strip()[:120],
                "thread": result["thread"],
                "tiktok": result["tiktok"],
                "score": score,
                "profile": brand.active_name(),
            })
            _save_workspaces()  # 落盘历史记录
            st.success(lang.t("exported", path=path))
        except TimeoutError:
            st.error(lang.t("timeout"))
        except _StopRender:
            pass  # 额度拒绝等已在 st.error 提示，不再渲染

# ============ 主界面底部：当前工作区历史 ============
st.markdown("---")
with st.expander(lang.t("ws_history"), expanded=False):
    hist = current_workspace()["history"]
    if not hist:
        st.caption(lang.t("ws_empty"))
    else:
        for i, item in enumerate(reversed(hist), 1):
            # 用「从末尾倒数第 i 条」定位，避免时间戳相同的记录误删
            idx = len(hist) - i
            col, del_col = st.columns([5, 1])
            with col:
                st.markdown(
                    f'<div class="omni-card" style="padding:12px 16px;margin-bottom:10px">'
                    f'<div style="display:flex;gap:16px;align-items:center">'
                    f'<span style="color:#94a3b8;font-size:0.8rem">{item["ts"]}</span>'
                    f'<span style="color:#4f6ef7">{item["profile"]}</span>'
                    f'<b class="num" style="color:#16a34a">{item["score"]}/100</b>'
                    f'</div>'
                    f'<p style="color:#334155;margin:6px 0 0">原文：{item["source"]}</p>'
                    f'</div>', unsafe_allow_html=True)
            with del_col:
                if st.button(lang.t("ws_del_rec"), key=f"del_hist_{st.session_state.current_ws}_{idx}"):
                    del current_workspace()["history"][idx]
                    _save_workspaces()
                    st.rerun()
