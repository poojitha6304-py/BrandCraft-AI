"""
agents.py - small multi-agent toolkit shared by this project.
Every agent is a Python function with a name and a role. The Pipeline runs them in order,
shows live progress in Streamlit and records a trace. An optional LLM (Google Gemini or
OpenAI) can be switched on from the sidebar; if it is off or fails, the offline logic runs.
"""
import json
import os
import time
import urllib.request

import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)


# ----------------------------------------------------------------------------- storage
def load_json(name, default):
    try:
        with open(os.path.join(DATA, name), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(name, obj):
    try:
        path = os.path.join(DATA, name)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(path + ".tmp", path)
    except Exception:
        pass


# ----------------------------------------------------------------------------- optional LLM
def llm_settings():
    return load_json("settings.json", {"provider": "offline", "key": "", "model": ""})


def llm(prompt, system="You are a helpful assistant.", max_words=180):
    """Return LLM text, or None when the LLM is off or unavailable (callers then use offline logic)."""
    s = llm_settings()
    key, provider = s.get("key", "").strip(), s.get("provider", "offline")
    if not key or provider == "offline":
        return None
    system = system + " Keep the answer under %d words. Use simple markdown." % max_words
    try:
        if provider == "openai":
            body = {"model": s.get("model") or "gpt-4o-mini",
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
            req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"].strip()
        model = s.get("model") or "gemini-2.5-flash"
        body = {"system_instruction": {"parts": [{"text": system}]}, "contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent?key=%s" % (model, key),
                                     data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=40) as r:
            res = json.loads(r.read())
        return "".join(p.get("text", "") for p in res["candidates"][0]["content"]["parts"]).strip() or None
    except Exception:
        return None


# ----------------------------------------------------------------------------- agents
class Agent:
    def __init__(self, name, role, fn, icon="*"):
        self.name, self.role, self.fn, self.icon = name, role, fn, icon


class Pipeline:
    """Runs agents in order. Each agent receives the shared context dict and returns a short summary string."""

    def __init__(self, agents):
        self.agents = agents

    def run(self, ctx, show=True, label="Agents at work"):
        trace = []
        box = st.status(label, expanded=False) if show else None
        for a in self.agents:
            t0 = time.time()
            try:
                summary = a.fn(ctx)
            except Exception as ex:  # an agent must never crash the app
                summary = "Skipped (%s)" % type(ex).__name__
            ms = int((time.time() - t0) * 1000) + 1
            trace.append({"agent": a.name, "role": a.role, "icon": a.icon, "summary": str(summary), "ms": ms})
            if box is not None:
                box.write("**%s %s** - %s" % (a.icon, a.name, summary))
        if box is not None:
            box.update(label="%d agents finished" % len(self.agents), state="complete")
        ctx["trace"] = trace
        return ctx


def show_trace(trace, title="How the agents worked"):
    if not trace:
        return
    with st.expander(title, expanded=False):
        for i, t in enumerate(trace, 1):
            st.markdown("**%d. %s %s** &nbsp; `%d ms`  \n<span style='opacity:.75'>%s</span>  \n%s" %
                        (i, t["icon"], t["agent"], t["ms"], t["role"], t["summary"]), unsafe_allow_html=True)


# ----------------------------------------------------------------------------- UI helpers
def css(text):
    st.markdown("<style>" + text + "</style>", unsafe_allow_html=True)


def settings_sidebar(extra_note=""):
    with st.sidebar.expander("AI settings (optional)", expanded=False):
        s = llm_settings()
        options = ["offline", "gemini", "openai"]
        prov = st.selectbox("Engine", options, index=options.index(s.get("provider", "offline")) if s.get("provider") in options else 0,
                            format_func=lambda x: {"offline": "Built-in offline agents", "gemini": "Google Gemini", "openai": "OpenAI"}[x])
        key = st.text_input("API key", value=s.get("key", ""), type="password", help="Free Gemini key: aistudio.google.com")
        model = st.text_input("Model (optional)", value=s.get("model", ""))
        if st.button("Save settings"):
            save_json("settings.json", {"provider": prov, "key": key, "model": model})
            st.success("Saved")
        st.caption("Works fully offline. With a key, some agents write richer answers. " + extra_note)


# ----------------------------------------------------------------------------- version-safe widgets
def chart(c):
    """Full-width Altair chart on both old and new Streamlit versions."""
    try:
        st.altair_chart(c, width="stretch")
    except TypeError:
        st.altair_chart(c, use_container_width=True)


def table(df, height=None):
    kw = {"hide_index": True}
    if height:
        kw["height"] = height
    try:
        st.dataframe(df, width="stretch", **kw)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kw)
