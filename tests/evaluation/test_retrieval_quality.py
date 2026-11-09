
from pathlib import Path

import pytest


SOP_PATH = Path(
    "data/sample/industrial_sop/pump_maintenance_sop.txt"
)


@pytest.fixture(scope="module")
def sop_text():

    assert SOP_PATH.exists(), (
        f"Sample SOP not found: {SOP_PATH}"
    )

    return SOP_PATH.read_text(encoding="utf-8").lower()


def test_sop_contains_temperature_threshold(sop_text):

    assert "75" in sop_text
    assert "temperature" in sop_text


def test_sop_contains_vibration_threshold(sop_text):

    assert "4.5" in sop_text
    assert "vibration" in sop_text


def test_sop_contains_maintenance_interval(sop_text):

    assert "500" in sop_text
    assert "hours" in sop_text


def test_sop_contains_lubrication_information(sop_text):

    assert "lubrication" in sop_text
    assert "week" in sop_text


def test_sop_contains_safety_instructions(sop_text):
    assert "lockout" in sop_text or "loto" in sop_text
    assert (
        "ppe" in sop_text
        or "personal protective equipment" in sop_text
    )


def test_sop_is_not_empty(sop_text):

    assert len(sop_text.strip()) > 100
