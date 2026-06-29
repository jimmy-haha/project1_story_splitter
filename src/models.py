"""Pydantic models that define the structured output of the story splitter.

These models double as:
  - the contract the LLM must satisfy (via JSON schema in the prompt)
  - the validation layer that catches malformed LLM output
  - the input to the renderer / exporter
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class StorySize(str, Enum):
    """T-shirt sizing for relative estimation."""

    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


class Priority(str, Enum):
    """MoSCoW prioritisation."""

    MUST = "Must Have"
    SHOULD = "Should Have"
    COULD = "Could Have"
    WONT = "Won't Have"


class AcceptanceCriterion(BaseModel):
    """A single Given/When/Then acceptance criterion."""

    given: str = Field(description="Given clause — preconditions / context")
    when: str = Field(description="When clause — the triggering action")
    then: str = Field(description="Then clause — the expected outcome")


class UserStory(BaseModel):
    """A single Jira-ready user story."""

    id: str = Field(description="Auto-generated, e.g. US-001")
    title: str = Field(
        description="Short, action-oriented, ideally < 80 chars",
        max_length=200,
    )
    as_a: str = Field(description="The persona / role")
    i_want: str = Field(description="The capability / action")
    so_that: str = Field(description="The business value / outcome")
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=2)
    size: StorySize
    priority: Priority
    dependencies: list[str] = Field(
        default_factory=list,
        description="Other story IDs this depends on (e.g. ['US-001'])",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Free-form labels, e.g. ['frontend', 'api', 'cross-team']",
    )
    notes: str | None = Field(
        default=None,
        description="Open questions, assumptions, or split-needed flag for XL",
    )


class SplitResult(BaseModel):
    """The full result of a single split run."""

    summary: str = Field(description="2-3 sentence summary of what was split")
    stories: list[UserStory] = Field(min_length=1)
    suggested_epic_name: str | None = None
    sprint_estimate: int | None = Field(
        default=None,
        ge=0,
        description="Rough number of sprints needed",
    )
    risks: list[str] = Field(default_factory=list)
