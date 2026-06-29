# Story Splitter — 详细 Spec（Vibe Coding Ready）

> 这份文档可以**整篇丢给 Cursor 作为系统提示 / 项目上下文**，然后让它按 §10 的实施步骤一步步实现。

---

## 0. 项目身份

| 字段 | 值 |
|---|---|
| 产品名称 | **Story Splitter**（中文可叫"需求拆解器"） |
| 目标用户 | Agile 团队的 BA / PO / PM，尤其跨国/跨语言团队 |
| 一句话价值 | 把一段 PRD/需求描述，AI 拆成 Jira-ready 的 User Stories（含 AC、估点、依赖） |
| 技术形态 | Streamlit Web App，单页面，可在线访问 |
| 预计工时 | 1.5–2 天（全职 vibe code） |
| 上线目标 | Streamlit Community Cloud，得到一个 `https://xxx.streamlit.app` 链接 |
| Repo 名建议 | `story-splitter` |

---

## 1. 设计理念（写代码前必须读）

1. **不是 ChatGPT 套壳**。区别在于：
   - 我们沉淀了**专业 prompt 模板**（基于 BA 经验）
   - 我们做了**结构化输出 + 校验**（不是输出散文）
   - 我们提供**多种导出格式**（CSV / Markdown / JSON）直接对接团队工具
   - 我们支持**上下文注入**（项目类型、技术栈、团队约定），让结果可用

2. **MVP 必须能 demo**。所有功能要服务于"30 秒视频里看得到效果"。

3. **代码风格**：可读性 > 巧妙。Python 3.11+，类型注解齐全，Pydantic 校验所有 LLM 输出。

---

## 2. 功能清单

### MVP（Day 1-2 必须做完）

- [x] **输入区**
  - 多行文本框：粘贴需求文字
  - 文件上传：支持 `.txt` / `.md` / `.docx`
  - 示例按钮：一键填入示范需求（要准备 3 个示例：电商、汽车、内部工具）
- [x] **上下文配置区**（折叠面板，默认收起）
  - 输出语言：中文 / 英文 / 双语
  - 团队背景：自由文本，例 "automotive OEM, working with German stakeholders"
  - 技术栈：自由文本，例 "React + Spring Boot + PostgreSQL"
  - 拆解粒度：Sprint-ready / Epic-level / 自动判断
  - LLM 模型：claude-3-5-sonnet / claude-3-5-haiku（成本对比）
- [x] **执行按钮**："✨ Split into Stories"，调用 LLM
- [x] **结果区**
  - 每个 story 一张卡片，可展开/折叠
  - 卡片字段（见 §4 数据模型）
  - 顶部摘要：共 N 个 story / 总估点 / 预估 sprint 数
- [x] **导出区**
  - 复制 Markdown
  - 下载 CSV（Jira-import 兼容字段）
  - 下载 JSON
- [x] **历史记录**（用 `st.session_state` 即可，刷新丢失没关系）
  - 侧边栏列出近 5 次拆解
  - 点击可回看

### V1.1（有时间再做，加分项）

- [ ] 流式输出（边生成边展示）
- [ ] 中英对照模式
- [ ] 每个 story 单独"重新拆得更细"按钮
- [ ] 检测"非 INVEST"的 story 并给改进建议
- [ ] 暗黑主题

### 明确不做（防止失焦）

- ❌ 用户登录系统
- ❌ 后端数据库
- ❌ 团队协作 / 评论
- ❌ Jira API 直连（先做 CSV 导出就够了）
- ❌ 多 LLM provider 抽象（先只接 Anthropic）

---

## 3. 用户流程图

```text
[首页]
   │
   ├─ 用户粘贴需求 OR 上传 docx OR 点击示例
   │
   ├─ (可选) 展开配置面板，填写团队/技术上下文
   │
   ▼
[点击 "Split into Stories"]
   │
   ├─ 显示 spinner "AI is splitting…"
   ├─ 调用 LLM，拿到结构化 JSON
   ├─ Pydantic 校验
   │     ├─ 通过 → 渲染卡片
   │     └─ 失败 → 重试一次 + 显示 raw response 让用户看到
   ▼
[结果页]
   │
   ├─ 顶部摘要条
   ├─ N 张 story 卡片（可折叠）
   ├─ 导出按钮组
   └─ "Try another input" 回到首页
```

