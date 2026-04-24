"""
Unit tests -- conversation memory module.
"""
import pytest
from sage.memory import conversation


def setup_function():
    """Clear all sessions before each test."""
    conversation._sessions.clear()


def test_get_history_empty():
    result = conversation.get_history("new_session")
    assert result == []


def test_save_and_retrieve_turn():
    conversation.save_turn("s1", "Hello Sage", "Good evening, sir.")
    history = conversation.get_history("s1")
    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Hello Sage"}
    assert history[1] == {"role": "assistant", "content": "Good evening, sir."}


def test_sessions_are_isolated():
    conversation.save_turn("s1", "Message A", "Response A")
    conversation.save_turn("s2", "Message B", "Response B")
    assert len(conversation.get_history("s1")) == 2
    assert len(conversation.get_history("s2")) == 2
    assert conversation.get_history("s1")[0]["content"] == "Message A"


def test_clear_session():
    conversation.save_turn("s1", "Hello", "Sir.")
    conversation.clear("s1")
    assert conversation.get_history("s1") == []


def test_clear_nonexistent_session_does_not_raise():
    conversation.clear("nonexistent")  # should not raise


def test_history_trimmed_at_max():
    max_msgs = conversation.MAX_HISTORY
    turns = max_msgs  # each turn = 2 messages
    for i in range(turns):
        conversation.save_turn("s1", f"user {i}", f"assistant {i}")
    history = conversation.get_history("s1")
    assert len(history) <= max_msgs
