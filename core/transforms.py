from __future__ import annotations
from abc import ABC, abstractmethod

from core.utils import ArithmeticException


####################
# Abstract Classes #
####################


class Transformation(ABC):
    def __init__(self, bits: int):
        self.max_bits = bits
        self.mask = (1 << bits) - 1

    def max(self) -> int:
        return 1 << self.max_bits

    @abstractmethod
    def transform(self, i: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def reversed(self) -> Transformation:
        raise NotImplementedError

    @staticmethod
    def gcd(a: int, b: int) -> int:
        if a == 0:
            return b
        if b == 0:
            return a
        n = 0
        while ((a | b) & 1) == 0:
            a >>= 1
            b >>= 1
            n += 1
        while (a & 1) == 0:
            a >>= 1
        while True:
            while (b & 1) == 0:
                b >>= 1
            if a > b:
                temp = a
                a = b
                b = temp
            b = b - a
            if b == 0:
                break
        return a << n

    @staticmethod
    def mod_inverse(a: int, m: int) -> int:
        if a % m == 0:
            raise ArithmeticException("Mod inverse can't be calculated when a/m")
        if Transformation.gcd(a, m) != 1:
            raise ArithmeticException("Mod inverse exists only if a and m are coprime")
        m0, y, x = m, 0, 1
        if m == 1:
            return 0
        while a > 1:
            q, t = a // m, m
            m = a % m
            a = t
            t = y
            y = x - q * y
            x = t
        if x < 0:
            x += m0
        return x


class TransformationChain:
    def __init__(self, *args: Transformation):
        self.transforms = args

    def apply(self, t: int) -> int:
        c = t
        for transformation in self.transforms:
            c = transformation.transform(c)
        return c

    def reverse(self) -> 'TransformationChain':
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

    def __iter__(self) -> 'TransformationChain':
        self.pos = 0
        return self

    def __next__(self) -> Transformation:
        if self.pos >= len(self.transforms):
            raise StopIteration
        transform = self.transforms[self.pos]
        self.pos += 1
        return transform


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
