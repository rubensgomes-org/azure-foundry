"""Tests for azure_foundry.agent_functions.functions."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from azure_foundry.agent_functions import functions

MODULE = "azure_foundry.agent_functions.functions"
NEW_YEAR = datetime(2026, 1, 1, 9, 30)


@pytest.fixture(autouse=True)
def fixed_now(mocker: MockerFixture) -> None:
    mocker.patch(f"{MODULE}.datetime").now.return_value = NEW_YEAR


def test_next_visible_event_returns_first_upcoming_event() -> None:
    event = json.loads(functions.next_visible_event("North America"))

    assert event["event"] == "Quadrantids Meteor Shower"
    assert event["date"] == "01-03"
    assert "north_america" in event["visible_from"]


def test_next_visible_event_reports_unknown_location() -> None:
    result = json.loads(functions.next_visible_event("Atlantis"))

    assert result == {"message": "No upcoming events found for Atlantis."}


def test_calculate_observation_cost_applies_rate_and_multiplier() -> None:
    cost = json.loads(
        functions.calculate_observation_cost("Advanced", 2, "High")
    )

    assert cost["base_cost"] == 240.0
    assert cost["total_cost"] == 420.0


@pytest.mark.parametrize(
    ("tier", "hours", "priority", "error"),
    [
        ("huge", 1, "low", "Unknown telescope tier"),
        ("standard", 1, "someday", "Unknown priority"),
        ("standard", 0, "low", "Hours must be greater than zero."),
    ],
)
def test_calculate_observation_cost_rejects_invalid_input(
    tier: str, hours: float, priority: str, error: str
) -> None:
    result = json.loads(
        functions.calculate_observation_cost(tier, hours, priority)
    )

    assert error in result["error"]


def test_generate_observation_report_writes_report_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    result = json.loads(
        functions.generate_observation_report(
            "Lunar Eclipse", "europe", "standard", 2, "normal", "Ada"
        )
    )

    report = (tmp_path / result["file"]).read_text(encoding="utf-8")
    assert "Observer:       Ada" in report
    assert "Total Cost:   $125.00" in report


def test_generate_observation_report_returns_cost_error() -> None:
    result = json.loads(
        functions.generate_observation_report(
            "Lunar Eclipse", "europe", "huge", 2, "normal", "Ada"
        )
    )

    assert "Unknown telescope tier" in result["error"]
