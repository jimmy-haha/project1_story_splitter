"""Story Splitter — Streamlit entry point.

Layout:
  Sidebar  → branding, history (last 5 runs), about
  Main     → 1) input area  2) context config  3) run button  4) results + export
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from src.examples import EXAMPLES
from src.exporter import to_csv, to_json, to_markdown
from src.llm import split_requirement
from src.models import SplitResult
from src.parser import parse_uploaded_file

# ----------------------------------------------------------------------------- #
# Page config
# ----------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Story Splitter",
    page_icon="🪓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------- #
# Session state defaults
# ----------------------------------------------------------------------------- #
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: {ts, label, result}
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "input_text" not in st.session_state:
    st.session_state.input_text = ""


def _record_history(result: SplitResult, label: str) -> None:
    entry = {
        "ts": datetime.now().strftime("%H:%M:%S"),
        "label": label,
        "result": result,
    }
    st.session_state.history = (st.session_state.history + [entry])[-5:]


# ----------------------------------------------------------------------------- #
# Sidebar
# ----------------------------------------------------------------------------- #
with st.sidebar:
    st.title("🪓 Story Splitter")
    st.caption("Turn raw PRDs into Jira-ready user stories with AI.")
    st.divider()

    st.subheader("History")
    if not st.session_state.history:
        st.caption("_Your recent splits will appear here._")
    else:
        # Render newest first
        for i, entry in enumerate(reversed(st.session_state.history)):
            label = entry["label"] or "(untitled)"
            if st.button(
                f"🕘 {entry['ts']} — {label[:30]}",
                key=f"hist_{i}",
                use_container_width=True,
            ):
                st.session_state.last_result = entry["result"]
                st.rerun()

    st.divider()
    st.markdown(
        "Made with ❤️ by Pan Jiang  ·  "
        "[GitHub](https://github.com/) · "
        "[About](#)"
    )

# ----------------------------------------------------------------------------- #
# Main — Input area
# ----------------------------------------------------------------------------- #
st.header("1. Paste your requirement")

col1, col2 = st.columns([3, 1])
with col1:
    raw_text = st.text_area(
        "Requirement text",
        value=st.session_state.input_text,
        height=240,
        placeholder="Paste a PRD paragraph, customer email, or meeting note…",
        label_visibility="collapsed",
    )
with col2:
    uploaded = st.file_uploader(
        "…or upload a file",
        type=["txt", "md", "docx"],
    )
    example_name = st.selectbox(
        "…or try an example",
        ["—"] + list(EXAMPLES.keys()),
    )

# Resolve effective input (file/example overrides empty textarea)
input_text = raw_text
if uploaded is not None:
    try:
        input_text = parse_uploaded_file(uploaded)
        st.success(f"Loaded {uploaded.name} ({len(input_text)} chars)")
    except Exception as e:
        st.error(f"Failed to read file: {e}")
elif example_name != "—" and not raw_text.strip():
    input_text = EXAMPLES[example_name]
    st.info(f"Loaded example: **{example_name}**")

# ----------------------------------------------------------------------------- #
# Context configuration
# ----------------------------------------------------------------------------- #
with st.expander("2. Context (optional but highly recommended)", expanded=False):
    cc1, cc2 = st.columns(2)
    with cc1:
        language = st.selectbox(
            "Output language",
            ["English", "中文", "Bilingual"],
            index=0,
        )
        granularity = st.radio(
            "Granularity",
            ["Sprint-ready", "Epic-level", "Auto"],
            horizontal=True,
            index=0,
        )
    with cc2:
        team_ctx = st.text_input(
            "Team context",
            placeholder="e.g. automotive OEM, German stakeholders",
        )
        tech_ctx = st.text_input(
            "Tech stack",
            placeholder="e.g. React + Spring Boot + PostgreSQL",
        )
    model = st.radio(
        "Model",
        ["deepseek-chat", "deepseek-reasoner"],
        horizontal=True,
        index=0,
        help=(
            "deepseek-chat = fast + cheap (V3). "
            "deepseek-reasoner = stronger reasoning (R1), slower."
        ),
    )

# ----------------------------------------------------------------------------- #
# Run
# ----------------------------------------------------------------------------- #
st.write("")
if st.button("✨ Split into Stories", type="primary", use_container_width=True):
    if not input_text.strip():
        st.error("Please paste a requirement, upload a file, or pick an example first.")
    else:
        with st.spinner("AI is splitting your requirement…"):
            try:
                result = split_requirement(
                    raw=input_text,
                    language=language,
                    team_context=team_ctx,
                    tech_stack=tech_ctx,
                    granularity=granularity,
                    model=model,
                )
                st.session_state.last_result = result
                label = (input_text[:40] + "…") if len(input_text) > 40 else input_text
                _record_history(result, label)
                st.toast("Split complete!", icon="✅")
            except Exception as e:
                st.error(f"Something went wrong: {e}")

# ----------------------------------------------------------------------------- #
# Result rendering
# ----------------------------------------------------------------------------- #
result: SplitResult | None = st.session_state.get("last_result")
if result:
    st.divider()
    st.header(f"📦 {len(result.stories)} stories generated")
    st.info(result.summary)

    # Summary metrics
    total_points = sum(
        {"XS": 1, "S": 2, "M": 3, "L": 5, "XL": 8}[s.size.value] for s in result.stories
    )
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Stories", len(result.stories))
    m2.metric("Total points", total_points)
    m3.metric("Sprints (est)", result.sprint_estimate if result.sprint_estimate is not None else "—")
    m4.metric("Risks flagged", len(result.risks))

    if result.suggested_epic_name:
        st.caption(f"Suggested epic: **{result.suggested_epic_name}**")

    # Risks
    if result.risks:
        with st.expander("⚠️ Risks & open questions", expanded=False):
            for r in result.risks:
                st.markdown(f"- {r}")

    # Story cards
    st.subheader("Stories")
    for story in result.stories:
        header = (
            f"**{story.id}** · {story.title}  "
            f"·  `{story.size.value}` · {story.priority.value}"
        )
        with st.expander(header, expanded=False):
            st.markdown(
                f"**As a** {story.as_a}  \n"
                f"**I want** {story.i_want}  \n"
                f"**So that** {story.so_that}"
            )
            st.markdown("**Acceptance Criteria**")
            for i, ac in enumerate(story.acceptance_criteria, 1):
                st.markdown(
                    f"{i}. **Given** {ac.given}  \n"
                    f"   **When** {ac.when}  \n"
                    f"   **Then** {ac.then}"
                )
            meta_cols = st.columns(2)
            with meta_cols[0]:
                if story.dependencies:
                    st.caption(f"Depends on: {', '.join(story.dependencies)}")
            with meta_cols[1]:
                if story.tags:
                    st.caption("Tags: " + " ".join(f"`{t}`" for t in story.tags))
            if story.notes:
                st.warning(story.notes)

    # Export
    st.divider()
    st.subheader("Export")
    e1, e2, e3 = st.columns(3)
    e1.download_button(
        "⬇️ CSV (Jira-ready)",
        to_csv(result),
        file_name="stories.csv",
        mime="text/csv",
        use_container_width=True,
    )
    e2.download_button(
        "⬇️ Markdown",
        to_markdown(result),
        file_name="stories.md",
        mime="text/markdown",
        use_container_width=True,
    )
    e3.download_button(
        "⬇️ JSON",
        to_json(result),
        file_name="stories.json",
        mime="application/json",
        use_container_width=True,
    )
else:
    st.caption(
        "👆 Paste a requirement (or pick an example) and hit "
        "**Split into Stories** to get started."
    )
