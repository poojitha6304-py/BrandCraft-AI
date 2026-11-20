"""BrandCraft AI - Automated Brand Identity Generation System for Startups and Small Businesses"""
import colorsys
import hashlib
import html

import streamlit as st

from agents import Agent, Pipeline, css, llm, settings_sidebar, show_trace

st.set_page_config(page_title="BrandCraft AI", page_icon="✳️", layout="wide")
css("""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Playfair+Display:wght@700&family=Poppins:wght@600;800&family=Merriweather:wght@700&family=Montserrat:wght@700;800&family=Lora:wght@500&display=swap');
html, body, [class*="css"] { font-family:'Inter',sans-serif }
.board { display:grid; grid-template-columns:1.2fr 1fr 1fr; gap:12px }
.tile { border-radius:14px; padding:16px; border:1px solid #e5e7eb; background:#fff; min-height:150px }
.sw { display:flex; height:120px; border-radius:12px; overflow:hidden } .sw div { flex:1; display:flex; align-items:flex-end; padding:6px; font-size:.7rem; font-family:monospace }
.nm { border:1px solid #e5e7eb; border-radius:10px; padding:8px 12px; margin-bottom:6px; background:#fff } .nm b { font-size:1.1rem }
.mock { border-radius:14px; padding:18px; color:#fff; min-height:150px }
""")

IND = {"Café / food": ("warm", ["Brew", "Bite", "Chai", "Nest", "Spoon"], "Playfair Display", "Lora"), "Tech startup": ("cool", ["Byte", "Nova", "Logic", "Pulse", "Stack"], "Montserrat", "Inter"),
       "Boutique / fashion": ("elegant", ["Silk", "Loom", "Muse", "Aura", "Thread"], "Playfair Display", "Inter"), "Education / coaching": ("trust", ["Mind", "Path", "Learn", "Spark", "Guru"], "Poppins", "Inter"),
       "Organic / agri": ("earthy", ["Leaf", "Soil", "Root", "Harvest", "Green"], "Merriweather", "Lora")}
HUES = {"warm": 25, "cool": 220, "elegant": 330, "trust": 205, "earthy": 105}
PERS = ["Friendly", "Premium", "Bold", "Calm", "Playful"]

st.sidebar.markdown("## ✳️ BrandCraft")
biz = st.sidebar.text_input("Business description", "A cosy café near the college serving filter coffee and millet snacks")
ind = st.sidebar.selectbox("Industry", list(IND))
pers = st.sidebar.multiselect("Brand personality", PERS, ["Friendly", "Calm"])
city = st.sidebar.text_input("City", "Hyderabad")
settings_sidebar()
st.markdown("<h1 style='font-weight:800;letter-spacing:-1px;margin-bottom:0'>BrandCraft<span style='color:#f97316'>.</span>AI</h1>Name · colours · logo · type · voice - a complete brand board", unsafe_allow_html=True)
seed_word = st.text_input("Seed word / founder name (optional)", "Ammi")
go = st.button("Generate brand", type="primary")


def hexc(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l, s)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def strategist(ctx):
    mood, words, hf, bf = IND[ind]
    ctx.update(mood=mood, words=words, hf=hf, bf=bf)
    ctx["voice"] = {"Friendly": "warm, simple, uses 'you' and 'we'", "Premium": "refined, minimal, confident", "Bold": "short, punchy, energetic", "Calm": "gentle, reassuring, slow-paced",
                    "Playful": "witty, emoji-friendly, light"}
    return "Positioning: %s %s brand in %s." % ("/".join(pers).lower() or "balanced", ind.lower(), city)


def namer(ctx):
    s = ctx["seed"].strip().title()
    w = ctx["words"]
    cands = [s + w[0], w[1] + "ly", s + "'s " + w[2], w[3] + "ora", "The " + w[4] + " Co.", w[0] + w[3]]
    if not s:
        cands = cands[1:]
    out = []
    for c in cands:
        sc = 60 + (15 if len(c) <= 9 else 0) + (10 if c[0] in "BCKPST" else 0) + int(hashlib.md5(c.encode()).hexdigest(), 16) % 12
        out.append({"name": c, "score": min(97, sc), "domain": c.lower().replace(" ", "").replace("'", "").replace(".", "") + ".in"})
    ctx["names"] = sorted(out, key=lambda x: -x["score"])
    return "Top name: %s (%d)." % (ctx["names"][0]["name"], ctx["names"][0]["score"])


def designer(ctx):
    h = HUES[ctx["mood"]] + (int(hashlib.md5(ctx["seed"].encode()).hexdigest(), 16) % 20 - 10)
    sat = 0.55 if "Bold" in pers else 0.35 if "Calm" in pers or "Premium" in pers else 0.45
    ctx["pal"] = [("Primary", hexc(h, sat, .32)), ("Secondary", hexc(h + 30, sat * .9, .55)), ("Accent", hexc(h + 180, .65, .55)), ("Light", hexc(h, .3, .95)), ("Ink", hexc(h, .2, .12))]
    return "5-colour palette around hue %d° (%s mood)." % (h % 360, ctx["mood"])


