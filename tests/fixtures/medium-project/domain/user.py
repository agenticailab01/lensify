"""User domain logic."""
from db.models import UserModel


class UserService:
    def list_all(self):
        return UserModel.all()

    def create(self, payload):
        return UserModel.create(**payload)

    def find_by_email(self, email):
        return UserModel.where(email=email).first()