---

## 4. 数据模型（Pydantic）

```python
from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum

class StorySize(str, Enum):
    XS = "XS"  # < 1 day
    S = "S"    # 1-2 days
    M = "M"    # 3-5 days
    L = "L"    # 1-2 weeks
    XL = "XL"  # > 2 weeks, must be split

class Priority(str, Enum):
    MUST = "Must Have"
    SHOULD = "Should Have"
    COULD = "Could Have"
    WONT = "Won't Have"

class AcceptanceCriterion(BaseModel):
    given: str = Field(description="Given clause")
    when: str = Field(description="When clause")
    then: str = Field(description="Then clause")

class UserStory(BaseModel):
    id: str = Field(description="Auto-generated, e.g. US-001")
    title: str = Field(description="Short, action-oriented, < 80 chars")
    as_a: str = Field(description="The persona / role")
    i_want: str = Field(description="The capability / action")
    so_that: str = Field(description="The business value / outcome")
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=2)
    size: StorySize
    priority: Priority
    dependencies: list[str] = Field(default_factory=list, description="Other story IDs this depends on")
    tags: list[str] = Field(default_factory=list, description="e.g. ['frontend', 'api', 'cross-team']")
    notes: str | None = Field(default=None, description="Open questions or assumptions")

class SplitResult(BaseModel):
    summary: str = Field(description="2-3 sentence summary of what was split")
    stories: list[UserStory]
    suggested_epic_name: str | None = None
    sprint_estimate: int | None = Field(default=None, description="Rough number of sprints needed")
    risks: list[str] = Field(default_factory=list)
```

---

## 5. Prompt 模板（核心资产）

把它存到 `prompts/story_split.md`，让 Cursor 可以随时调整。

```markdown
You are a Senior Business Analyst with 10+ years of agile experience,
specialized in user story decomposition following INVEST principles
(Independent, Negotiable, Valuable, Estimable, Small, Testable).

## Your task
Given a raw requirement (which may be a PRD paragraph, a customer email,
a feature idea, or a meeting note), break it down into well-formed
user stories that a sprint team can pick up immediately.

## Context for this request
- Output language: {language}
- Team context: {team_context}
- Tech stack: {tech_stack}
- Granularity: {granularity}

## Quality bar
1. Each story must follow the "As a X, I want Y, so that Z" pattern,
   and Z must be a real business outcome, not a restatement of Y.
2. Each story must have at least 2 acceptance criteria in
   Given/When/Then form. Cover happy path AND at least one edge case.
3. Size each story using T-shirt sizes (XS/S/M/L/XL). Any XL must be
   flagged as "needs further split" in notes.
4. Identify dependencies between stories using IDs (US-001 etc.).
5. Surface risks, open questions, or assumptions — do not silently invent.
6. If the input is vague, prefer fewer well-defined stories over many
   half-baked ones.

## Output format
Return STRICT JSON matching this schema (no markdown fences, no commentary):

{json_schema}

## Raw requirement
<<<
{raw_requirement}
>>>
```

> **重点**：让 Anthropic 的 tool-use / structured output 模式来保证 JSON 合法。如果用 OpenAI 用 `response_format={"type": "json_schema", ...}`。

---

## 6. 项目结构

```text
story-splitter/
├── README.md                  # ★ 简历用，必须好好写
├── requirements.txt
├── .env.example               # ANTHROPIC_API_KEY=...
├── .gitignore                 # 不要提交 .env
├── .streamlit/
│   └── config.toml            # 主题色等
├── app.py                     # Streamlit 入口
├── src/
│   ├── __init__.py
│   ├── models.py              # Pydantic 模型 (§4)
│   ├── llm.py                 # LLM 调用 + 重试 + JSON 校验
│   ├── parser.py              # .docx / .txt 解析
│   ├── exporter.py            # CSV / MD / JSON 导出
│   └── examples.py            # 3 个示例需求
├── prompts/
│   └── story_split.md         # §5 的 prompt 模板
├── tests/
│   ├── test_parser.py
│   ├── test_exporter.py
│   └── test_models.py
└── assets/
    └── screenshots/           # 给 README 用
```

---

## 7. 关键文件骨架（让 Cursor 照着填）

