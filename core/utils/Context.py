from typing import List

from core.transformations.TransformationChain import TransformationChain


class Context:
    def __init__(self, max_bits: int, bytes_in: List[int], mask: int,
                 forward: TransformationChain, reverse: TransformationChain):
        self.max_bits = max_bits
        self.bytes = bytes_in
        self.mask = mask
        self.forward = forward
        self.reverse = reverse
