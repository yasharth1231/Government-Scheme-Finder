import os, json, html
import streamlit as st
import store, ingest, rules, llm
from config import *

st.set_page_config(page_title="Government Scheme Finder", page_icon="🏛️", layout="wide")

# ====================================================================== STYLE
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
.stApp, .stApp p, .stApp label, .stApp button, .stApp h1, .stApp h2, .stApp h3, .stApp li {
    font-family: 'Poppins', sans-serif;
}
#MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 1.4rem; max-width: 1100px;}

/* hero */
.hero {background: linear-gradient(135deg,#1F2A6B 0%,#3B4CCA 55%,#6A78FF 100%);
       border-radius: 22px; padding: 2rem 2.2rem; color: #fff; margin-bottom: 1.2rem;
       box-shadow: 0 10px 30px rgba(59,76,202,.25);}
.hero h1 {color:#fff; margin:0; font-size:2rem; font-weight:700; line-height:1.25;}
.hero p {color:#DCE1FF; margin:.5rem 0 0; font-size:1rem;}
.tricolor {height:5px; width:150px; border-radius:6px; margin-top:1.1rem;
           background: linear-gradient(90deg,#FF9933 33.3%,#FFFFFF 33.3% 66.6%,#138808 66.6%);}
.hero-tags {margin-top:1rem; display:flex; gap:.5rem; flex-wrap:wrap;}
.hero-tags span {background: rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.25);
                 padding:.25rem .8rem; border-radius:999px; font-size:.8rem; color:#fff;}

/* tabs */
.stTabs [data-baseweb="tab-list"] {gap: 8px; border-bottom: none;}
.stTabs [data-baseweb="tab"] {background:#E9ECFA; border-radius: 12px; padding: 8px 20px; height:auto;}
.stTabs [aria-selected="true"] {background:#3B4CCA;}
.stTabs [aria-selected="true"] p {color:#fff !important;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {display:none;}

/* form + containers */
[data-testid="stForm"] {background:#fff; border:1px solid #E3E7F7; border-radius:18px;
                        padding:1.4rem 1.5rem; box-shadow:0 4px 18px rgba(31,42,107,.06);}
[data-testid="stVerticalBlockBorderWrapper"]:has(.result-head) {background:#fff; border-radius:18px;
                        border:1px solid #E3E7F7; box-shadow:0 4px 18px rgba(31,42,107,.07);}
.stButton>button, .stFormSubmitButton>button {border-radius:12px; font-weight:600; padding:.6rem 1.2rem;}
[data-testid="stSidebar"] {border-right:1px solid #E3E7F7;}

/* section titles */
.section-title {font-size:1.25rem; font-weight:700; margin:1.2rem 0 .6rem; color:#1B2559;}
.section-sub {color:#6B7390; font-size:.9rem; margin-top:-.4rem; margin-bottom:.8rem;}

/* stat tiles */
.stat {background:#fff; border:1px solid #E3E7F7; border-radius:16px; padding:1rem 1.2rem;
       box-shadow:0 4px 14px rgba(31,42,107,.05);}
.stat .num {font-size:1.9rem; font-weight:700; line-height:1.1;}
.stat .lbl {color:#6B7390; font-size:.85rem;}
.stat.ok .num {color:#137A3A;} .stat.maybe .num {color:#B45F06;} .stat.no .num {color:#B42318;}

/* result card */
.result-head {display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;}
.result-title {font-size:1.2rem; font-weight:700; color:#1B2559;}
.pill {padding:.3rem .9rem; border-radius:999px; font-size:.8rem; font-weight:600; white-space:nowrap;}
.pill.ok {background:#E6F6EC; color:#137A3A;}
.pill.maybe {background:#FFF4E0; color:#B45F06;}
.pill.no {background:#FDECEC; color:#B42318;}
.reason {color:#39406B; margin:.6rem 0 .8rem; line-height:1.6;}
.label {font-size:.72rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase;
        color:#8A90AD; margin:.7rem 0 .3rem;}
.chip {display:inline-block; background:#EEF0FF; color:#3B4CCA; border-radius:999px;
       padding:.25rem .75rem; margin:0 .35rem .35rem 0; font-size:.8rem;}
.chip.green {background:#E6F6EC; color:#137A3A;}
.chip.red {background:#FDECEC; color:#B42318;}
.confirm {background:#FFF8E8; border-left:4px solid #F5A524; border-radius:10px;
          padding:.6rem .9rem; color:#7A4A06; font-size:.9rem; margin:.5rem 0;}
.infobox {background:#F6F7FD; border-radius:12px; padding:.7rem .9rem; color:#39406B; font-size:.92rem;}
.disclaimer {text-align:center; color:#8A90AD; font-size:.8rem; margin-top:1.5rem;}
.sidebar-brand {font-size:1.2rem; font-weight:700; color:#1B2559;}
</style>
""", unsafe_allow_html=True)


def esc(x):
    return html.escape(str(x))


def chips(items, cls=""):
    return "".join(f'<span class="chip {cls}">{esc(i)}</span>' for i in items)


def stat(num, label, cls):
    return f'<div class="stat {cls}"><div class="num">{num}</div><div class="lbl">{label}</div></div>'


# ====================================================================== SIDEBAR
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🏛️ Scheme Finder</div>', unsafe_allow_html=True)
    st.caption("Powered by Gemini + local RAG")
    st.divider()
    api_key = st.text_input("Gemini API key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
    st.caption(f"Model: `{LLM_MODEL}`")
    used, left = store.calls_used(), store.calls_left()
    st.metric("API calls left today", left, help=f"{used} used of {DAILY_LIMIT} (keeping {SAFETY_MARGIN} in reserve)")
    st.progress(min(1.0, used / max(DAILY_LIMIT, 1)))
    st.caption("Search, embeddings and eligibility rules run locally and cost 0 calls.")

# ====================================================================== HERO
st.markdown("""
<div class="hero">
  <h1>Find government schemes you qualify for</h1>
  <p>Tell us a little about yourself and we will match you with schemes, with the reason for each match.</p>
  <div class="hero-tags"><span>📄 Based on official scheme documents</span><span>⚡ Instant rule-based check</span><span>🔒 Nothing stored about you</span></div>
  <div class="tricolor"></div>
</div>
""", unsafe_allow_html=True)

tab_find, tab_admin, tab_review = st.tabs(["🔎  Find schemes", "📥  Add schemes", "📝  Review criteria"])

# ====================================================================== ADMIN TAB
with tab_admin:
    st.markdown('<div class="section-title">1. Upload and index PDFs</div>'
                '<div class="section-sub">Uses 0 API calls. The file name becomes the scheme name.</div>',
                unsafe_allow_html=True)
    files = st.file_uploader("Scheme PDFs", type="pdf", accept_multiple_files=True, label_visibility="collapsed")
    if st.button("Index PDFs", type="primary") and files:
        bar = st.progress(0.0)
        for i, f in enumerate(files):
            name = os.path.splitext(f.name)[0].replace("_", " ").replace("-", " ")
            sid = ingest.slugify(name)
            text, ocr_pages, ocr_err = ingest.extract_text(f.read())
            if len(text.strip()) < 50:
                st.error(f"{f.name}: no readable text. " + (f"OCR failed: {ocr_err}" if ocr_err else ""))
            else:
                h = ingest.text_hash(text)
                existing = store.get_scheme(sid)
                if existing and existing["text_hash"] == h:
                    st.info(f"{f.name}: unchanged, skipped.")
                else:
                    store.upsert_scheme(sid, name, h, ingest.eligibility_text(text), ocr_pages)
                    store.add_chunks(sid, name, ingest.make_chunks(text))
                    st.success(f"{f.name}: indexed" + (f" (OCR used on {ocr_pages} pages)" if ocr_pages else ""))
                    if ocr_err:
                        st.warning(f"{f.name}: some pages need OCR but Tesseract is unavailable: {ocr_err}")
            bar.progress((i + 1) / len(files))

    st.markdown('<div class="section-title">2. Indexed schemes and criteria</div>', unsafe_allow_html=True)
    all_schemes = store.list_schemes()
    if all_schemes:
        st.dataframe([{"Scheme": s["name"], "OCR pages": s["ocr_pages"],
                       "Criteria extracted": "✅ Yes" if s["criteria_json"] else "⏳ No"} for s in all_schemes],
                     use_container_width=True, hide_index=True)
        with st.expander("✏️ Rename a scheme (0 API calls)"):
            target = st.selectbox("Scheme to rename", all_schemes, format_func=lambda s: s["name"], key="rename_pick")
            new_name = st.text_input("New name", value=target["name"], key=f"rename-{target['scheme_id']}")
            if st.button("Save name"):
                if new_name.strip():
                    store.rename_scheme(target["scheme_id"], new_name)
                    st.success(f"Renamed to: {new_name.strip()}")
                    st.rerun()
                else:
                    st.error("Name cannot be empty.")
    else:
        st.info("No schemes indexed yet. Upload PDFs and click 'Index PDFs' above.")

    pending = [s for s in all_schemes if not s["criteria_json"]]
    calls_needed = -(-len(pending) // EXTRACT_BATCH)
    st.markdown('<div class="section-title">3. Extract eligibility criteria</div>'
                f'<div class="section-sub">{len(pending)} scheme(s) waiting → {calls_needed} API call(s) '
                f'({EXTRACT_BATCH} schemes per call). {left} call(s) available today.</div>', unsafe_allow_html=True)
    if pending and st.button(f"Extract criteria ({calls_needed} calls)", type="primary"):
        if not api_key:
            st.error("Enter your API key first.")
        else:
            for i in range(0, len(pending), EXTRACT_BATCH):
                batch = pending[i:i + EXTRACT_BATCH]
                try:
                    out = llm.extract_criteria_batch(api_key, [dict(b) for b in batch])
                    ids = {b["scheme_id"] for b in batch}
                    for c in out:
                        if c.get("scheme_id") in ids:
                            store.save_criteria(c["scheme_id"], c)
                    st.success(f"Extracted {len(out)} scheme(s).")
                except llm.QuotaExceeded as e:
                    st.warning(f"{e} Continue tomorrow; progress is saved.")
                    break
                except Exception as e:
                    st.error(f"Extraction failed: {e}")
                    break
            st.rerun()
    if all_schemes and not pending:
        st.success("All indexed schemes already have criteria. Nothing to extract.")
        with st.expander("Re-extract everything (uses API calls)"):
            st.write(f"This clears all criteria, including manual edits, and needs "
                     f"{-(-len(all_schemes) // EXTRACT_BATCH)} call(s).")
            if st.button("Clear criteria and re-extract"):
                store.reset_all_criteria()
                st.rerun()

# ====================================================================== REVIEW TAB
with tab_review:
    st.markdown('<div class="section-title">Review extracted criteria</div>'
                '<div class="section-sub">Wrong rules mean wrong results. Fix them here (no API call).</div>',
                unsafe_allow_html=True)
    schemes = [s for s in store.list_schemes() if s["criteria_json"]]
    if not schemes:
        st.info("No criteria yet. Index PDFs and run extraction first.")
    else:
        pick = st.selectbox("Scheme", schemes, format_func=lambda s: s["name"])
        edited = st.text_area("Criteria (JSON)", json.dumps(json.loads(pick["criteria_json"]), indent=2),
                              height=320, key=f"edit-{pick['scheme_id']}")
        if st.button("Save changes", type="primary"):
            try:
                store.save_criteria(pick["scheme_id"], json.loads(edited))
                st.success("Saved.")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")

# ====================================================================== FIND TAB
with tab_find:
    st.markdown('<div class="section-title">Your details</div>'
                '<div class="section-sub">Used only to check eligibility. Nothing is saved.</div>',
                unsafe_allow_html=True)
    with st.form("profile"):
        c1, c2, c3 = st.columns(3)
        age = c1.number_input("Age", 0, 120, 30)
        income = c2.number_input("Annual family income (₹)", 0, 100_000_000, 200_000, step=10_000)
        state = c3.selectbox("State", STATES, index=STATES.index("Maharashtra"))
        c4, c5, c6 = st.columns(3)
        occupation = c4.selectbox("Occupation", OCCUPATIONS)
        gender = c5.selectbox("Gender", GENDERS)
        category = c6.selectbox("Social category", CATEGORIES)
        c7, c8 = st.columns(2)
        disability = c7.checkbox("Person with disability")
        bpl = c8.checkbox("Has BPL card")
        go = st.form_submit_button("🔍  Find my schemes", type="primary", use_container_width=True)

    if go:
        profile = {"age": int(age), "income": int(income), "state": state, "occupation": occupation,
                   "gender": gender, "category": category, "disability": disability, "bpl": bpl}
        ready = [s for s in store.list_schemes() if s["criteria_json"]]
        if not ready:
            st.warning("No schemes are ready yet. Use the 'Add schemes' tab first.")
            st.stop()

        key = store.cache_key(profile)
        results = store.cache_get(key)
        source = "cache (0 API calls)"

        if results is None:
            with st.spinner("Checking eligibility..."):
                cands, rejected = [], []
                for s in ready:
                    status, matched, failed, confirm = rules.evaluate(profile, json.loads(s["criteria_json"]))
                    row = {"scheme_id": s["scheme_id"], "name": s["name"], "status": status,
                           "matched": matched, "failed": failed, "to_confirm": confirm}
                    (rejected if status == "Not eligible" else cands).append(row)
                cands.sort(key=lambda r: r["status"] != "Eligible")

                qvec = store.embed([f"eligibility benefits documents required how to apply "
                                    f"{occupation} {category} {gender} {state}"])[0]
                for r in cands:
                    r["excerpts"] = store.search_scheme(r["scheme_id"], qvec, CHUNKS_PER_SCHEME)

                explained = {}
                top = cands[:MAX_EXPLAIN]
                source = "rules + RAG only (no API call used)"
                if top and api_key:
                    try:
                        out = llm.explain(api_key, profile, top)
                        explained = {o.get("scheme_id"): o for o in out}
                        source = "rules + RAG + 1 Gemini call"
                    except llm.QuotaExceeded:
                        source = "daily quota reached: showing rule-based results only"
                    except Exception as e:
                        source = f"Gemini error ({e}): showing rule-based results only"
                elif top:
                    source = "no API key: showing rule-based results only"

                for r in cands:
                    e = explained.get(r["scheme_id"], {})
                    r["reason"] = e.get("reason") or ("Matches: " + "; ".join(r["matched"])
                                                      if r["matched"] else "No conflicting criteria found.")
                    r["benefits"] = e.get("benefits", "")
                    r["documents_required"] = e.get("documents_required", [])
                    r["how_to_apply"] = e.get("how_to_apply", "")
                results = {"candidates": cands, "rejected": rejected}
                if explained or not top:
                    store.cache_put(key, results)

        cands, rejected = results["candidates"], results["rejected"]
        n_ok = sum(r["status"] == "Eligible" for r in cands)
        n_maybe = len(cands) - n_ok

        st.markdown('<div class="section-title">Your results</div>', unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        s1.markdown(stat(n_ok, "Eligible", "ok"), unsafe_allow_html=True)
        s2.markdown(stat(n_maybe, "Possibly eligible", "maybe"), unsafe_allow_html=True)
        s3.markdown(stat(len(rejected), "Not eligible", "no"), unsafe_allow_html=True)
        st.caption(f"Answer source: {source}")

        if not cands:
            st.info("No matching schemes found among the indexed schemes.")
        for r in cands:
            ok = r["status"] == "Eligible"
            with st.container(border=True):
                st.markdown(
                    f'<div class="result-head"><div class="result-title">{esc(r["name"])}</div>'
                    f'<span class="pill {"ok" if ok else "maybe"}">{"✓ Eligible" if ok else "⚠ Possibly eligible"}</span></div>'
                    f'<div class="reason">{esc(r["reason"])}</div>', unsafe_allow_html=True)
                if r["matched"]:
                    st.markdown('<div class="label">Criteria matched</div>' + chips(r["matched"], "green"),
                                unsafe_allow_html=True)
                if r["to_confirm"]:
                    st.markdown(f'<div class="confirm"><b>Please confirm:</b> {esc("; ".join(r["to_confirm"]))}</div>',
                                unsafe_allow_html=True)
                if r.get("benefits"):
                    st.markdown(f'<div class="label">Benefits</div><div class="infobox">{esc(r["benefits"])}</div>',
                                unsafe_allow_html=True)
                if r.get("documents_required"):
                    st.markdown('<div class="label">Documents required</div>' + chips(r["documents_required"]),
                                unsafe_allow_html=True)
                if r.get("how_to_apply"):
                    st.markdown(f'<div class="label">How to apply</div><div class="infobox">{esc(r["how_to_apply"])}</div>',
                                unsafe_allow_html=True)
                if r.get("excerpts"):
                    with st.expander("📄 Source excerpts from the scheme document"):
                        for ex in r["excerpts"]:
                            st.write("• " + ex)

        if rejected:
            with st.expander(f"❌ Not eligible ({len(rejected)})"):
                for r in rejected:
                    st.markdown(f'<div class="label">{esc(r["name"])}</div>' + chips(r["failed"], "red"),
                                unsafe_allow_html=True)

        st.markdown('<div class="disclaimer">⚠️ Indicative only. Always verify eligibility on the official '
                    'government portal before applying.</div>', unsafe_allow_html=True)