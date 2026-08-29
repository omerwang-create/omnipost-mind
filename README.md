# OmniPost Mind 🧠

> **A Minds-powered content repurposing engine for the Creative Minds Jam.**
> Paste one long piece of writing, get back a Twitter thread, a TikTok script, and a virality score — in a voice your brand actually remembers.

OmniPost Mind turns a single long-form text into platform-native content for **Twitter/X** and **TikTok**, then scores it for virality. Its differentiator is **persistent style memory**: it uses the Minds **Context / Cognition** capability to remember a workspace's language, persona, and formatting preferences *across conversations*, so every regeneration stays on-brand without re-prompting.

---

## ✨ Features

- **Multi-platform generation** — one paste produces a tweet-by-tweet Twitter thread and a scene-by-scene TikTok script.
- **AI virality score** — a 0–100 score across three weighted dimensions (Hook appeal 30%, Platform fit 40%, Spread potential 30%), with deduction reasons and optimization tips.
- **Cognition-powered style memory** — language and persona preferences persist in Minds context, so the AI stays consistent across sessions.
- **Brand personas** — `Tech Geek` (cold, zero-emoji, data-driven) and `Marketing` (high-emoji, high-FOMO, strong CTA), each with hard style constraints.
- **Workspace isolation** — each project folder keeps its own persona, generation history, and its own Minds conversation, fully isolated from the others.
- **Bilingual UI** — English and 简体中文, with AI output locked to the selected language.
- **One-click export** — download the thread as `.txt` and the script as `.md`, with auto-saved Markdown archives.

---

## 🧠 How the Memory Works

The core idea is simple: **the Minds conversation *is* the memory node.**

OmniPost Mind doesn't store preferences in a local config and re-send them every time. Instead, it injects a compact **system context** — language directive + persona tone — into a persistent Minds conversation. Minds' Context/Cognition retains that context, so:

- Switch to `Marketing` → the AI remembers the high-FOMO, high-emoji voice on every later generation in that workspace.
- Switch to `Tech Geek` → the AI remembers zero emojis, academic tone, and data-driven formatting.
- Switch language to 中文 → all subsequent output follows.

Each workspace maps to its own isolated conversation (`omni-ws-{workspace}-{lang}-e{epoch}`), so different projects never leak style into each other.

---

## 🗂 Project Structure

```
omnipost-mind/
├── app.py          # Streamlit web UI + workspace/memory orchestration
├── minds.py        # Minimal Minds Builder Hub API client (REST)
├── lang.py         # Bilingual UI strings + system/convert prompts
├── brand.py        # Persona profile loader
├── content.py      # Response parsing, scoring, Markdown export
├── profiles/
│   ├── tech_geek.json
│   └── marketing.json
├── requirements.txt
└── .env.template   # Copy to .env and add your key
```

---

## ⚡ Demo Quickstart (60 seconds)

For judges / evaluators who want to see it running immediately — a one-minute path to a working demo:

1. **Get a free Minds key** — sign up at [build.hellominds.ai](https://build.hellominds.ai), grab your API key (a JWT starting with `eyJ0...`).
2. **Run three commands:**

```bash
git clone https://github.com/omerwang-create/omnipost-mind.git
cd omnipost-mind
pip install -r requirements.txt
```

3. **Add the key:**

```bash
echo "MINDS_API_KEY=YOUR_KEY_HERE" > .env
```

4. **Launch:**

```bash
streamlit run app.py
```

Open **http://localhost:8501**, pick a workspace + persona, paste any text, hit **Generate** — you'll see the virality score, Twitter thread, TikTok script, and export buttons within one prompt. That's the whole Cognition-memory flow, live.

> Demo tip: the first generation on a fresh workspace can take a minute or two (Minds cognition cold start) — subsequent ones are fast.
>
> ⚠️ **Before the demo, make sure the Minds account has cognition credits.** Minds runs on a credit model — an account with a negative/zero balance refuses to generate (the Mind replies with a top-up notice). If that happens, OmniPost Mind shows a clear "credits exhausted" message instead of garbled output, but to actually see generations you should top up first at [build.hellominds.ai](https://build.hellominds.ai).

---

## 🚀 Local Setup

### Prerequisites

- **Python 3.12** (recommended — see note below)
- A **Minds Builder Hub API key** — get one at [build.hellominds.ai](https://build.hellominds.ai)

> **Python version note:** `streamlit` pulls in `pandas`, which ships prebuilt wheels only for stable Python releases. If you're on Python 3.13+ beta, either use Python 3.12, or install via `uv` (which resolves a compatible version automatically).

### 1. Clone & set up a virtual environment

```bash
cd omnipost-mind
python3.12 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.template .env
```

Then edit `.env` and paste your Minds Builder Hub key:

```
MINDS_API_KEY=eyJ0eXAiOiJKV1Qi...
```

The app reads this key at startup — no other configuration is required. Your account's first Mind is auto-selected.

### 4. Run it

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 📖 Usage

1. **Pick a workspace** in the sidebar (or create a new folder).
2. **Choose a language** (English / 中文) and a **persona** (`Tech Geek` or `Marketing`).
3. **Paste your long text** and hit **Generate**.
4. Review the **virality score** ring, the **Twitter thread** cards, and the **TikTok scene** blocks.
5. **Download** each output, or scroll to the workspace history to review past generations.

---

## 🎨 The Personas

| Persona | Voice | Hard constraints |
| --- | --- | --- |
| **Marketing** 🔥 | Hype, FOMO, emotional payoff | 2–3 emojis per line, a rhetorical question every 3 sentences, high-pressure CTA |
| **Tech Geek** 🧊 | Cold, academic, systems-architect | 0 emojis, no exclamation marks, data-driven phrasing ("3 core variables", "40% optimization") |

---

## 🛠 Tech Stack

- **Python** + **Streamlit** — web UI
- **Minds Builder Hub API** — cognition/memory backend (`api.build.hellominds.ai`)
- **requests** — REST client
- **rich** — console formatting (fallback renderer)

---

## ⚠️ Known Notes

- **Cold start:** a brand-new workspace's first generation can take up to a few minutes while Minds cognition initializes. Subsequent generations are fast.
- **Workspace history** persists to `workspaces.json` in the project root, so it survives page refreshes.
- **Credits required:** Minds is a credit-based platform. An account with an exhausted/negative cognition balance will refuse to generate (the Mind replies with a top-up notice). Top up at [build.hellominds.ai](https://build.hellominds.ai) before judging; the app detects this case and shows a clear message — it never renders billing chatter as output.

---

Built for the **Creative Minds Jam**. 🏆