def copywriter(ctx):
    n = ctx["names"][0]["name"]
    ctx["tag"] = llm("Write one 5-7 word tagline for %s: %s. Personality: %s." % (n, biz, pers), "You are a brand copywriter.", 15) or \
        {"Café / food": "Good coffee. Better conversations.", "Tech startup": "Smart tools for everyday work.", "Boutique / fashion": "Wear your story.", "Education / coaching": "Learn today. Lead tomorrow.", "Organic / agri": "From our soil to your table."}[ind]
    ctx["bio"] = "%s - %s in %s. %s" % (n, biz[0].lower() + biz[1:], city, ctx["tag"])
    return "Tagline and social bio written."


if go or "bc" not in st.session_state:
    st.session_state.bc = Pipeline([Agent("Brand Strategist", "Defines mood, fonts and voice", strategist, "🧭"), Agent("Naming Agent", "Generates and scores names with domains", namer, "🏷️"),
                                    Agent("Visual Designer", "Builds the colour palette and logo", designer, "🎨"), Agent("Copywriter", "Writes tagline and bio", copywriter, "✍️")]).run({"seed": seed_word}, show=go)
R = st.session_state.bc
name = st.radio("Choose a name", [n["name"] for n in R["names"]], horizontal=True)
P = dict(R["pal"])
ini = "".join(w[0] for w in name.replace("'s", "").split()[:2]).upper()
logo = ("<svg width='120' height='120' viewBox='0 0 120 120'><circle cx='60' cy='60' r='56' fill='%s'/><circle cx='60' cy='60' r='44' fill='none' stroke='%s' stroke-width='3' stroke-dasharray='6 5'/>"
        "<text x='60' y='74' text-anchor='middle' font-family='%s' font-size='40' font-weight='800' fill='%s'>%s</text></svg>") % (P["Primary"], P["Accent"], R["hf"], P["Light"], ini)
c1, c2, c3 = st.columns([1.2, 1, 1])
c1.markdown("<div class='tile' style='background:%s;display:flex;gap:16px;align-items:center'>%s<div><div style='font-family:%s;font-size:2rem;font-weight:800;color:%s'>%s</div><div style='color:%s'>%s</div></div></div>" % (
    P["Light"], logo, R["hf"], P["Ink"], html.escape(name), P["Primary"], html.escape(R["tag"])), unsafe_allow_html=True)
c2.markdown("<div class='tile'><b>Colour palette</b><div class='sw'>%s</div></div>" % "".join("<div style='background:%s;color:%s'>%s<br>%s</div>" % (v, "#fff" if k in ("Primary", "Ink", "Accent") else "#111", k, v) for k, v in R["pal"]), unsafe_allow_html=True)
c3.markdown("<div class='tile'><b>Typography</b><div style='font-family:%s;font-size:1.8rem;font-weight:800'>Aa %s</div><small>Headings · %s</small><div style='font-family:%s;font-size:1.1rem;margin-top:8px'>The quick brown fox jumps.</div><small>Body · %s</small></div>" % (
    R["hf"], R["hf"].split()[0], R["hf"], R["bf"], R["bf"]), unsafe_allow_html=True)
a, b, c = st.columns(3)
a.markdown("<div class='mock' style='background:%s'><small>Business card</small><div style='font-family:%s;font-size:1.4rem;font-weight:800'>%s</div><small>%s · %s</small><div style='margin-top:30px;color:%s'>hello@%s</div></div>" % (
    P["Primary"], R["hf"], html.escape(name), city, html.escape(R["tag"]), P["Light"], [n["domain"] for n in R["names"] if n["name"] == name][0]), unsafe_allow_html=True)
b.markdown("<div class='mock' style='background:linear-gradient(135deg,%s,%s)'><small>Instagram post</small><div style='font-family:%s;font-size:1.6rem;font-weight:800;margin-top:24px'>%s</div><div>@%s</div></div>" % (
    P["Secondary"], P["Primary"], R["hf"], html.escape(R["tag"]), name.lower().replace(" ", "").replace("'", "")), unsafe_allow_html=True)
with c:
    st.markdown("**Name scores & domains**")
    for n in R["names"][:4]:
        st.markdown("<div class='nm'><b>%s</b> <span style='float:right'>%d</span><br><small>%s</small></div>" % (html.escape(n["name"]), n["score"], n["domain"]), unsafe_allow_html=True)
st.markdown("**Brand voice:** " + "; ".join("%s - %s" % (p, R["voice"][p]) for p in pers) if pers else "**Brand voice:** balanced and clear")
guide = "BRAND GUIDE - %s\nTagline: %s\nBio: %s\nColours: %s\nFonts: %s / %s\nVoice: %s" % (name, R["tag"], R["bio"], ", ".join("%s %s" % kv for kv in R["pal"]), R["hf"], R["bf"], ", ".join(pers))
c_ = st.columns(2)
c_[0].download_button("⬇️ Brand guide (.txt)", guide, "brand_guide.txt")
c_[1].download_button("⬇️ Logo (.svg)", logo, "logo.svg")
show_trace(R["trace"])
