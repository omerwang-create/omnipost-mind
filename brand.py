"""Brand Brain: load a persona profile and expose its tone instruction.

A profile is a JSON file in profiles/ with `name` and `tone_zh`/`tone_en`.
The tone instruction is merged with the language instruction in app.py and
injected into the Minds conversation (the memory node) on every request.
"""
import json, os

PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
ACTIVE = None


def load(name):
    global ACTIVE
    path = os.path.join(PROFILES_DIR, name + ".json")
    with open(path, encoding="utf-8") as f:
        ACTIVE = json.load(f)
    return ACTIVE


def list_profiles():
    return sorted(
        p[:-5] for p in os.listdir(PROFILES_DIR) if p.endswith(".json")
    )


def profile_meta(pid, lang_code):
    """Read a profile's display name + one-line desc without touching ACTIVE."""
    path = os.path.join(PROFILES_DIR, pid + ".json")
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("name", pid), d.get("desc_" + lang_code, "")


def tone(lang_code):
    """Return the active persona's tone instruction in the given language."""
    if ACTIVE is None:
        return ""
    return ACTIVE.get("tone_" + lang_code, "")


def desc(lang_code):
    """Return the active persona's one-line description in the given language."""
    if ACTIVE is None:
        return ""
    return ACTIVE.get("desc_" + lang_code, "")


def active_name():
    return ACTIVE["name"] if ACTIVE else None
