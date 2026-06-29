"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from src.models import (
    AcceptanceCriterion,
    Priority,
    SplitResult,
    StorySize,
    UserStory,
)


def _ac(g: str, w: str, t: str) -> AcceptanceCriterion:
    return AcceptanceCriterion(given=g, when=w, then=t)


@pytest.fixture()
def sample_result() -> SplitResult:
    """A small, fully-populated SplitResult used by exporter tests."""
    story_a = UserStory(
        id="US-001",
        title="Save item to wishlist",
        as_a="logged-in customer",
        i_want="to save items to a wishlist",
        so_that="I can purchase them later",
        acceptance_criteria=[
            _ac("I am logged in", "I click Save", "the item is in my wishlist"),
            _ac("my wishlist has 100 items", "I click Save", "I see an error"),
        ],
        size=StorySize.M,
        priority=Priority.MUST,
        tags=["frontend", "api"],
    )
    story_b = UserStory(
        id="US-002",
        title="Share wishlist via link",
        as_a="logged-in customer",
        i_want="to share my wishlist via a link",
        so_that="friends can buy gifts for me",
        acceptance_criteria=[
            _ac("I have a wishlist", "I click Share", "I get a shareable URL"),
            _ac("the link is opened by anyone", "they visit", "they see read-only items"),
        ],
        size=StorySize.S,
        priority=Priority.SHOULD,
        dependencies=["US-001"],
        tags=["sharing"],
        notes="Need legal review of public sharing",
    )
    return SplitResult(
        summary="Wishlist MVP split into two stories.",
        stories=[story_a, story_b],
        suggested_epic_name="Wishlist",
        sprint_estimate=1,
        risks=["No notification flow defined"],
    )