### `requirements.txt`
```text
streamlit>=1.36
anthropic>=0.34
pydantic>=2.7
python-docx>=1.1
python-dotenv>=1.0
pandas>=2.2
```

### `app.py` 骨架
```python
import streamlit as st
from src.models import SplitResult
from src.llm import split_requirement
from src.parser import parse_uploaded_file
from src.exporter import to_csv, to_markdown, to_json
from src.examples import EXAMPLES

st.set_page_config(page_title="Story Splitter", page_icon="🪓", layout="wide")

# --- Sidebar: history + about ---
with st.sidebar:
    st.title("🪓 Story Splitter")
    st.caption("Turn PRDs into Jira-ready user stories with AI.")
    st.divider()
    st.subheader("History")
    # render st.session_state.history
    st.divider()
    st.markdown("Made with ❤️ by Pan Jiang  ·  [GitHub](#)")

# --- Main: input area ---
st.header("1. Paste your requirement")
col1, col2 = st.columns([3, 1])
with col1:
    raw_text = st.text_area("Requirement text", height=240, placeholder="Paste PRD, email, meeting note…")
with col2:
    uploaded = st.file_uploader("…or upload", type=["txt", "md", "docx"])
    example_name = st.selectbox("…or try an example", ["—"] + list(EXAMPLES.keys()))

# Resolve input
input_text = raw_text
if uploaded:
    input_text = parse_uploaded_file(uploaded)
elif example_name != "—":
    input_text = EXAMPLES[example_name]

# --- Context configuration ---
with st.expander("2. Context (optional but recommended)"):
    language = st.selectbox("Output language", ["English", "中文", "Bilingual"])
    team_ctx = st.text_input("Team context", placeholder="e.g. automotive OEM, German stakeholders")
    tech_ctx = st.text_input("Tech stack", placeholder="e.g. React + Spring Boot + PostgreSQL")
    granularity = st.radio("Granularity", ["Sprint-ready", "Epic-level", "Auto"], horizontal=True)
    model = st.radio("Model", ["claude-3-5-sonnet", "claude-3-5-haiku"], horizontal=True)

# --- Run ---
if st.button("✨ Split into Stories", type="primary", use_container_width=True):
    if not input_text.strip():
        st.error("Please provide a requirement first.")
    else:
        with st.spinner("AI is splitting your requirement…"):
            result: SplitResult = split_requirement(
                raw=input_text,
                language=language,
                team_context=team_ctx,
                tech_stack=tech_ctx,
                granularity=granularity,
                model=model,
            )
        st.session_state.last_result = result
        st.session_state.history = (st.session_state.get("history", []) + [result])[-5:]

# --- Result rendering ---
result = st.session_state.get("last_result")
if result:
    st.divider()
    st.header(f"📦 {len(result.stories)} stories generated")
    st.info(result.summary)

    # Summary metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Stories", len(result.stories))
    c2.metric("Sprints (est)", result.sprint_estimate or "—")
    c3.metric("Risks flagged", len(result.risks))

    # Story cards
    for story in result.stories:
        with st.expander(f"**{story.id}** · {story.title}  ·  `{story.size.value}` · {story.priority.value}"):
            st.markdown(f"**As a** {story.as_a}\n\n**I want** {story.i_want}\n\n**So that** {story.so_that}")
            st.markdown("**Acceptance Criteria**")
            for i, ac in enumerate(story.acceptance_criteria, 1):
                st.markdown(f"{i}. **Given** {ac.given}  \n   **When** {ac.when}  \n   **Then** {ac.then}")
            if story.dependencies:
                st.caption(f"Depends on: {', '.join(story.dependencies)}")
            if story.tags:
                st.caption("Tags: " + " ".join(f"`{t}`" for t in story.tags))
            if story.notes:
                st.warning(story.notes)

    # Export
    st.divider()
    st.subheader("Export")
    e1, e2, e3 = st.columns(3)
    e1.download_button("⬇️ CSV (Jira)", to_csv(result), file_name="stories.csv", mime="text/csv")
    e2.download_button("⬇️ Markdown", to_markdown(result), file_name="stories.md", mime="text/markdown")
    e3.download_button("⬇️ JSON", to_json(result), file_name="stories.json", mime="application/json")
```

