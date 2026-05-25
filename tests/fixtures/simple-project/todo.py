"""Todo list domain logic."""
from dataclasses import dataclass


@dataclass
class TodoItem:
    text: str
    done: bool = False


class TodoList:
    def __init__(self):
        self._items: list[TodoItem] = []

    def add(self, text: str) -> None:
        self._items.append(TodoItem(text=text))

    def complete(self, idx: int) -> None:
        if 0 <= idx < len(self._items):
            self._items[idx].done = True

    def all(self) -> list[TodoItem]:
        return list(self._items)
