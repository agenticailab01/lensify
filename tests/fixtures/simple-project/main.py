"""Simple to-do CLI — fixture for T1 tier testing."""
from todo import TodoList


def main():
    todos = TodoList()
    todos.add("Write tests")
    todos.add("Ship plugin")
    todos.complete(0)
    for item in todos.all():
        print(item)


if __name__ == "__main__":
    main()
