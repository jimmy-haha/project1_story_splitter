# 🪓 Story Splitter

> Turn raw PRDs, customer emails, or meeting notes into **Jira-ready user stories** —
> backed by 10+ years of BA experience, codified as prompts.

**🌐 Live demo**: _coming soon — deploy via Streamlit Community Cloud_
**📹 30-sec walkthrough**: _coming soon_

![hero](assets/screenshots/hero.png)

---

## Why

In agile teams, the gap between _"the customer said X"_ and _"developers can pick up a story tomorrow"_
is where requirements rot. Story Splitter compresses that gap by combining a
senior-BA prompt with structured LLM output and one-click Jira export.

It is **not a ChatGPT wrapper**. The value lives in three places:

1. A professional prompt template forged from real BA practice (INVEST, MoSCoW, Given/When/Then).
2. Strict Pydantic-validated structured output — no free-form prose.
3. Multi-format export (CSV / Markdown / JSON) that drops straight into Jira / Confluence / GitHub.

---

## Features

- 📋 Paste text, or upload `.docx` / `.txt` / `.md`
- 🌏 Context-aware splitting (team background, tech stack, granularity)
- 🎯 INVEST-aligned stories with **Given/When/Then** acceptance criteria
- 👕 T-shirt sizing + dependency graph + risk surfacing
- 📤 Export to **Jira-compatible CSV**, **Markdown**, or **JSON**
- 🌐 Bilingual output (中 / EN / both)
- 🕘 Session history (last 5 splits)
- ⚙️ Choose between **DeepSeek V3** (`deepseek-chat`, fast/cheap) and **DeepSeek R1** (`deepseek-reasoner`, stronger reasoning)

---

## Architecture

```text
[Streamlit UI: app.py]
        │
        │ raw text + context
        ▼
[src/llm.py] ── render prompt ──► [DeepSeek API (OpenAI-compatible)]
        │                              │
        │      JSON-mode response ◄────┘
        ▼
[Pydantic validation: src/models.py]
        │
        ├─ on failure → retry up to N times
        │
        ▼
[src/exporter.py]  →  CSV / MD / JSON downloads
```

> The LLM layer talks to DeepSeek through the `openai` SDK with a custom
> `base_url`, so swapping to OpenAI / Together / Groq / a local Ollama
> later is literally a one-line change.

---

## Prompt-engineering notes

The prompt (`prompts/story_split.md`) makes a few deliberate design bets:

- **Persona pinning**: "Senior BA with 10+ years agile experience" anchors the
  model to professional output rather than generic LLM verbosity.
- **INVEST as a contract**, not a suggestion — the model knows what "well-formed"
  means before it starts generating.
- **Two-layer JSON safety**: we ask DeepSeek for `response_format={"type":
  "json_object"}` (its native JSON mode, which guarantees syntactic validity)
  **and** inject the Pydantic JSON schema into the prompt so the model knows
  the required *shape*. A fence-stripping regex + retry loop catches the rare
  edge cases. Result: structured output without flaky prompt-engineering.
- **Explicit XL flag**: any XL story must self-flag with `needs further split`
  in `notes` — preventing the model from emitting unactionable mega-stories.
- **Risks as first-class output**: surface uncertainty rather than silently
  inventing requirements. This is the single biggest differentiator from
  "give me user stories" ChatGPT prompting.

---

## Run locally

```bash
git clone https://github.com/<you>/story-splitter.git
cd story-splitter

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set DEEPSEEK_API_KEY=sk-...
# Get a key at https://platform.deepseek.com/api_keys

streamlit run app.py
```

## Run tests

```bash
pytest -q
```

All tests are fully mocked — no API key is required to run the test suite.

---

## Deploying to Streamlit Cloud (5 minutes)

1. Push this repo to GitHub (public).
2. Visit https://share.streamlit.io → **New app** → select your repo → main file = `app.py`.
3. **Advanced settings → Secrets**, add:
   ```toml
   DEEPSEEK_API_KEY = "sk-..."
   ```
4. Deploy. Copy the resulting `https://<your-app>.streamlit.app` link into
   the **About** section of your GitHub repo.

---

## Project layout

```text
story-splitter/
├── app.py                  # Streamlit entry point
├── prompts/
│   └── story_split.md      # ★ the senior-BA prompt
├── src/
│   ├── models.py           # Pydantic models (the LLM contract)
│   ├── llm.py              # Anthropic call + JSON validation + retries
│   ├── parser.py           # .docx / .txt / .md → text
│   ├── exporter.py         # CSV / MD / JSON output
│   └── examples.py         # 3 demo requirements
├── tests/                  # pytest suite (no live API needed)
├── .streamlit/config.toml  # theme
├── requirements.txt
└── .env.example
```

---

## Roadmap

- [ ] Streaming output (token-by-token)
- [ ] Per-story "refine further" button
- [ ] INVEST-violation detector with suggested fixes
- [ ] Direct Jira API push (instead of CSV)
- [ ] Dark theme

---

## Built with AI

This project was built with Cursor + Claude as a pair-programming partner —
roughly **~12 hours over 2 days** of human time. The prompt template under
`prompts/` is the soul of the project; everything else is plumbing.

## License

MIT — see [`LICENSE`](./LICENSE).
