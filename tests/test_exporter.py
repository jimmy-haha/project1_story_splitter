"""Tests for src.exporter."""

from __future__ import annotations

import csv
import io
import json

from src.exporter import SIZE_TO_POINTS, to_csv, to_json, to_markdown
from src.models import SplitResult


class TestToCSV:
    def test_returns_bytes_with_header(self, sample_result):
        out = to_csv(sample_result)
        assert isinstance(out, bytes)
        text = out.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        assert len(rows) == 2
        assert {"Issue Key", "Summary", "Story Points", "Priority"}.issubset(
            reader.fieldnames or []
        )

    def test_story_points_mapped_correctly(self, sample_result):
        text = to_csv(sample_result).decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))
        assert int(rows[0]["Story Points"]) == SIZE_TO_POINTS["M"]
        assert int(rows[1]["Story Points"]) == SIZE_TO_POINTS["S"]

    def test_acceptance_criteria_joined(self, sample_result):
        text = to_csv(sample_result).decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))
        assert "Given" in rows[0]["Acceptance Criteria"]
        assert "When" in rows[0]["Acceptance Criteria"]
        assert "Then" in rows[0]["Acceptance Criteria"]

    def test_dependencies_serialised(self, sample_result):
        text = to_csv(sample_result).decode("utf-8")
        rows = list(csv.DictReader(io.StringIO(text)))
        assert rows[1]["Depends On"] == "US-001"


class TestToMarkdown:
    def test_contains_all_story_ids(self, sample_result):
        md = to_markdown(sample_result)
        assert "US-001" in md
        assert "US-002" in md

    def test_includes_summary_and_risks(self, sample_result):
        md = to_markdown(sample_result)
        assert sample_result.summary in md
        assert "Risks" in md
        assert "No notification flow defined" in md

    def test_includes_dependencies_when_present(self, sample_result):
        md = to_markdown(sample_result)
        assert "Depends on" in md
        assert "US-001" in md


class TestToJSON:
    def test_round_trips(self, sample_result):
        out = to_json(sample_result)
        loaded = json.loads(out)
        assert loaded["stories"][0]["id"] == "US-001"
        # Should be parseable back into the model
        rebuilt = SplitResult.model_validate_json(out)
        assert rebuilt == sample_result

    def test_pretty_printed(self, sample_result):
        out = to_json(sample_result)
        assert "\n" in out
        assert "  " in out  # indented
