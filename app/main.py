"""Ordinance Lab: a small local dashboard for the EDA pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR.parent) not in sys.path:
    sys.path.insert(0, str(APP_DIR.parent))

from app.services import (  # noqa: E402
    available_years,
    latest_manifest,
    load_table,
    raw_pdf_count,
    read_checklist,
    read_report,
    run_audit,
    status_counts,
)


st.set_page_config(
    page_title="Ordinance Lab",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    :root {
      --ink: #17212b;
      --muted: #64717d;
      --paper: #f5f2eb;
      --card: #fffdf8;
      --line: #ded9cf;
      --coral: #e56b4f;
      --teal: #277d78;
      --navy: #243b53;
    }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stSidebar"] { background: #20333f; }
    [data-testid="stSidebar"] * { color: #f7f2e8; }
    [data-testid="stSidebar"] .stCaption { color: #bdc9ca; }
    h1, h2, h3, p, label, div { font-family: 'Space Grotesk', sans-serif; }
    h1 { letter-spacing: -0.045em; font-size: 3.1rem; color: var(--navy); }
    h2 { letter-spacing: -0.025em; color: var(--navy); }
    [data-testid="stMetric"] {
      background: var(--card); border: 1px solid var(--line);
      border-radius: 14px; padding: 16px 18px;
      box-shadow: 0 5px 18px rgba(36, 59, 83, .05);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    [data-testid="stMetricValue"] { color: var(--navy); }
    .eyebrow {
      color: var(--coral); font-family: 'DM Mono', monospace;
      text-transform: uppercase; letter-spacing: .12em; font-size: .72rem;
      font-weight: 500; margin-bottom: .45rem;
    }
    .hero {
      border-bottom: 1px solid var(--line); padding: 1.2rem 0 1.4rem;
      margin-bottom: 1.5rem;
    }
    .hero p { color: var(--muted); max-width: 720px; font-size: 1.06rem; }
    .notice {
      background: #fff5df; border-left: 4px solid #e2a23b;
      border-radius: 8px; padding: 12px 16px; color: #5e4724;
    }
    .safe-badge {
      display: inline-block; border: 1px solid #76b7a6; color: #246457;
      background: #e6f5ed; border-radius: 999px; padding: 4px 10px;
      font-family: 'DM Mono', monospace; font-size: .72rem;
    }
    .stButton > button {
      border-radius: 9px; border: 0; background: var(--coral); color: white;
      font-weight: 600; min-height: 2.6rem;
    }
    .stButton > button:hover { background: #c8523b; color: white; }
    code, pre { font-family: 'DM Mono', monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)


def metric_value(table: pd.DataFrame | None, predicate) -> int:
    if table is None or table.empty:
        return 0
    return int(predicate(table).sum())


def render_overview(table: pd.DataFrame | None) -> None:
    if table is None or table.empty:
        st.markdown(
            '<div class="notice"><strong>No audit output yet.</strong> '
            'Put PDFs in data/raw/&lt;year&gt; and run an audit from the sidebar.</div>',
            unsafe_allow_html=True,
        )
        return

    total = len(table)
    valid = metric_value(table, lambda frame: frame["temporal_status"] == "valid")
    review = metric_value(
        table, lambda frame: frame["temporal_status"].isin(["review", "unresolved"])
    )
    included = metric_value(table, lambda frame: frame["included_in_corpus"].fillna(False))
    enactment_coverage = table["detected_enactment_year"].notna().mean() * 100

    first, second, third, fourth = st.columns(4)
    first.metric("Documents", f"{total:,}")
    second.metric("Valid placement", f"{valid:,}", f"{valid / total:.0%}" if total else None)
    third.metric("Needs review", f"{review:,}")
    fourth.metric("Eligible for modelling", f"{included:,}")

    st.write("")
    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("Temporal integrity")
        st.bar_chart(status_counts(table), color="#e56b4f", height=285)
    with right:
        st.subheader("Extraction health")
        methods = table["extraction_method"].value_counts().rename("Documents")
        st.bar_chart(methods, color="#277d78", height=285)
        color = "#277d78" if enactment_coverage >= 50 else "#c8523b"
        st.markdown(
            f'<div style="border-top: 1px solid #ded9cf; padding-top: 12px; color: {color};">'
            f'<strong>Enactment signal coverage: {enactment_coverage:.1f}%</strong><br>'
            f'<span style="color:#64717d;">Target: at least 50% before trusting temporal results.</span></div>',
            unsafe_allow_html=True,
        )

    manifest = latest_manifest()
    if manifest:
        st.caption(
            f"Last run: {manifest.get('generated_at_utc', 'unknown')} · "
            f"revision {str(manifest.get('git_revision', 'unknown'))[:10]} · "
            f"{manifest.get('pdf_backend', 'unknown')} backend"
        )


def render_documents(table: pd.DataFrame | None) -> None:
    if table is None or table.empty:
        st.info("Run an audit to populate the document table.")
        return
    st.subheader("Document register")
    first, second, third = st.columns([1, 1, 1.7])
    statuses = ["All"] + sorted(table["temporal_status"].dropna().unique().tolist())
    with first:
        status = st.selectbox("Status", statuses)
    with second:
        years = ["All"] + sorted(table["folder_year"].dropna().astype(int).unique().tolist())
        selected_year = st.selectbox("Folder year", years)
    with third:
        search = st.text_input("Search filename or title", placeholder="e.g. traffic")

    filtered = table.copy()
    if status != "All":
        filtered = filtered[filtered["temporal_status"] == status]
    if selected_year != "All":
        filtered = filtered[filtered["folder_year"] == selected_year]
    if search:
        mask = (
            filtered["filename"].astype(str).str.contains(search, case=False, na=False)
            | filtered.get("title", pd.Series("", index=filtered.index)).astype(str)
              .str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    preferred = [
        "filename", "folder_year", "corpus_year", "temporal_status", "confidence_score",
        "included_in_corpus", "extraction_method", "clean_word_count", "title",
    ]
    columns = [column for column in preferred if column in filtered.columns]
    st.caption(f"Showing {len(filtered):,} of {len(table):,} documents")
    st.dataframe(filtered[columns], use_container_width=True, hide_index=True)


def render_reports() -> None:
    st.subheader("Generated report")
    report_scope = st.radio("Report", ["Corpus", "Year"], horizontal=True)
    if report_scope == "Corpus":
        report = read_report()
    else:
        years = available_years()
        year = st.selectbox("Report year", years) if years else None
        report = read_report(year)
    if report:
        st.markdown(report)
    else:
        st.info("No report is available yet. Run an audit first.")


def main() -> None:
    years = available_years()
    table = load_table()

    st.markdown('<div class="eyebrow">Davao City ordinance corpus</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero"><h1>Ordinance Lab</h1>'
        '<p>A simple control room for auditing, understanding, and preparing the ordinance corpus.</p>'
        '<span class="safe-badge">SAFE AUDIT MODE · no files moved or deleted</span></div>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## Run controls")
        if years:
            scope = st.radio("Audit scope", ["All available years", "Single year"])
            selected_year = st.selectbox("Year", years) if scope == "Single year" else None
        else:
            selected_year = None
            st.warning("No year folders with PDFs found.")
        window_min = st.number_input("Study window start", min_value=1900, max_value=2035, value=2016)
        window_max = st.number_input("Study window end", min_value=1900, max_value=2035, value=2024)
        use_ocr = st.checkbox("Use OCR fallback", value=True)
        use_cache = st.checkbox("Use extraction cache", value=True)
        run = st.button("Run audit", use_container_width=True)
        st.divider()
        st.caption(f"Raw PDFs detected: {raw_pdf_count():,}")
        st.caption("The first version intentionally omits relocation, quarantine, and purge actions.")

    if run:
        if window_min > window_max:
            st.error("The study window start must not be later than the end.")
        else:
            with st.spinner("Running the audit pipeline…"):
                result = run_audit(selected_year, window_min, window_max, use_ocr, use_cache)
            if result.succeeded:
                st.success("Audit completed. Dashboard data refreshed.")
                st.session_state["last_run_output"] = result.output
                st.rerun()
            else:
                st.error("The audit failed. Review the output below.")
                st.code(result.output or "No process output.", language="text")

    if "last_run_output" in st.session_state:
        with st.expander("Last run log"):
            st.code(st.session_state["last_run_output"], language="text")

    tabs = st.tabs(["Overview", "Documents", "Reports", "Thesis checklist"])
    with tabs[0]:
        render_overview(table)
    with tabs[1]:
        render_documents(table)
    with tabs[2]:
        render_reports()
    with tabs[3]:
        st.markdown(read_checklist())


if __name__ == "__main__":
    main()
