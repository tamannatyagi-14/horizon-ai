import html as _html
import re
from datetime import date

import streamlit as st

from agents.researcher import researcher_node
from agents.writer import writer_node
from agents.editor import editor_node
from agents.fact_checker import fact_checker_node
from agents.platform_adapter import platform_adapter_node
from agents.slop_detector import slop_node
from agents.engagement import engagement_node
from agents.strategist import strategist_node, status as strategist_status
from agents.hook_writer import regenerate_hook
from utils.pdf_export import build_pdf
from utils import cache, history_db

st.set_page_config(
    page_title="Horizon AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CYAN, PURPLE, PINK, GREEN, GOLD = "#00D4FF", "#7C3AFF", "#FF2D8F", "#4DFFB0", "#FFD23F"
GRAD = "linear-gradient(135deg,#00D4FF,#7C3AFF,#FF2D8F)"

st.markdown(
    """
<style>
html, body, .stApp { background:#080B14 !important; color:#C4D4FF; }
section[data-testid="stSidebar"] { display:none !important; }
#MainMenu, footer, header { visibility:hidden; }
.block-container { padding:1.2rem 1.5rem 2rem 1.5rem !important; max-width:100% !important; }
::-webkit-scrollbar { width:4px; }
::-webkit-scrollbar-thumb { background:#1A1A2A; border-radius:4px; }

/* Primary buttons = gradient, secondary = dark outline */
button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background:linear-gradient(135deg,#00D4FF,#7C3AFF,#FF2D8F) !important;
  color:#fff !important; border:none !important; border-radius:22px !important;
  font-weight:600 !important; font-size:13px !important; padding:6px 14px !important;
}
button[kind="secondary"], button[data-testid="stBaseButton-secondary"] {
  background:#0C0E1A !important; color:#8A9AC0 !important;
  border:1px solid #1E2036 !important; border-radius:22px !important;
  font-size:13px !important; padding:6px 14px !important;
}
button[kind="secondary"]:hover, button[data-testid="stBaseButton-secondary"]:hover {
  border-color:#7C3AFF !important; color:#C4D4FF !important;
}
button:disabled { opacity:.45 !important; }

/* Sidebar nav buttons */
[class*="st-key-nav_"] button {
  justify-content:flex-start !important; text-align:left !important;
  background:transparent !important; border:1px solid transparent !important;
  color:#5A5A88 !important; border-radius:10px !important;
  padding:8px 12px !important; font-size:14px !important; font-weight:400 !important;
}
[class*="st-key-nav_"] button:hover { background:#0F111C !important; color:#C4D4FF !important; }
[class*="st-key-nav_"] button[kind="primary"], [class*="st-key-nav_"] button[data-testid="stBaseButton-primary"] {
  background:#10121C !important; border:1px solid #00D4FF40 !important;
  color:#00D4FF !important; font-weight:500 !important;
}

.stTextArea textarea {
  background:#0A0C16 !important; color:#E0E8FF !important;
  border:1px solid #1E2036 !important; border-radius:12px !important; font-size:14px !important;
}
div[data-baseweb="select"] > div {
  background:#0A0C16 !important; border:1px solid #1E2036 !important;
  border-radius:22px !important; color:#C4D4FF !important;
}
.stCheckbox label p, .stRadio label p { color:#C4D4FF !important; font-size:13px !important; }

.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid #1A1A2A; }
.stTabs [data-baseweb="tab"] { color:#4A4A70 !important; font-size:13px !important; }
.stTabs [aria-selected="true"] { color:#E0E8FF !important; }
.stTabs [data-baseweb="tab-highlight"] { background:#7C3AFF !important; }

/* Copy box: readable font + copy icon always visible */
div[data-testid="stCode"] pre, .stCode pre { background:#0A0C16 !important; border:1px solid #1E2036; border-radius:12px; }
div[data-testid="stCode"] code { font-family:"Segoe UI","Source Sans",sans-serif !important; font-size:14px !important; line-height:1.7 !important; }
[data-testid="stCode"] div:has([data-testid="stElementToolbarButton"]),
[data-testid="stCode"] [data-testid="stElementToolbarButton"],
[data-testid="stCode"] [data-testid="stElementToolbarButton"] * { visibility:visible !important; opacity:1 !important; }
[data-testid="stCode"] button[data-testid="stBaseButton-elementToolbar"] { color:#00D4FF !important; background:#0F1220 !important; border-radius:8px !important; }

div[data-testid="stSpinner"] { color:#8A9AC0; }
div[data-testid="stExpander"] { border:1px solid #1A1A2A !important; border-radius:12px !important; background:#0C0E1A; }
hr { border-color:#1A1A2A !important; }
</style>
""",
    unsafe_allow_html=True,
)

S = st.session_state

# (page key, material icon, label, accent colour)
NAV = [
    ("home", ":material/explore:", "Home", CYAN),
    ("pipelines", ":material/hub:", "Pipelines", PURPLE),
    ("history", ":material/history:", "History", PINK),
    ("settings", ":material/tune:", "Settings", GREEN),
]
_nav_css = "".join(
    f"""
.st-key-nav_{k} [data-testid="stIconMaterial"] {{ color:{c} !important; font-size:20px !important; }}
.st-key-nav_{k} button[kind="primary"], .st-key-nav_{k} button[data-testid="stBaseButton-primary"] {{
  border-color:{c}55 !important; color:{c} !important; box-shadow:0 0 16px {c}22; }}
.st-key-nav_{k} button:hover {{ border-color:{c}40 !important; }}"""
    for k, _i, _l, c in NAV
)
st.markdown(
    f"""<style>
[class*="st-key-nav_"] button, [class*="st-key-nav_"] button > div,
[class*="st-key-nav_"] button [data-testid="stMarkdownContainer"] {{
  justify-content:flex-start !important; text-align:left !important; }}
[class*="st-key-nav_"] button > div {{ width:100%; gap:12px; }}
[class*="st-key-nav_"] button p {{ font-size:14px !important; text-align:left !important; }}
[class*="st-key-nav_"] button [data-testid="stIconMaterial"] {{ opacity:.75; }}
[class*="st-key-nav_"] button[kind="primary"] [data-testid="stIconMaterial"],
[class*="st-key-nav_"] button:hover [data-testid="stIconMaterial"] {{
  opacity:1; filter:drop-shadow(0 0 6px currentColor); }}
{_nav_css}
</style>""",
    unsafe_allow_html=True,
)

# Keep widget values alive when the user switches pages (widgets not drawn on a
# page would otherwise lose their state).
for _k in ("topic_in", "tone_in", "p_li", "p_ig", "p_tw", "pause_text"):
    if _k in S:
        S[_k] = S[_k]

# ───────────────────────── session state ─────────────────────────
for _k, _v in {
    "page": "home",       # home | pipelines | history | settings
    "stage": "idle",      # idle | research | write | edit | verify | adapt | done
    "running": False,
    "pause": None,        # None | research | draft | reject | manual | max | verify
    "pause_text": "",
    "state": None,
    "mode": "auto",       # auto | review
    "platforms": ["linkedin", "instagram", "twitter"],
    "calls": 0,
    "error": None,
    "warn": None,
    "run_meta": {},
    "from_cache": False,
    "force_fresh": False,
    "run_id": None,
    "hook_req": None,
    "hook_error": None,
    "hooks_used": {},
    "p_li": True,
    "p_ig": True,
    "p_tw": True,
}.items():
    if _k not in S:
        S[_k] = _v

ORDER = [
    ("research", "🔍", "Research"),
    ("strategy", "🧭", "Strategy"),
    ("write", "✍️", "Write"),
    ("edit", "👁️", "Edit"),
    ("verify", "🛡️", "Verify"),
    ("adapt", "⚡", "Adapt"),
]
PAUSE_FOCUS = {"research": 0, "draft": 2, "editor": 3, "reject": 3, "manual": 3, "max": 3, "verify": 4}
MAX_RETRIES = 3
SPIN = {
    "research": "Researcher agent is working…",
    "strategy": "Strategist is checking what worked before…",
    "write": "Writer agent is drafting…",
    "edit": "Editor agent is reviewing…",
    "verify": "Fact-checker is verifying…",
    "adapt": "Adapting for each platform…",
}
LABELS = {"linkedin": "🔵 LinkedIn", "instagram": "🔴 Instagram", "twitter": "🔷 Twitter"}
TONES = ["Professional", "Casual", "Storytelling", "Motivational"]
COST_PER_CALL = 0.00016  # rough estimate per Gemini call


def html(s: str):
    """Collapse HTML so markdown never mistakes indented lines for code blocks."""
    return "".join(line.strip() for line in s.splitlines())


def esc(x) -> str:
    return _html.escape(str(x))


CACHE_FIELDS = (
    "research_notes", "draft", "retry_count", "fact_check_passed",
    "fact_check_notes", "platform_outputs", "slop", "engagement",
)


def save_history(s):
    """Save the finished run to SQLite. A DB problem must never lose the result."""
    try:
        m = S.run_meta
        S.run_id = history_db.save_run(
            m.get("topic", ""), m.get("tone", ""), m.get("mode", ""),
            S.platforms, s["retry_count"], S.calls * COST_PER_CALL,
            s.get("platform_outputs") or {},
            draft=s.get("draft", ""),
            virality=(s.get("engagement") or {}).get("virality"),
        )
    except Exception:  # noqa: BLE001
        pass


def store_cache(s):
    """Cache only clean Auto-mode runs (no manual edits)."""
    m = S.run_meta
    if m.get("mode") != "auto" or m.get("manual"):
        return
    try:
        cache.put(cache.make_key(m["topic"], m["tone"]), {k: s.get(k) for k in CACHE_FIELDS})
    except Exception:  # noqa: BLE001
        pass


# ───────────────────────── callbacks ─────────────────────────
def set_page(p):
    S.page = p


def set_mode(m):
    S.mode = m


def start_run():
    topic = (S.get("topic_in") or "").strip()
    plats = [p for p, k in (("linkedin", "p_li"), ("instagram", "p_ig"), ("twitter", "p_tw")) if S.get(k)]
    if not topic:
        S.warn = "Please write your idea first."
        return
    if not plats:
        S.warn = "Select at least one platform."
        return
    tone = S.get("tone_in", "Professional")
    S.warn, S.error = None, None
    S.platforms = plats
    S.run_meta = {"topic": topic, "tone": tone, "mode": S.mode, "manual": False}
    S.state = {
        "topic": f"{topic} (Tone: {tone})",
        "research_notes": "",
        "draft": "",
        "editor_feedback": "",
        "retry_count": 0,
        "is_approved": False,
        "human_review_needed": False,
        "fact_check_passed": False,
        "fact_check_notes": "",
        "platform_outputs": {},
    }
    S.stage, S.running, S.pause, S.calls = "research", True, None, 0
    S.from_cache = False
    S.run_id, S.hook_req, S.hook_error, S.hooks_used = None, None, None, {}

    fresh, S.force_fresh = S.force_fresh, False
    if S.mode == "auto" and not fresh:
        hit = cache.get(cache.make_key(topic, tone))
        if hit:
            S.state.update(hit)
            S.stage, S.running, S.calls = "done", False, 0
            S.from_cache = True
            save_history(S.state)


def cb_regenerate():
    S.force_fresh = True
    start_run()


def cb_continue():
    s = S.state
    if S.pause == "research":
        s["research_notes"] = S.pause_text
    elif S.pause == "draft":
        s["draft"] = S.pause_text
    S.pause = None


def cb_manual():
    S.run_meta["manual"] = True
    S.pause_text = S.state["draft"]
    S.pause = "manual"


def cb_retry():
    S.pause = None
    S.stage = "write"


def cb_editor_approve():
    """Review mode: the human agrees with the Editor (optionally after tweaking the draft)."""
    s = S.state
    if S.pause_text != s["draft"]:
        S.run_meta["manual"] = True
    s["draft"] = S.pause_text
    S.pause = None  # stage is already "verify"


def cb_editor_reject():
    """Review mode: the human overrules the Editor and sends the draft back with their own feedback."""
    s = S.state
    s["draft"] = S.pause_text
    s["editor_feedback"] = (S.get("human_fb") or "").strip() or (
        "Rejected by the author: make the hook stronger and the structure clearer."
    )
    s["is_approved"] = False
    s["retry_count"] = s.get("retry_count", 0) + 1
    S["human_fb"] = ""
    if s["retry_count"] >= MAX_RETRIES:
        s["human_review_needed"] = True
        S.pause, S.pause_text, S.stage = "max", s["draft"], "edit"
    else:
        S.pause, S.stage = None, "write"


def cb_approve():
    S.run_meta["manual"] = True
    s = S.state
    s["draft"] = S.pause_text
    s["is_approved"] = True
    s["human_review_needed"] = False
    S.pause = None
    S.stage = "verify"


def cb_reset():
    S.stage, S.state, S.pause, S.running, S.error = "idle", None, None, False, None


def cb_retry_after_error():
    S.error = None
    S.running = True


def cb_clear_history():
    history_db.clear_runs()


def cb_clear_cache():
    cache.clear()


def cb_hook_req(platform):
    S.hook_req = platform


def cb_rate(run_id):
    v = S.get(f"fb_{run_id}")  # st.feedback gives 0-4, or None when cleared
    history_db.set_rating(run_id, None if v is None else int(v) + 1)


# ───────────────────────── pipeline ─────────────────────────
def open_pause(kind, text=""):
    S.pause = kind
    S.pause_text = text


def run_stage():
    s, stg = S.state, S.stage
    review = S.mode == "review"

    if stg == "research":
        s.update(researcher_node(s))
        S.calls += 1
        S.stage = "strategy"
        if review:
            open_pause("research", str(s["research_notes"]))

    elif stg == "strategy":
        res = strategist_node(s)  # sleeps until enough rated posts exist
        s["strategy"] = res["strategy"]
        if "research_notes" in res:
            s["research_notes"] = res["research_notes"]
        if res["strategy"]["called"]:
            S.calls += 1
        S.stage = "write"

    elif stg == "write":
        s.update(writer_node(s))
        S.calls += 1
        S.stage = "edit"
        if review:
            open_pause("draft", s["draft"])

    elif stg == "edit":
        s.update(editor_node(s))
        S.calls += 1
        if s["is_approved"]:
            S.stage = "verify"
            if review:  # the human gets the final say on the Editor's verdict
                open_pause("editor", s["draft"])
        elif s["human_review_needed"]:
            open_pause("max", s["draft"])
        else:
            S.pause = "reject"  # always shown, even in auto mode

    elif stg == "verify":
        s.update(fact_checker_node(s))
        S.calls += 1
        S.stage = "adapt"
        if review:
            S.pause = "verify"

    elif stg == "adapt":
        s.update(platform_adapter_node(s))
        S.calls += 3
        s.update(slop_node(s))  # rule-based, free
        try:
            s.update(engagement_node(s))
            S.calls += 1
        except Exception:  # noqa: BLE001 — the score is a bonus, never block the posts
            s["engagement"] = None
        S.stage = "done"
        S.running = False
        save_history(s)
        store_cache(s)


def focus_index():
    if S.stage == "done":
        return len(ORDER)
    if S.pause:
        return PAUSE_FOCUS[S.pause]
    if S.stage == "idle":
        return -1
    return [o[0] for o in ORDER].index(S.stage)


def agent_status(i, f):
    """(color, text, bg, opacity) for agent i given focus index f."""
    s = S.state or {}
    is_strategy = ORDER[i][0] == "strategy"
    if i < f:
        info = s.get("strategy")
        if is_strategy and info:
            if info.get("rules"):
                return GREEN, f"{len(info['rules'])} rules applied", "#0C0E1A", 1
            msg = f"Learning {info['rated']}/{info['needed']}" if not info["active"] else "No pattern yet"
            return "#6A6A98", msg, "#0C0E1A", 1
        return GREEN, "Done ✓", "#0C0E1A", 1
    if i > f:
        if is_strategy and S.stage == "idle":
            stt = strategist_status()
            return "#6A6A98", ("Ready" if stt["active"] else f"Learning {stt['rated']}/{stt['needed']}"), "#0C0E1A", 0.45
        return "#2A2550", "Waiting", "#0C0E1A", 0.4
    if S.error:
        return PINK, "Failed", "#130818", 1
    if S.pause == "reject":
        return PURPLE, f"Rejected {s.get('retry_count', 0)}/3", "#130818", 1
    if S.pause in ("manual", "max"):
        return PURPLE, "Your edit", "#130818", 1
    if S.pause:
        return CYAN, "Your review", "#0A1420", 1
    if ORDER[i][0] == "edit":
        return PURPLE, f"Attempt {s.get('retry_count', 0) + 1}/3", "#130818", 1
    return PURPLE, "Running…", "#130818", 1


def cards_html():
    f = focus_index()
    cards = []
    for i, (_, icon, name) in enumerate(ORDER):
        col, txt, bg, op = agent_status(i, f)
        glow = f"box-shadow:0 0 14px {col}30;" if i == f else ""
        cards.append(
            f"""<div style="background:{bg};border:1.5px solid {col};border-radius:14px;
            padding:12px 4px;text-align:center;opacity:{op};{glow}">
            <div style="font-size:22px;">{icon}</div>
            <div style="font-size:13px;color:{col};font-weight:600;margin-top:4px;">{name}</div>
            <div style="font-size:10px;color:{col};opacity:.75;margin-top:2px;">{txt}</div></div>"""
        )
    return html(
        f'<div style="display:grid;grid-template-columns:repeat({len(ORDER)},1fr);gap:8px;margin:6px 0 10px;">'
        + "".join(cards)
        + "</div>"
    )


def normalize_tag(tag) -> str:
    """'AI Agents' -> '#AIAgents', 'langgraph' -> '#langgraph', '#Python' -> '#Python'."""
    words = [w for w in re.split(r"[\s_\-]+", str(tag).strip().lstrip("#")) if w]
    if len(words) > 1:
        words = [w[:1].upper() + w[1:] for w in words]
    clean = re.sub(r"\W", "", "".join(words))
    return "#" + clean if clean else ""


def compose_post(out: dict) -> str:
    """One platform's output as a single copy-ready text (post + hashtags)."""
    tweets = out.get("tweets") or []
    text = "\n\n".join(tweets) if tweets else out.get("content", "")
    if not text:
        return ""
    tags = [normalize_tag(t) for t in (out.get("hashtags") or [])]
    missing = [t for t in dict.fromkeys(tags) if t and t not in text]
    return text + ("\n\n" + " ".join(missing) if missing else "")


def render_outputs(outs, platforms, hook_button=False):
    """Tabs with one copy-ready block per platform (post + hashtags together)."""
    st.caption("Click the copy icon at the top-right of the box to copy the post and its hashtags together.")
    tabs = st.tabs([LABELS[p] for p in platforms])
    for tab, p in zip(tabs, platforms):
        with tab:
            text = compose_post(outs.get(p) or {})
            if not text:
                st.caption("No output for this platform.")
                continue
            try:
                st.code(text, language=None, wrap_lines=True)
            except TypeError:
                st.code(text, language=None)
            if hook_button:
                st.button(
                    "↺ New hook", key=f"hook_{p}", on_click=cb_hook_req, args=(p,),
                    help="Rewrites only the opening line. The rest of the post stays exactly as it is.",
                )


# ───────────────────────── side panels ─────────────────────────
def render_stats(ph):
    runs, cost, posts = history_db.today_stats()
    ph.markdown(
        html(
            f"""
        <div style="background:#0C0E1A;border:1px solid #1A1A2A;border-radius:12px;padding:12px 14px;margin-top:18px;">
          <div style="font-size:10px;color:#4A4A78;text-transform:uppercase;letter-spacing:.6px;margin-bottom:10px;">Today</div>
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="font-size:12px;color:#6A6A98;">Runs</span><span style="font-size:12px;color:#E0E8FF;font-weight:600;">{runs}</span></div>
          <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
            <span style="font-size:12px;color:#6A6A98;">Cost</span><span style="font-size:12px;color:{GREEN};font-weight:600;">${cost:.4f}</span></div>
          <div style="display:flex;justify-content:space-between;">
            <span style="font-size:12px;color:#6A6A98;">Posts</span><span style="font-size:12px;color:#E0E8FF;font-weight:600;">{posts}</span></div>
        </div>"""
        ),
        unsafe_allow_html=True,
    )


def render_right(ph):
    f = focus_index()
    done_n = max(0, min(f, len(ORDER)))
    s = S.state or {}
    info = s.get("strategy") or {}
    strat_note = (
        f"{len(info['rules'])} style rules applied" if info.get("rules")
        else f"Learning {info.get('rated', 0)}/{info.get('needed', 10)} rated posts" if info
        else "Done"
    )
    notes = {
        0: "Key points found",
        1: strat_note,
        2: "Draft created",
        3: f"Approved · {s.get('retry_count', 0)} {'retry' if s.get('retry_count', 0) == 1 else 'retries'}",
        4: "Claims passed" if s.get("fact_check_passed") else "Claims flagged",
        5: "Posts ready",
    }
    tl = []
    for i, (_, _, name) in enumerate(ORDER):
        col, txt, _, op = agent_status(i, f)
        sub = notes[i] if i < f else (txt if i == f else "Queued")
        mark = "✓" if i < f else ("●" if i == f else "○")
        tl.append(
            f"""<div style="display:flex;gap:9px;align-items:flex-start;opacity:{op};margin-bottom:10px;">
            <div style="width:20px;height:20px;border-radius:50%;border:1px solid {col};background:{col}18;
            display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:10px;color:{col};">{mark}</div>
            <div><div style="font-size:13px;color:{col if i == f else '#C4D4FF'};font-weight:500;">{name}</div>
            <div style="font-size:11px;color:#4A4A78;">{sub}</div></div></div>"""
        )

    def tile(val, label, color="#E0E8FF"):
        return (
            f'<div style="background:#0C0E1A;border:1px solid #1A1A2A;border-radius:10px;padding:10px 6px;text-align:center;">'
            f'<div style="font-size:18px;color:{color};font-weight:600;">{val}</div>'
            f'<div style="font-size:10px;color:#4A4A78;margin-top:2px;">{label}</div></div>'
        )

    def soon(title, color):
        return (
            f'<div style="background:#0C0E1A;border:1px solid {color}20;border-radius:12px;padding:12px;margin-bottom:10px;">'
            f'<div style="font-size:10px;color:{color}90;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">{title}</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<span style="font-size:12px;color:#6A6A98;">Score</span><span style="font-size:15px;color:#3A3A60;font-weight:600;">—</span></div>'
            f'<div style="background:#0A0C16;border-radius:20px;height:5px;margin:7px 0 5px;"></div>'
            f'<div style="font-size:10px;color:#3A3A60;">Appears after a run</div></div>'
        )

    def level(v):
        return GREEN if v >= 70 else GOLD if v >= 45 else PINK

    def score_card(title, color, big_label, value, grad, rows_html, footer):
        return (
            f'<div style="background:#0C0E1A;border:1px solid {color}30;border-radius:12px;padding:12px;margin-bottom:10px;">'
            f'<div style="font-size:10px;color:{color};text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">{title}</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline;">'
            f'<span style="font-size:12px;color:#8A9AC0;">{big_label}</span>'
            f'<span style="font-size:18px;color:{level(value)};font-weight:600;">{value}<span style="font-size:11px;color:#4A4A78;">/100</span></span></div>'
            f'<div style="background:#0A0C16;border-radius:20px;height:5px;margin:8px 0;">'
            f'<div style="width:{value}%;height:5px;border-radius:20px;background:{grad};"></div></div>'
            f'{rows_html}'
            f'<div style="font-size:11px;color:#6A6A98;margin-top:6px;line-height:1.5;">{footer}</div></div>'
        )

    slop, eng = s.get("slop"), s.get("engagement")

    if slop:
        fl = slop["flagged"]
        foot = (
            f'{len(fl)} flagged: ' + ", ".join(f"“{esc(x)}”" for x in fl[:2]) + (" …" if len(fl) > 2 else "")
            if fl else "No clichés found"
        )
        slop_html = score_card("🧹 AI-Slop score", PINK, "Human feel", slop["human_score"],
                               f"linear-gradient(90deg,{PURPLE},{GREEN})", "", foot)
    else:
        slop_html = soon("🧹 AI-Slop score", PINK)

    if eng:
        def row(name, d):
            return (
                f'<div style="display:flex;justify-content:space-between;margin-top:3px;">'
                f'<span style="font-size:11px;color:#6A6A98;">{name}</span>'
                f'<span style="font-size:11px;color:{level(d["score"])};">{d["label"]}</span></div>'
            )
        rows = row("Hook", eng["hook"]) + row("CTA", eng["cta"]) + row("Emotion", eng["emotion"])
        eng_html = score_card("⚡ Engagement score", GOLD, "Virality", eng["virality"],
                              "linear-gradient(90deg,#FF5F3A,#FFD23F)", rows,
                              f"💡 {esc(eng['tip'])}" if eng.get("tip") else "")
    elif S.stage == "done":
        eng_html = (
            '<div style="background:#0C0E1A;border:1px solid #1A1A2A;border-radius:12px;padding:12px;margin-bottom:10px;'
            'font-size:11px;color:#4A4A78;">⚡ Engagement score unavailable for this run.</div>'
        )
    else:
        eng_html = soon("⚡ Engagement score", GOLD)

    ph.markdown(
        html(
            f"""
        <div style="font-size:10px;color:#4A4A78;text-transform:uppercase;letter-spacing:.6px;margin-bottom:8px;">Pipeline insights</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:6px;">
          {tile(f"{done_n}/{len(ORDER)}", "Stages")}{tile(len(S.platforms), "Platforms")}
        </div>
        <div style="margin-bottom:14px;">{tile(f"${S.calls * COST_PER_CALL:.4f}", "Estimated run", GREEN)}</div>
        {slop_html}
        {eng_html}
        <div style="font-size:10px;color:#4A4A78;text-transform:uppercase;letter-spacing:.6px;margin:16px 0 10px;">Activity</div>
        {"".join(tl)}
        """
        ),
        unsafe_allow_html=True,
    )


def render_chip(ph):
    label, color = (
        ("Pipeline running", CYAN) if S.running and not S.pause
        else ("Waiting for you", GOLD) if S.pause
        else ("Done", GREEN) if S.stage == "done"
        else ("Pipeline ready", GREEN)
    )
    ph.markdown(
        html(
            f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <span style="font-size:12px;color:#4A4A78;">✦ New pipeline run</span>
          <div style="display:flex;align-items:center;gap:6px;background:#0C0E1A;border:1px solid #1A1A2A;border-radius:20px;padding:5px 13px;">
            <div style="width:7px;height:7px;border-radius:50%;background:{color};"></div>
            <span style="font-size:11px;color:{color};font-weight:500;">{label}</span>
          </div>
        </div>"""
        ),
        unsafe_allow_html=True,
    )


def page_title(title, sub):
    st.markdown(
        html(
            f"""<div style="margin-bottom:16px;">
            <div style="font-size:20px;color:#F0F4FF;font-weight:600;">{title}</div>
            <div style="font-size:12px;color:#4A4A78;margin-top:2px;">{sub}</div></div>"""
        ),
        unsafe_allow_html=True,
    )


# ───────────────────────── pages ─────────────────────────
def page_home():
    chip_ph = st.empty()
    render_chip(chip_ph)

    st.text_area(
        "Your idea",
        key="topic_in",
        placeholder="e.g. My DRDO internship where I built a computer vision system",
        max_chars=200,
        height=90,
        label_visibility="collapsed",
        disabled=S.running,
    )

    m1, m2 = st.columns(2)
    with m1:
        st.button("⚡ Auto mode", key="m_auto", use_container_width=True,
                  type="primary" if S.mode == "auto" else "secondary",
                  on_click=set_mode, args=("auto",), disabled=S.running)
    with m2:
        st.button("👁 Review each step", key="m_rev", use_container_width=True,
                  type="primary" if S.mode == "review" else "secondary",
                  on_click=set_mode, args=("review",), disabled=S.running)
    st.markdown(
        f'<div style="font-size:11px;color:#4A4A78;text-align:center;margin:4px 0 10px;">'
        f'{"Pipeline runs automatically, end to end" if S.mode == "auto" else "Pipeline pauses after each agent so you can review and edit"}</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns([1.6, 1, 1, 1])
    with c1:
        st.selectbox("Tone", TONES, key="tone_in", label_visibility="collapsed", disabled=S.running)
    with c2:
        st.checkbox("LinkedIn", key="p_li", disabled=S.running)
    with c3:
        st.checkbox("Instagram", key="p_ig", disabled=S.running)
    with c4:
        st.checkbox("Twitter", key="p_tw", disabled=S.running)

    st.button("Run pipeline ▶", key="run_btn", type="primary", use_container_width=True,
              on_click=start_run, disabled=S.running)

    if S.warn:
        st.warning(S.warn)

    cards_ph = st.empty()

    def draw_cards():
        cards_ph.markdown(cards_html(), unsafe_allow_html=True)

    # ── drive the pipeline until it pauses, finishes, or fails ──
    was_running = S.running
    try:
        while S.running and not S.pause and S.stage not in ("idle", "done"):
            draw_cards()
            with st.spinner(SPIN[S.stage]):
                run_stage()
    except Exception as e:  # noqa: BLE001
        S.error = f"{type(e).__name__}: {e}"
        S.running = False
    if was_running and not S.running:
        st.rerun()  # inputs above were drawn disabled; redraw them now the run is over
    draw_cards()
    render_chip(chip_ph)

    if S.error:
        st.error(f"Pipeline failed — {S.error}")
        st.button("↺ Retry this step", key="err_retry", type="primary", on_click=cb_retry_after_error)

    def pause_card(color, title, sub=""):
        st.markdown(
            html(
                f"""<div style="background:#0C0E1A;border:1px solid {color}40;border-radius:12px;padding:11px 14px;margin:4px 0 8px;">
                <div style="font-size:13px;color:{color};font-weight:600;">{title}</div>
                <div style="font-size:12px;color:#6A6A98;margin-top:2px;">{sub}</div></div>"""
            ),
            unsafe_allow_html=True,
        )

    # one pause UI at a time → widget keys never collide
    if S.pause in ("research", "draft"):
        if S.pause == "research":
            pause_card(CYAN, "⏸ Researcher finished — review the notes",
                       "Edit anything you like. The Writer will use exactly what is below.")
        else:
            pause_card(CYAN, "⏸ Writer finished — read the draft",
                       "Tweak it if you want. Next the AI Editor reviews it, and then you get the final say.")
        st.text_area("Edit", key="pause_text", height=200, label_visibility="collapsed")
        st.button("Continue pipeline ▶", key="cont_btn", type="primary", on_click=cb_continue)

    elif S.pause == "editor":
        fb = (S.state.get("editor_feedback") or "").strip()
        pause_card(
            GREEN, "⏸ Editor approved this draft — your decision",
            f"Editor's note: “{esc(fb)}”" if fb else "The Editor had no notes. Read the draft, then approve or reject it.",
        )
        st.text_area("Draft", key="pause_text", height=220, label_visibility="collapsed")
        st.text_input(
            "Your feedback if you reject", key="human_fb",
            placeholder="If you reject, tell the Writer what to fix, e.g. “Hook is generic — open with a number”",
        )
        e1, e2 = st.columns([2, 1.3])
        with e1:
            st.button("✓ Approve & continue ▶", key="ed_approve", type="primary",
                      use_container_width=True, on_click=cb_editor_approve)
        with e2:
            st.button("✕ Reject — send back to Writer", key="ed_reject",
                      use_container_width=True, on_click=cb_editor_reject)

    elif S.pause == "verify":
        ok = S.state.get("fact_check_passed")
        pause_card(CYAN, "⏸ Paused — fact-check result", "Passed ✓" if ok else "Some claims were flagged")
        if S.state.get("fact_check_notes"):
            st.write(S.state["fact_check_notes"])
        st.button("Continue pipeline ▶", key="cont_btn", type="primary", on_click=cb_continue)

    elif S.pause == "reject":
        n = S.state.get("retry_count", 0)
        pause_card(PURPLE, f"⚠ Draft rejected — attempt {n} of 3", f"“{esc(S.state.get('editor_feedback', ''))}”")
        b1, b2 = st.columns([1, 2])
        with b1:
            st.button("✎ Edit myself", key="rej_edit", use_container_width=True, on_click=cb_manual)
        with b2:
            st.button("↺ Retry with AI", key="rej_retry", type="primary", use_container_width=True, on_click=cb_retry)

    elif S.pause in ("manual", "max"):
        if S.pause == "max":
            pause_card(PINK, "⚠ Max retries reached — your turn", "Edit the draft, then approve to continue.")
        else:
            pause_card(PURPLE, "✎ Edit the draft", "Approve when you are happy with it.")
        st.text_area("Draft", key="pause_text", height=220, label_visibility="collapsed")
        st.button("Approve & Continue ▶", key="appr_btn", type="primary", on_click=cb_approve)

    if S.stage == "done" and S.state:
        s = S.state
        st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

        # "New hook" was clicked: rewrite only that platform's opening line, then show the result
        if S.hook_req:
            p, S.hook_req = S.hook_req, None
            outs = s.get("platform_outputs") or {}
            used = S.hooks_used.setdefault(p, [])
            try:
                with st.spinner("Writing a new hook…"):
                    new_out, hook, old = regenerate_hook(p, outs.get(p) or {}, S.run_meta.get("tone", "Professional"), used)
                if old not in used:
                    used.append(old)
                used.append(hook)
                outs[p] = new_out
                S.calls += 1
                if S.run_id:
                    try:
                        history_db.update_outputs(S.run_id, outs)
                    except Exception:  # noqa: BLE001
                        pass
            except Exception as e:  # noqa: BLE001
                S.hook_error = f"Couldn't write a new hook: {e}"
        if S.hook_error:
            st.warning(S.hook_error)
            S.hook_error = None

        render_outputs(s.get("platform_outputs") or {}, S.platforms, hook_button=True)

        if s.get("fact_check_notes"):
            with st.expander("Fact-check notes"):
                st.write(s["fact_check_notes"])

        strat = s.get("strategy") or {}
        if strat.get("rules"):
            with st.expander("🧭 Strategy applied — learned from your rated posts"):
                for rule in strat["rules"]:
                    st.markdown(f"- {rule}")

        rc = s.get("retry_count", 0)
        cost_note = "⚡ served from cache · $0.0000" if S.from_cache else f"~${S.calls * COST_PER_CALL:.4f} this run"
        st.markdown(
            html(
                f"""<div style="display:flex;justify-content:space-between;padding:6px 2px;">
                <span style="font-size:11px;color:#3A3A60;">{rc} {'retry' if rc == 1 else 'retries'} · fact-check {'passed' if s.get('fact_check_passed') else 'flagged'}</span>
                <span style="font-size:11px;color:{GREEN};font-weight:500;">{cost_note}</span></div>"""
            ),
            unsafe_allow_html=True,
        )
        if any(S.hooks_used.values()):
            st.caption("The scores on the right were calculated for the original draft, before the new hook.")

        b1, b2, _ = st.columns([1.2, 1.9, 4])
        with b1:
            st.button("＋ New run", key="reset_btn", on_click=cb_reset)
        if S.from_cache:
            with b2:
                st.button("↻ Regenerate fresh", key="regen_btn", on_click=cb_regenerate)


def page_history():
    page_title("History", "Every pipeline run, saved locally in data/performance.db")
    runs = history_db.list_runs()
    if not runs:
        st.markdown(
            '<div style="background:#0C0E1A;border:1px solid #1A1A2A;border-radius:12px;padding:22px;'
            'text-align:center;font-size:13px;color:#4A4A78;">No runs yet. Run your first pipeline from Home.</div>',
            unsafe_allow_html=True,
        )
        return
    stt = strategist_status()
    if stt["active"]:
        st.success(f"🧭 Strategist is active — learning from your {stt['rated']} rated posts.")
    else:
        st.progress(
            min(stt["rated"] / stt["needed"], 1.0),
            text=f"🧭 Strategist is learning — {stt['rated']}/{stt['needed']} rated posts needed to activate",
        )

    for r in runs:
        stars = f"{'★' * r['rating']}  " if r.get("rating") else ""
        title = f"{stars}{r['ts'].replace('T', ' ')}  ·  {r['topic'][:70]}"
        with st.expander(title):
            st.caption(
                f"Tone: {r['tone']} · Mode: {r['mode']} · Retries: {r['retries']} · "
                f"Cost: ~${(r['cost'] or 0):.4f} · Platforms: {', '.join(r['platforms'])}"
            )
            if hasattr(st, "feedback"):
                key = f"fb_{r['id']}"
                if key not in S and r.get("rating"):
                    S[key] = r["rating"] - 1
                st.caption("How did this post perform? Rate it after you've posted it — the Strategist learns from this.")
                st.feedback("stars", key=key, on_change=cb_rate, args=(r["id"],))
            else:
                st.caption("Update Streamlit (pip install -U streamlit) to rate posts.")
            render_outputs(r["outputs"], r["platforms"])


def page_pipelines():
    page_title("Pipelines", "How Horizon AI turns one idea into three platform-ready posts")
    info = [
        ("🔍", "Researcher", "Finds key points, an angle and a hook idea from your topic.", CYAN),
        ("🧭", "Strategist", "Learns from the posts you rated highly and gives the Writer 3 style rules. Wakes up after 10 rated posts.", GOLD),
        ("✍️", "Writer", "Writes the first draft — or rewrites it using the editor's feedback.", PURPLE),
        ("👁️", "Editor", "Approves or rejects with specific feedback. Max 3 retries, then you take over. In Review mode you get the final say on its verdict.", PINK),
        ("🛡️", "Fact-Checker", "Flags unverifiable or exaggerated claims before anything is published.", GREEN),
        ("⚡", "Platform Adapter", "Reshapes the approved draft for LinkedIn, Instagram and Twitter.", GOLD),
    ]
    for i, (icon, name, desc, col) in enumerate(info, 1):
        st.markdown(
            html(
                f"""<div style="display:flex;gap:14px;align-items:center;background:#0C0E1A;border:1px solid {col}30;
                border-radius:12px;padding:12px 16px;margin-bottom:8px;">
                <div style="font-size:22px;">{icon}</div>
                <div><div style="font-size:14px;color:{col};font-weight:600;">{i}. {name}</div>
                <div style="font-size:12px;color:#8A9AC0;margin-top:2px;">{desc}</div></div></div>"""
            ),
            unsafe_allow_html=True,
        )
    st.caption("Editor → Writer is a feedback loop: a rejected draft goes back to the Writer with the Editor's notes.")


def page_settings():
    page_title("Settings", "Defaults for new runs")
    mode_label = st.radio(
        "Default mode", ["⚡ Auto mode", "👁 Review each step"],
        index=0 if S.mode == "auto" else 1, horizontal=True, key="set_mode",
    )
    S.mode = "auto" if mode_label.startswith("⚡") else "review"

    cur = S.get("tone_in", "Professional")
    S.tone_in = st.selectbox("Default tone", TONES, index=TONES.index(cur) if cur in TONES else 0, key="set_tone")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    try:
        from config.settings import FLASH, FLASH_LITE
        st.caption(f"Models — fast: {FLASH_LITE} · quality: {FLASH}")
    except Exception:  # noqa: BLE001
        pass

    st.divider()
    st.button("🗑 Clear run history", key="clear_hist", on_click=cb_clear_history)
    st.caption("Deletes every saved run from data/performance.db.")
    st.button("🗑 Clear cache", key="clear_cache", on_click=cb_clear_cache)
    st.caption(
        f"{cache.count()} cached result(s). The same idea + tone in Auto mode reuses a saved result "
        f"and skips every API call (expires after {cache.TTL_DAYS} days)."
    )


def render_pdf(ph):
    """Export button lives in the left panel and only appears once a run has finished."""
    if S.page != "home" or S.stage != "done" or not S.state:
        return
    s, m = S.state, S.run_meta
    outs = s.get("platform_outputs") or {}
    strat = s.get("strategy") or {}
    with ph.container():
        st.markdown(
            '<div style="margin-top:20px;font-size:10px;color:#4A4A78;text-transform:uppercase;'
            'letter-spacing:.6px;">This run</div>',
            unsafe_allow_html=True,
        )
        try:
            pdf = build_pdf(
                {
                    "topic": m.get("topic", ""), "tone": m.get("tone", ""), "mode": m.get("mode", ""),
                    "date": date.today().isoformat(), "retries": s.get("retry_count", 0),
                    "fact_check_passed": s.get("fact_check_passed"),
                    "cost": 0.0 if S.from_cache else S.calls * COST_PER_CALL,
                },
                {p: compose_post(outs.get(p) or {}) for p in S.platforms},
                slop=s.get("slop"), engagement=s.get("engagement"), rules=strat.get("rules"),
            )
            slug = re.sub(r"[^a-z0-9]+", "-", m.get("topic", "post").lower()).strip("-")[:40] or "post"
            st.download_button(
                "⬇ Export PDF", pdf, file_name=f"horizon-ai-{slug}.pdf",
                mime="application/pdf", key="pdf_btn", use_container_width=True,
            )
        except Exception:  # noqa: BLE001
            st.caption("PDF export needs reportlab: pip install reportlab")


# ───────────────────────── layout ─────────────────────────
left, main, right = st.columns([1.15, 4, 1.5], gap="medium")

with left:
    st.markdown(
        html(
            f"""
        <div style="display:flex;align-items:center;gap:9px;margin-bottom:20px;">
          <div style="width:34px;height:34px;border-radius:10px;flex-shrink:0;background:{GRAD};
          display:flex;align-items:center;justify-content:center;font-size:16px;color:#fff;">✦</div>
          <div>
            <div style="font-size:15px;font-weight:600;color:#F0F4FF;line-height:1.2;">Horizon AI</div>
            <div style="font-size:9px;color:#4A4A78;line-height:1.3;">Every idea deserves<br>a bigger horizon</div>
          </div>
        </div>"""
        ),
        unsafe_allow_html=True,
    )
    for _key, _icon, _label, _ in NAV:
        st.button(
            _label, key=f"nav_{_key}", icon=_icon, use_container_width=True,
            type="primary" if S.page == _key else "secondary",
            on_click=set_page, args=(_key,),
        )
    stats_ph = st.empty()
    st.markdown(
        '<div style="padding:18px 4px 0;font-size:12px;color:#2A2A50;font-style:italic;line-height:2;">'
        "Explore<br>Create<br>Elevate</div>",
        unsafe_allow_html=True,
    )
    pdf_ph = st.empty()

right_ph = right.empty()

# first paint (so panels show while the pipeline is running)
render_stats(stats_ph)
render_right(right_ph)

with main:
    {"home": page_home, "pipelines": page_pipelines, "history": page_history, "settings": page_settings}[S.page]()

# repaint with the final state of this run
render_stats(stats_ph)
render_right(right_ph)
render_pdf(pdf_ph)