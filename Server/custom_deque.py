from collections import deque
import numpy as np

class Graph_Deque:
    _raw: list
    _item_size: int

    def __init__(self, item_size, length):
        self._raw = list(np.zeros(item_size * length))
        self._item_size = item_size

    def add(self, items: list[float]):
        if len(items) != self._item_size:
            print(len(items))
            return
        self._raw += items
        self._raw = self._raw[self._item_size:]

    def convert_to_list(self):
        return self._raw
