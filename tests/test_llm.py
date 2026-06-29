"""Tests for src.llm — fully mocked, no real API calls."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from src import llm
from src.models import SplitResult


VALID_RESPONSE = {
    "summary": "Split into 1 story for wishlist.",
    "stories": [
        {
            "id": "US-001",
            "title": "Save item to wishlist",
            "as_a": "logged-in customer",
            "i_want": "to save items to a wishlist",
            "so_that": "I can purchase them later",
            "acceptance_criteria": [
                {
                    "given": "I am logged in",
                    "when": "I click 'Save'",
                    "then": "the item appears in my wishlist",
                },
                {
                    "given": "my wishlist has 100 items",
                    "when": "I try to save another",
                    "then": "I see an error message",
                },
            ],
            "size": "M",
            "priority": "Must Have",
            "dependencies": [],
            "tags": ["frontend", "api"],
            "notes": None,
        }
    ],
    "suggested_epic_name": "Wishlist",
    "sprint_estimate": 1,
    "risks": ["No sharing logic specified"],
}


class TestBuildPrompt:
    def test_substitutes_all_placeholders(self):
        template = (
            "lang={language} team={team_context} tech={tech_stack} "
            "gran={granularity} req={raw_requirement} schema={json_schema}"
        )
        out = llm.build_prompt(
            raw="hello",
            language="English",
            team_context="acme",
            tech_stack="python",
            granularity="Sprint-ready",
            template=template,
        )
        assert "lang=English" in out
        assert "team=acme" in out
        assert "tech=python" in out
        assert "gran=Sprint-ready" in out
        assert "req=hello" in out
        assert '"stories"' in out  # schema embedded

    def test_empty_context_gets_defaults(self):
        template = "team={team_context} tech={tech_stack}"
        out = llm.build_prompt(
            raw="x",
            language="English",
            team_context="",
            tech_stack="",
            granularity="Auto",
            template=template,
        )
        assert "general SaaS team" in out
        assert "modern web stack" in out


class TestStripFences:
    def test_no_fences_unchanged(self):
        assert llm._strip_fences('{"a": 1}') == '{"a": 1}'

    def test_plain_fences_removed(self):
        text = "```\n{\"a\": 1}\n```"
        assert llm._strip_fences(text) == '{"a": 1}'

    def test_json_tagged_fences_removed(self):
        text = "```json\n{\"a\": 1}\n```"
        assert llm._strip_fences(text) == '{"a": 1}'


class TestSplitRequirement:
    def test_happy_path_returns_split_result(self):
        with patch.object(llm, "_call_llm", return_value=json.dumps(VALID_RESPONSE)):
            result = llm.split_requirement(raw="Build a wishlist")
        assert isinstance(result, SplitResult)
        assert len(result.stories) == 1
        assert result.stories[0].id == "US-001"
        assert result.sprint_estimate == 1

    def test_handles_fenced_response(self):
        fenced = f"```json\n{json.dumps(VALID_RESPONSE)}\n```"
        with patch.object(llm, "_call_llm", return_value=fenced):
            result = llm.split_requirement(raw="Build a wishlist")
        assert len(result.stories) == 1

    def test_retries_then_succeeds(self):
        responses = ["not json", "still not json", json.dumps(VALID_RESPONSE)]
        with patch.object(llm, "_call_llm", side_effect=responses) as mocked:
            result = llm.split_requirement(raw="x", max_retries=2)
        assert mocked.call_count == 3
        assert isinstance(result, SplitResult)

    def test_raises_after_exhausting_retries(self):
        with patch.object(llm, "_call_llm", return_value="garbage"):
            with pytest.raises(RuntimeError, match="failed validation"):
                llm.split_requirement(raw="x", max_retries=1)

    def test_passes_model_name_through(self):
        """The model name from the UI should reach the API call unchanged."""
        fake_choice = type(
            "Choice",
            (),
            {"message": type("Msg", (), {"content": json.dumps(VALID_RESPONSE)})()},
        )()
        fake_resp = type("Resp", (), {"choices": [fake_choice]})()
        with patch.object(llm, "_get_client") as mock_client:
            mock_client.return_value.chat.completions.create.return_value = fake_resp
            llm.split_requirement(raw="x", model="deepseek-reasoner")
            kwargs = mock_client.return_value.chat.completions.create.call_args.kwargs
            assert kwargs["model"] == "deepseek-reasoner"
            assert kwargs["response_format"] == {"type": "json_object"}
