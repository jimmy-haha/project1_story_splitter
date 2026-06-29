"""Tests for the Pydantic models in src.models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import (
    AcceptanceCriterion,
    Priority,
    SplitResult,
    StorySize,
    UserStory,
)


def _make_ac(suffix: str = "") -> AcceptanceCriterion:
    return AcceptanceCriterion(
        given=f"a logged-in user{suffix}",
        when=f"they click submit{suffix}",
        then=f"the form is saved{suffix}",
    )


def _make_story(**overrides) -> UserStory:
    defaults = dict(
        id="US-001",
        title="Save wishlist item",
        as_a="logged-in customer",
        i_want="to save items to a wishlist",
        so_that="I can buy them later",
        acceptance_criteria=[_make_ac("-a"), _make_ac("-b")],
        size=StorySize.M,
        priority=Priority.MUST,
    )
    defaults.update(overrides)
    return UserStory(**defaults)


class TestUserStory:
    def test_valid_story(self):
        story = _make_story()
        assert story.id == "US-001"
        assert story.size is StorySize.M
        assert story.priority is Priority.MUST
        assert len(story.acceptance_criteria) == 2
        assert story.dependencies == []
        assert story.tags == []
        assert story.notes is None

    def test_requires_at_least_two_acceptance_criteria(self):
        with pytest.raises(ValidationError):
            _make_story(acceptance_criteria=[_make_ac()])

    def test_rejects_invalid_size(self):
        with pytest.raises(ValidationError):
            _make_story(size="HUGE")

    def test_rejects_invalid_priority(self):
        with pytest.raises(ValidationError):
            _make_story(priority="Maybe")

    def test_dependencies_and_tags_accepted(self):
        story = _make_story(
            dependencies=["US-000"],
            tags=["frontend", "api"],
            notes="Needs UX review",
        )
        assert story.dependencies == ["US-000"]
        assert "frontend" in story.tags
        assert story.notes == "Needs UX review"


class TestSplitResult:
    def test_valid_result_round_trips_through_json(self):
        result = SplitResult(
            summary="Split into 1 story.",
            stories=[_make_story()],
            suggested_epic_name="Wishlist",
            sprint_estimate=1,
            risks=["No login flow defined"],
        )
        roundtripped = SplitResult.model_validate_json(result.model_dump_json())
        assert roundtripped == result

    def test_requires_at_least_one_story(self):
        with pytest.raises(ValidationError):
            SplitResult(summary="Empty", stories=[])

    def test_sprint_estimate_must_be_non_negative(self):
        with pytest.raises(ValidationError):
            SplitResult(
                summary="bad",
                stories=[_make_story()],
                sprint_estimate=-1,
            )

    def test_json_schema_is_generated(self):
        schema = SplitResult.model_json_schema()
        assert schema["type"] == "object"
        assert "stories" in schema["properties"]
