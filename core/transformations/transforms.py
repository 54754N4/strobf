from __future__ import annotations
from abc import ABC

from core.utils.Exceptions import ArithmeticException
from core.transformations.Transformation import Transformation


####################
# Abstract Classes #
####################


class Modulus(Transformation, ABC):
    def __init__(self, value: int, modulo: int, max_bits: int):
        super().__init__(max_bits)
        self.value = value
        self.modulo = modulo


class Rotation(Transformation, ABC):
    def __init__(self, value: int, max_bits: int):
        super().__init__(max_bits)
        self.value = value

    def lhs(self) -> int:
        return self.max_bits - self.value

    def rhs(self) -> int:
        return self.value


##########################
# Implementation Classes #
##########################


class Add(Transformation):
    def __init__(self, value: int, max_bits: int):
        super().__init__(max_bits)
        self.value = value

    def transform(self, i: int) -> int:
        if i > self.max() - self.value:
            raise ArithmeticException("Additive overflow")
        return i + self.value

    def reversed(self) -> Transformation:
        return Substract(self.value, self.max_bits)


class MulMod(Modulus):
    def __init__(self, value: int, modulo: int, max_bits: int):
        super().__init__(value, modulo, max_bits)

    def transform(self, i: int) -> int:
        if i != (i * self.value) // self.value or i * self.value >= self.max():
            raise ArithmeticException("Multiplicative overflow")
        return (i * self.value) % self.modulo

    def reversed(self) -> Transformation:
        return MulModInv(self.value, self.modulo, self.max_bits)


class MulModInv(MulMod):
    def __init__(self, value: int, modulo: int, max_bits: int):
        super().__init__(Transformation.mod_inverse(value, modulo), modulo, max_bits)
        self.initial = value

    def reversed(self) -> Transformation:
        return MulMod(self.initial, self.modulo, self.max_bits)


class Not(Transformation):
    def __init__(self, max_bits: int):
        super().__init__(max_bits)

    def transform(self, i: int) -> int:
        return ~i & ((1 << self.max_bits) - 1)

    def reversed(self) -> Transformation:
        return self


class Permutation(Transformation):
    def __init__(self, pos1: int, pos2: int, bits: int, max_bits: int):
        super().__init__(max_bits)
        self.pos1 = pos1
        self.pos2 = pos2
        self.bits = bits
        if max(pos1, pos2) + bits > max_bits:
            raise ArithmeticException("Invalid ranges")

    def transform(self, i: int) -> int:
        xor = ((i >> self.pos1) ^ (i >> self.pos2)) & ((1 << self.bits) - 1)
        return i ^ ((xor << self.pos1) | (xor << self.pos2))

    def reversed(self) -> Transformation:
        return self


class RotateLeft(Rotation):
    def __init__(self, value: int, max_bits: int):
        super().__init__(value, max_bits)

    def transform(self, i: int) -> int:
        return (((i & self.mask) >> self.lhs()) | (i << self.rhs())) & self.mask

    def reversed(self) -> Transformation:
        return RotateRight(self.value, self.max_bits)


class RotateRight(Rotation):
    def __init__(self, value: int, max_bits: int):
        super().__init__(value, max_bits)

    def transform(self, i: int) -> int:
        return (((i & self.mask) << self.lhs()) | (i >> self.rhs())) & self.mask

    def reversed(self) -> Transformation:
        return RotateLeft(self.value, self.max_bits)


class Substract(Transformation):
    def __init__(self, value: int, max_bits: int):
        super().__init__(max_bits)
        self.value = value

    def transform(self, i: int) -> int:
        if i < self.value:
            raise ArithmeticException("Substraction underflow")
        return i - self.value

    def reversed(self) -> Transformation:
        return Add(self.value, self.max_bits)


class Xor(Transformation):
    def __init__(self, value: int, max_bits: int):
        super().__init__(max_bits)
        self.value = value

    def transform(self, i: int) -> int:
        return i ^ self.value

    def reversed(self) -> Transformation:
        return self
