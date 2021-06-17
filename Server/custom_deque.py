"""
Custom datatype for graphing realtime data

Copyright © Vijay Sambamurthy 2021.
Rights given to HKUST Civil Engineering Department.
"""
import numpy as np


class GraphDeque:
    """
    A custom data type that follows a similar structure to a deque from collections module. However
    this works with a list and artificially creates the effect desired.
    """
    _raw: list
    _item_size: int

    def __init__(self, item_size: int, length: int):
        """
        This object is initialized with purely zeroes at the start.
        Args:
            item_size: Number of elements that will be dealt with each add or remove.
            length: The total number of "chunks" of elements that will be stored in a deque fashion.
        """
        self._raw = list(np.zeros(item_size * length))
        self._item_size = item_size

    def add(self, items: list[float]):
        """
        Add item to the object. This removes the first '_item_size' number of elements from the list
        after adding the new items into the list.
        Args:
            items: a list containing '_item_size' number of elements.
        """
        if len(items) != self._item_size:
            print(len(items))
            return
        self._raw += items
        self._raw = self._raw[self._item_size:]

    def convert_to_list(self) -> list[any]:
        """
        Simply return the list
        (Function was created due to a different implementation of this class)
        """
        return self._raw
