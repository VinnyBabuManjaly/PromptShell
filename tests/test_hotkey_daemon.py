"""Tests for hotkey leading-edge trigger logic.

These tests exercise the combo detection logic in isolation without a live
keyboard listener. The logic under test is the `prev_pressed` / `pressed`
leading-edge check extracted into a helper so it can be unit-tested.
"""

from __future__ import annotations

from prompt_shell.main import _combo_just_completed


class TestComboJustCompleted:
    """_combo_just_completed(combo, prev, current) returns True only on the rising edge."""

    def test_fires_when_last_key_completes_combo(self):
        combo = frozenset(["ctrl", "alt", "e"])
        prev = frozenset(["ctrl", "alt"])  # one key short
        current = frozenset(["ctrl", "alt", "e"])  # now complete
        assert _combo_just_completed(combo, prev, current) is True

    def test_does_not_fire_on_autorepeated_key(self):
        """Combo was already satisfied before this key event — no re-trigger."""
        combo = frozenset(["ctrl", "alt", "e"])
        prev = frozenset(["ctrl", "alt", "e"])  # already complete
        current = frozenset(["ctrl", "alt", "e"])  # same (auto-repeat of 'e')
        assert _combo_just_completed(combo, prev, current) is False

    def test_does_not_fire_when_unrelated_key_added_while_held(self):
        """Extra key pressed while combo is held must not re-trigger."""
        combo = frozenset(["ctrl", "alt", "e"])
        prev = frozenset(["ctrl", "alt", "e"])  # already complete
        current = frozenset(["ctrl", "alt", "e", "x"])  # extra key added
        assert _combo_just_completed(combo, prev, current) is False

    def test_does_not_fire_when_combo_not_yet_satisfied(self):
        combo = frozenset(["ctrl", "alt", "e"])
        prev = frozenset(["ctrl"])
        current = frozenset(["ctrl", "alt"])  # still missing 'e'
        assert _combo_just_completed(combo, prev, current) is False

    def test_fires_for_single_key_combo(self):
        combo = frozenset(["escape"])
        prev = frozenset()
        current = frozenset(["escape"])
        assert _combo_just_completed(combo, prev, current) is True

    def test_does_not_fire_for_single_key_combo_on_repeat(self):
        combo = frozenset(["escape"])
        prev = frozenset(["escape"])
        current = frozenset(["escape"])
        assert _combo_just_completed(combo, prev, current) is False