### `src/llm.py` 骨架
```python
import json
import os
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv
from .models import SplitResult

load_dotenv()
_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
_PROMPT = (Path(__file__).parent.parent / "prompts" / "story_split.md").read_text()

def split_requirement(
    raw: str,
    language: str,
    team_context: str,
    tech_stack: str,
    granularity: str,
    model: str,
    max_retries: int = 2,
) -> SplitResult:
    schema = SplitResult.model_json_schema()
    prompt = _PROMPT.format(
        language=language,
        team_context=team_context or "general SaaS team",
        tech_stack=tech_stack or "modern web stack",
        granularity=granularity,
        json_schema=json.dumps(schema, indent=2, ensure_ascii=False),
        raw_requirement=raw.strip(),
    )

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        resp = _client.messages.create(
            model=f"{model}-latest",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        # Strip code fences if the model still added them
        if text.startswith("```"):
            text = text.split("```")[1].lstrip("json").strip()
        try:
            return SplitResult.model_validate_json(text)
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"LLM output failed validation after retries: {last_err}")
```

### `src/exporter.py` 骨架
```python
import io, json
import pandas as pd
from .models import SplitResult

def to_csv(result: SplitResult) -> bytes:
    rows = []
    for s in result.stories:
        rows.append({
            "Issue Key": s.id,
            "Summary": s.title,
            "Description": f"As a {s.as_a}, I want {s.i_want}, so that {s.so_that}",
            "Acceptance Criteria": "\n".join(
                f"Given {ac.given} When {ac.when} Then {ac.then}"
                for ac in s.acceptance_criteria
            ),
            "Story Points": {"XS":1, "S":2, "M":3, "L":5, "XL":8}[s.size.value],
            "Priority": s.priority.value,
            "Labels": ",".join(s.tags),
            "Depends On": ",".join(s.dependencies),
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")

def to_markdown(result: SplitResult) -> str:
    parts = [f"# Stories\n\n_{result.summary}_\n"]
    for s in result.stories:
        parts.append(f"## {s.id} — {s.title}")
        parts.append(f"- **Size**: {s.size.value} · **Priority**: {s.priority.value}")
        parts.append(f"- **Story**: As a {s.as_a}, I want {s.i_want}, so that {s.so_that}")
        parts.append("- **Acceptance Criteria**:")
        for ac in s.acceptance_criteria:
            parts.append(f"  - Given {ac.given} When {ac.when} Then {ac.then}")
        if s.dependencies:
            parts.append(f"- **Depends on**: {', '.join(s.dependencies)}")
        parts.append("")
    return "\n".join(parts)

def to_json(result: SplitResult) -> str:
    return result.model_dump_json(indent=2)
```

### `src/parser.py` 骨架
```python
from docx import Document

def parse_uploaded_file(uploaded) -> str:
    name = uploaded.name.lower()
    if name.endswith(".docx"):
        doc = Document(uploaded)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return uploaded.read().decode("utf-8", errors="ignore")
```

### `src/examples.py` 骨架
```python
EXAMPLES = {
    "E-commerce: Wishlist": """We want logged-in customers to save products to a wishlist
so they can come back later and easily move items to cart. Wishlists should be
private by default but shareable via link. Limit 100 items per wishlist.""",

    "Automotive: OTA update opt-in": """For Connected-Car users we need an opt-in flow for
over-the-air software updates. Driver must consent in-vehicle or via the mobile app.
Updates should only download on Wi-Fi by default and must be cancellable. Compliance
team requires audit logs of all consent changes.""",

    "Internal tool: Meeting recap": """Build an internal tool where any employee can
upload a meeting recording. The tool transcribes (zh/en), generates a summary,
extracts action items with owners and due dates, and emails the recap to attendees.
Recordings should be deleted after 30 days.""",
}
```

---

## 8. README.md 模板（简历用，照着填）

```markdown
# 🪓 Story Splitter

> Turn raw PRDs, customer emails, or meeting notes into Jira-ready user stories
> — backed by 10+ years of BA experience, codified as prompts.

**🌐 Live demo**: https://story-splitter.streamlit.app
**📹 30-sec walkthrough**: <loom link>

![hero](assets/screenshots/hero.png)

## Why
In agile teams, the gap between "the customer said X" and "developers can pick
up a story tomorrow" is where requirements rot. Story Splitter compresses that
gap by combining a senior-BA prompt with structured LLM output.

## Features
- Paste text or upload `.docx` / `.txt` / `.md`
- Context-aware splitting (team, tech stack, granularity)
- INVEST-aligned stories with Given/When/Then acceptance criteria
- T-shirt sizing + dependency graph + risk surfacing
- Export to Jira-compatible CSV, Markdown, or JSON
- Bilingual output (中 / EN / both)

## Architecture
[简短画一下：Streamlit → llm.py → Anthropic API → Pydantic 校验 → 渲染]

## Prompt-engineering notes
[这一节最稀缺。把你设计 prompt 时的取舍写出来：为什么强制 JSON、
为什么要 INVEST、为什么 XL 要标记 needs-split。这是 vibe coding 的灵魂。]

## Run locally
\`\`\`bash
git clone …
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY
streamlit run app.py
\`\`\`

## Roadmap
- [ ] Streaming output
- [ ] Per-story refine
- [ ] Jira API direct push

## Built with AI
This project was built with Cursor + Claude as a pair-programming partner.
Total human time: ~12 hours over 2 days. Notes on the workflow: <blog link>
```

---

## 9. 部署到 Streamlit Cloud（5 分钟）

1. 项目推到 GitHub（**public repo**，简历要展示）
2. 登 https://share.streamlit.io → New app → 选 repo → 选 `app.py`
3. Advanced settings → Secrets 里加：
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
4. Deploy。拿到 `https://<your-app>.streamlit.app` 链接
5. **重要**：在 GitHub repo 的 About 区贴上这个链接

---

## 10. Vibe Coding 实施步骤（按顺序，每步都让 Cursor 跑通再下一步）

> 把这份 SPEC.md 整个塞给 Cursor 当背景，然后按下面顺序逐步 prompt：

**Step 0**（环境）
- "用 uv 初始化项目 story-splitter，按 §6 创建目录结构，按 §7 生成 requirements.txt 和 .env.example"

**Step 1**（数据模型）
- "按 §4 实现 src/models.py，加上 pytest 单元测试覆盖正常/异常案例"

**Step 2**（LLM 客户端）
- "按 §5 和 §7 实现 src/llm.py 和 prompts/story_split.md，写一个 mock 测试不用真调 API"

**Step 3**（解析与导出）
- "按 §7 实现 src/parser.py 和 src/exporter.py，加测试"

**Step 4**（Streamlit UI）
- "按 §7 实现 app.py，先跑通最小可用版本：输入文本 → 调用 LLM → 展示结果"

**Step 5**（打磨）
- 加示例按钮、加历史记录、加导出按钮、加主题
- 用真实需求（你自己 Connected-Car 项目里随便挑一段，**脱敏**后）测一遍

**Step 6**（部署 + 文档）
- 推 GitHub → 部署 Streamlit Cloud → 写 README（§8）→ 截 3 张图 → 录 30s Loom

**Step 7**（简历素材整理）
- 把 demo URL / GitHub URL / Loom URL / 3 张截图存到一个地方
- 写一段 60 字的项目描述（中英各一版），准备好往简历里贴

---

## 11. 验收清单（你做完后自查）

- [ ] Repo 公开，README 有 demo 链接 + 截图
- [ ] Streamlit 在线 demo 可访问，且能成功跑完一次拆解（用 3 个示例都测过）
- [ ] CSV 下载后能直接 import 到 Jira（找个免费 Jira workspace 试一次）
- [ ] Loom 视频 30 秒以内，无废话，直接展示效果
- [ ] 至少有 3 个 commit，体现 vibe coding 的迭代过程（不要 squash 成 1 个）
- [ ] LICENSE 文件加上（MIT 即可）

---

## 12. 你做完后回来找我做什么

1. 把 demo URL、repo URL、Loom URL 发给我
2. 告诉我**实际花了多少小时** + 遇到的最大坑
3. 我帮你写：
   - 简历里这段项目的最终文案（中英各一版）
   - LinkedIn 帖子（如果你想公开发）
   - 1 篇短博客（可选，但发了能放进简历再加一分）

---

**Good luck. Now go vibe code. 🪓**
