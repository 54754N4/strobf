from __future__ import annotations

from abc import ABC, abstractmethod

from core.transformations.Exceptions import ArithmeticException


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
