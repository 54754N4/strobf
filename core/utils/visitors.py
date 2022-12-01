from __future__ import annotations

import random
from typing import Any, Dict, Tuple

from core.engine.Context import Context
from core.engine.TransformationChain import TransformationChain
from core.transformations.transforms import *
from core.transformations.transforms import Add, MulMod, MulModInv, Not, Permutation, RotateLeft, RotateRight, \
    Substract, Xor
from core.utils.StringBuilder import StringBuilder


#####################
# Convenience class #
#####################


####################
# Abstract Classes #
####################


class Visitor(ABC):

    def __init__(self):
        self.switcher = self.visit_switch()

    def visit(self, ctx: Context) -> StringBuilder:
        t = self.initialise(ctx)
        self.visit_chain(ctx.reverse, t)
        self.finalise(t)
        return t

    def visit_chain(self, chain: TransformationChain, sb: StringBuilder) -> None:
        for element in chain:
            self.visit_transform(element, sb)

    #T = TypeVar('T', bound=Transformation)

    def visit_switch(self) -> Dict[Transformation, Tuple[Transformation, StringBuilder, None]]:
        return {
            Add: self.visit_add,
            MulMod: self.visit_mul_mod,
            MulModInv: self.visit_mul_mod_inv,
            Not: self.visit_not,
            Permutation: self.visit_permutation,
            RotateLeft: self.visit_rotate_left,
            RotateRight: self.visit_rotate_right,
            Substract: self.visit_substract,
            Xor: self.visit_xor
        }

    def visit_transform(self, transformation: Transformation, sb: StringBuilder) -> None:
        try:
            self.switcher[transformation.__class__](transformation, sb)
        except KeyError:
            raise Exception("Unimplemented transformation double dispatch")

    @abstractmethod
    def initialise(self, ctx: Context) -> StringBuilder:
        raise NotImplementedError

    @abstractmethod
    def finalise(self, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        raise NotImplementedError

    @abstractmethod
    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        raise NotImplementedError


def generate_alphabet():
    with StringBuilder() as sb:
        sb.append("_")
        c, end = ord('a'), ord('z')
        while c <= end:
            sb.append(chr(c)).append(chr(c ^ 32))
            c += 1
        return sb.to_string()


class LanguageVisitor(Visitor, ABC):
    NAME_MIN = 4
    NAME_MAX = 10
    DEFAULT_ALPHABET = generate_alphabet()

    @staticmethod
    def generate_name(alphabet: str = ""):
        if alphabet == "":
            alphabet = LanguageVisitor.DEFAULT_ALPHABET
        size = random.randint(LanguageVisitor.NAME_MIN, LanguageVisitor.NAME_MAX)
        with StringBuilder() as sb:
            i = 0
            while i < size:
                sb.append(random.choice(alphabet))
                i += 1
            return sb.to_string()

    @staticmethod
    def hex(num: int) -> str:
        return "0x" + "{:x}".format(num)


################
# Bash Visitor #
################


class BashVisitor(LanguageVisitor):

    def __init__(self):
        super().__init__()
        self.variable_name = None
        self.variable = None
        self.temp_name = None
        self.i_name = None
        self.i = None
        self.result_name = None
        self.result = None
        self.has_permutations = None

    def ae(self, fmt: str, *args: Any) -> str:
        """
        Arithmetic expansion helper function.
        :param fmt: format string
        :param args: vararg params
        :return: formatted string as an arithmetic expansion
        """
        return ("((" + fmt + "))").format(*args)

    def initialise(self, ctx: Context) -> StringBuilder:
        self.variable_name = self.generate_name()
        self.variable = "$" + self.variable_name
        self.temp_name = self.generate_name()
        self.i_name = self.generate_name()
        self.i = "$" + self.i_name
        self.result_name = "string"
        self.result = "$" + self.result_name
        self.has_permutations = ctx.reverse.contains_permutation()
        # Write bytes in string
        sb = StringBuilder()
        sb.append(self.result_name + "=( ")
        for b in ctx.bytes:
            sb.append(self.hex(b) + " ")
        sb.append(")\n")
        # Write for loop
        sb.append("for {} in ${{!{}[@]}}; do\n".format(self.i_name, self.result_name))
        sb.append("\t" + self.variable_name + "=${" + self.result_name + "[" + self.i + "]}\n")
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        sb.append("\t{}[{}]={}\n".format(self.result_name, self.i, self.variable)) \
            .append("done\n") \
            .append("unset {}\n".format(self.i_name)) \
            .append("unset {}\n".format(self.variable_name))
        if self.has_permutations:
            sb.append("unset {}\n".format(self.temp_name))
        sb.append(self.result_name + "=$(printf %b \"$(printf '\\\\U%x' \"${" + self.result_name + "[@]}\")\")\n") \
            .append("echo " + self.result)

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        if add.value == 1:
            sb.append("\t" + self.ae("{}++", self.variable_name)).append("\n")
            return
        sb.append("\t") \
            .append(self.ae("{} += {}", self.variable_name, self.hex(add.value))) \
            .append("\n")

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        sb.append("\t") \
            .append(self.ae("{} = ({} * {}) % {}", self.variable_name, self.variable_name, self.hex(mm.value),
                            self.hex(mm.modulo))) \
            .append("\n")

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\t") \
            .append(self.ae("{} = ~{} & {}", self.variable_name, self.variable_name, self.hex(negation.mask))) \
            .append("\n")

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        sb.append("\t") \
            .append(self.ae("{} = (({} >> {}) ^ ({} >> {})) & ((1 << {})-1)",
                            self.temp_name,
                            self.variable_name,
                            self.hex(permutation.pos1),
                            self.variable_name,
                            self.hex(permutation.pos2),
                            self.hex(permutation.bits))) \
            .append("\n")
        sb.append("\t") \
            .append(
            self.ae("{} ^= ({} << {}) | ({} << {})", self.variable_name, self.temp_name, self.hex(permutation.pos1),
                    self.temp_name, self.hex(permutation.pos2))) \
            .append("\n")

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        mask = self.hex(rol.mask)
        sb.append("\t") \
            .append(self.ae("{} = ((({} & {}) >> {}) | ({} << {})) & {}",
                            self.variable_name,
                            self.variable_name,
                            self.mask,
                            self.hex(rol.lhs()),
                            self.variable_name,
                            self.hex(rol.rhs),
                            mask)) \
            .append("\n")

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        mask = self.hex(ror.mask)
        sb.append("\t") \
            .append(self.ae("{} = ((({} & {}) << {}) | ({} >> {})) & {}",
                            self.variable_name,
                            self.variable_name,
                            self.mask,
                            self.hex(ror.lhs()),
                            self.variable_name,
                            self.hex(ror.rhs()),
                            mask)) \
            .append("\n")

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        if sub.value == 1:
            sb.append("\t").append(self.ae("{}--", self.variable_name)).append("\n")
            return
        sb.append("\t") \
            .append(self.ae("{} -= {}", self.variable_name, self.hex(sub.value))) \
            .append("\n")

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\t") \
            .append(self.ae("{} ^= {}", self.variable_name, self.hex(xor.value))) \
            .append("\n")

