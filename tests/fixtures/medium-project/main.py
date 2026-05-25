"""Entry point — medium project fixture."""
from api.routes import get_users, create_user, login


def main():
    print("Server starting...")
    print(get_users())


if __name__ == "__main__":
    main()
