"""Tests for user domain."""
from domain.user import UserService


def test_user_service_list():
    assert UserService().list_all() == []
