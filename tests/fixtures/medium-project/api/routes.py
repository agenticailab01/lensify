"""HTTP route handlers."""
from domain.user import UserService
from domain.auth import authenticate


def get_users():
    """GET /users — list users."""
    return UserService().list_all()


def create_user(payload):
    """POST /users — create a user."""
    return UserService().create(payload)


def login(payload):
    """POST /login — issue a token."""
    return authenticate(payload["email"], payload["password"])
