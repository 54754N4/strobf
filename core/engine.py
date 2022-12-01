from __future__ import annotations
from typing import List, Dict, Callable, Tuple
from random import randint
from core.transforms import *
import os


class TransformationChain:
    def __init__(self, *args: Transformation):
        self.transforms = args

    def apply(self, t: int) -> int:
        c = t
        for transformation in self.transforms:
            c = transformation.transform(c)
        return c

    def reverse(self) -> TransformationChain:
        transformations = []
        i = len(self.transforms) - 1
        while i >= 0:
            transformations.append(self.transforms[i].reversed())
            i -= 1
        return TransformationChain(*transformations)

    def contains(self, cls) -> bool:
        for transformation in self.transforms:
            if isinstance(transformation, cls):
                return True
        return False

    def contains_permutation(self) -> bool:
        return self.contains(Permutation)

    # Iterator methods

    def __iter__(self) -> TransformationChain:
        self.pos = 0
        return self

    def __next__(self) -> Transformation:
        if self.pos >= len(self.transforms):
            raise StopIteration
        transform = self.transforms[self.pos]
        self.pos += 1
        return transform


class Context:
    def __init__(self, max_bits: int, bytes_in: List[int], mask: int, forward: TransformationChain, reverse: TransformationChain):
        self.max_bits = max_bits
        self.bytes = bytes_in
        self.mask = mask
        self.forward = forward
        self.reverse = reverse


class PolymorphicEngine:
    def __init__(self, min_ops: int, max_ops: int, max_bits: int):
        self.max_bits = max_bits
        self.min_ops = min_ops
        self.max_ops = max_ops
        self.MASK = (1 << max_bits) - 1
        self.MULTIPLICATIVE_LIMIT = 1 << (max_bits // 2)
        self.ADDITIVE_LIMIT = 1 << (max_bits - 2)
        self.SWITCH = self.switcher()

    class Retry(Exception):
        pass

    def transform(self, text: str) -> Context:
        if os.path.exists(text):
            file = open(text, "r")
            text = file.read()
            file.close()
        buffer = [0 for _ in range(len(text))]
        buffer_len = len(buffer)
        while True:
            try:
                forward = self.generate_forward()
                reverse = forward.reverse()
                pos = 0
                while pos < buffer_len:
                    try:
                        c = ord(text[pos])
                        buffer[pos] = forward.apply(c)
                        # Dynamic check in case of implicit overflows
                        check = reverse.apply(buffer[pos])
                        if chr(check) != chr(c):
                            raise PolymorphicEngine.Retry
                    except ArithmeticException:
                        raise PolymorphicEngine.Retry
                    # Valid range sanity check
                    if buffer[pos] < 0 or buffer[pos] >= self.max():
                        raise PolymorphicEngine.Retry
                    pos += 1
            except PolymorphicEngine.Retry:
                continue
            # If no exceptions raised (e.g. sanity checks passed)
            break
        return Context(self.max_bits, buffer, self.MASK, forward, reverse)

    def generate_forward(self) -> TransformationChain:
        forward = []
        for i in range(randint(self.min_ops, self.max_ops)):
            forward.append(self.generate_transformation())
        return TransformationChain(*forward)

    def generate_transformation(self) -> Transformation:
        return self.SWITCH[randint(0, 8)]()

    def switcher(self) -> Dict[int, Callable[[], Transformation]]:
        return {
            0: self.addition,
            1: self.mul_mod,
            2: self.mul_mod_inv,
            3: self.negation,
            4: self.permutation,
            5: self.rotate_left,
            6: self.rotate_right,
            7: self.substraction,
            8: self.xor
        }

    def addition(self) -> Transformation:
        return Add(self.next_long(self.ADDITIVE_LIMIT), self.max_bits)

    def negation(self) -> Transformation:
        return Not(self.max_bits)

    def rotate_left(self) -> Transformation:
        return RotateLeft(self.next_long(self.max_bits - 1) + 1, self.max_bits)

    def rotate_right(self) -> Transformation:
        return RotateRight(self.next_long(self.max_bits - 1) + 1, self.max_bits)

    def substraction(self) -> Transformation:
        return Substract(self.next_long(self.ADDITIVE_LIMIT), self.max_bits)

    def xor(self) -> Transformation:
        return Xor(self.random_max(), self.max_bits)

    def permutation(self) -> Transformation:
        while True:
            pos1 = self.next_long(self.max_bits)
            pos2 = self.next_long(self.max_bits)
            bits = self.next_long(self.max_bits - 2) + 2
            if (pos1 + bits) < self.max_bits and (pos2 + bits) < self.max_bits:
                break
        return Permutation(pos1, pos2, bits, self.max_bits)

    def mul_mod(self) -> Transformation:
        while True:
            mm = MulMod(self.random_max(), 1 << self.max_bits, self.max_bits)
            if mm.value == 1:
                continue
            try:
                mmi = mm.reversed()
                if mmi.value > self.MULTIPLICATIVE_LIMIT:
                    continue
            except ArithmeticException:     # no inverse mod
                continue
            break
        return mm

    def mul_mod_inv(self) -> Transformation:
        while True:
            try:
                mmi = MulModInv(self.random_max(), 1 << self.max_bits, self.max_bits)
                if mmi.value == 1:
                    continue
            except ArithmeticException:      # no inverse mod
                continue
            mm = mmi.reversed()
            if mm.value > self.MULTIPLICATIVE_LIMIT:
                continue
            break
        return mmi

    @staticmethod
    def next_long(bound: int) -> int:
        return randint(0, bound - 1)

    def max(self) -> int:
        return 1 << self.max_bits

    def random_max(self) -> int:
        return self.next_long(self.max())

