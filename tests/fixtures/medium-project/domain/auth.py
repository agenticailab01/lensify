"""Authentication logic."""
from domain.user import UserService


def authenticate(email, password):
    user = UserService().find_by_email(email)
    if not user:
        return None
    if check_password(password, user.password_hash):
        return issue_token(user)
    return None


def check_password(plain, hashed):
    return hashed == "hashed_" + plain  # demo only


def issue_token(user):
    return f"token-for-{user.email}"
