from core.transformations.transforms import Permutation
from core.transformations.Transformation import Transformation


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

