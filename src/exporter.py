"""Export a SplitResult to the three formats the user can download:

  - Jira-import-compatible CSV
  - Human-readable Markdown
  - Round-trippable JSON
"""

from __future__ import annotations

import pandas as pd

from .models import SplitResult

# Map T-shirt sizes to Fibonacci-ish story points (Jira-friendly).
SIZE_TO_POINTS: dict[str, int] = {"XS": 1, "S": 2, "M": 3, "L": 5, "XL": 8}


def to_csv(result: SplitResult) -> bytes:
    """Return CSV bytes compatible with Jira's CSV importer.

    Column names mirror the defaults the Jira import wizard recognises so
    users can map them in one click.
    """
    rows = []
    for s in result.stories:
        rows.append(
            {
                "Issue Key": s.id,
                "Summary": s.title,
                "Issue Type": "Story",
                "Description": (
                    f"As a {s.as_a}, I want {s.i_want}, so that {s.so_that}"
                ),
                "Acceptance Criteria": "\n".join(
                    f"Given {ac.given} When {ac.when} Then {ac.then}"
                    for ac in s.acceptance_criteria
                ),
                "Story Points": SIZE_TO_POINTS[s.size.value],
                "Priority": s.priority.value,
                "Labels": ",".join(s.tags),
                "Depends On": ",".join(s.dependencies),
                "Notes": s.notes or "",
            }
        )
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def to_markdown(result: SplitResult) -> str:
    """Return a Markdown document suitable for pasting into a doc or PR."""
    lines: list[str] = []
    lines.append("# Stories")
    lines.append("")
    lines.append(f"_{result.summary}_")
    lines.append("")

    if result.suggested_epic_name:
        lines.append(f"**Suggested epic**: {result.suggested_epic_name}")
    if result.sprint_estimate is not None:
        lines.append(f"**Sprint estimate**: {result.sprint_estimate}")
    if result.risks:
        lines.append("")
        lines.append("**Risks / open questions**:")
        for r in result.risks:
            lines.append(f"- {r}")
    lines.append("")

    for s in result.stories:
        lines.append(f"## {s.id} — {s.title}")
        lines.append(f"- **Size**: {s.size.value} · **Priority**: {s.priority.value}")
        lines.append(
            f"- **Story**: As a {s.as_a}, I want {s.i_want}, so that {s.so_that}"
        )
        lines.append("- **Acceptance Criteria**:")
        for ac in s.acceptance_criteria:
            lines.append(
                f"  - Given {ac.given} When {ac.when} Then {ac.then}"
            )
        if s.dependencies:
            lines.append(f"- **Depends on**: {', '.join(s.dependencies)}")
        if s.tags:
            lines.append(f"- **Tags**: {', '.join(s.tags)}")
        if s.notes:
            lines.append(f"- **Notes**: {s.notes}")
        lines.append("")
    return "\n".join(lines)


def to_json(result: SplitResult) -> str:
    """Return a pretty-printed JSON dump (round-trippable into SplitResult)."""
    return result.model_dump_json(indent=2)
