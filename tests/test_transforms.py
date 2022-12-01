import unittest

from core.transforms import *


class MyTestCase(unittest.TestCase):
    def test_permutations(self) -> None:
        perm = Permutation(0, 3, 2, 16)
        reverse = perm.reversed()
        for x in range(30, 100):
            temp = perm.transform(x)
            temp = reverse.transform(temp)
            self.assertEqual(x, temp)

    def test_negation(self) -> None:
        negate = Not(32)
        reverse = negate.reversed()
        for x in range(1000):
            temp = negate.transform(x)
            temp = reverse.transform(temp)
            self.assertEqual(x, temp)

    def test_mul_mod(self) -> None:
        # Check mod inverse works
        self.assertEqual(4, Transformation.mod_inverse(3, 11))
        # Check mul mod reversibility
        mm = MulMod(3, 11, 16)
        mmi = mm.reversed()
        c = 5
        temp = mm.transform(c)
        temp = mmi.transform(temp)
        self.assertEqual(c, temp)

    def test_rotations(self) -> None:
        rl = RotateLeft(1, 16)
        rr = rl.reversed()
        v = 10
        temp = rl.transform(v)
        temp = rr.transform(temp)
        self.assertEqual(rl.lhs(), rr.lhs())
        self.assertEqual(rl.rhs(), rr.rhs())
        self.assertEqual(v, temp)


if __name__ == '__main__':
    unittest.main()
