from __future__ import annotations

import random
from typing import Any, Dict, TypeVar, Callable, Type

from core.engine import Context
from core.transforms import *
from core.transforms import Transformation, TransformationChain
from core.utils import StringBuilder


####################
# Abstract Classes #
####################


class Visitor(ABC):
    T = TypeVar('T', bound=Transformation)

    def __init__(self):
        self.switcher = self.visit_switch()

    def visit(self, ctx: Context) -> str:
        t = self.initialise(ctx)
        self.visit_chain(ctx.reverse, t)
        self.finalise(t)
        result = t.to_string()
        t.close()
        return result

    def visit_chain(self, chain: TransformationChain, sb: StringBuilder) -> None:
        for element in chain:
            self.visit_transform(element, sb)

    def visit_switch(self) -> Dict[Type[T], Callable[[T, StringBuilder], None]]:
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
        return "0x" + "{:04X}".format(num)


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
        Arithmetic expansion helper function
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
        sb.append(" ".join([self.hex(b) for b in ctx.bytes]))
        sb.append(" )\n")
        # Write for loop
        sb.append("for {} in ${{!{}[@]}}; do\n".format(self.i_name, self.result_name))
        sb.append("\t" + self.variable_name + "=${" + self.result_name + "[" + self.i + "]}\n")
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        sb.append("\t{}[{}]={}\n".format(self.result_name, self.i, self.variable))
        sb.append("done\n")
        sb.append("unset {}\n".format(self.i_name))
        sb.append("unset {}\n".format(self.variable_name))
        if self.has_permutations:
            sb.append("unset {}\n".format(self.temp_name))
        sb.append(self.result_name + "=$(printf %b \"$(printf '\\\\U%x' \"${" + self.result_name + "[@]}\")\")\n")
        sb.append("echo " + self.result)

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        if add.value == 1:
            sb.append("\t" + self.ae("{}++", self.variable_name)).append("\n")
            return
        sb.append("\t")
        sb.append(self.ae("{} += {}", self.variable_name, self.hex(add.value)))
        sb.append("\n")

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        sb.append("\t")
        sb.append(self.ae("{} = ({} * {}) % {}", self.variable_name, self.variable_name, self.hex(mm.value),
                          self.hex(mm.modulo)))
        sb.append("\n")

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\t")
        sb.append(self.ae("{} = ~{} & {}", self.variable_name, self.variable_name, self.hex(negation.mask)))
        sb.append("\n")

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        sb.append("\t")
        sb.append(self.ae("{} = (({} >> {}) ^ ({} >> {})) & ((1 << {})-1)",
                          self.temp_name,
                          self.variable_name, self.hex(permutation.pos1),
                          self.variable_name, self.hex(permutation.pos2),
                          self.hex(permutation.bits)))
        sb.append("\n")
        sb.append("\t")
        sb.append(
            self.ae("{} ^= ({} << {}) | ({} << {})",
                    self.variable_name,
                    self.temp_name, self.hex(permutation.pos1),
                    self.temp_name, self.hex(permutation.pos2)))
        sb.append("\n")

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        mask = self.hex(rol.mask)
        sb.append("\t")
        sb.append(self.ae("{} = ((({} & {}) >> {}) | ({} << {})) & {}",
                          self.variable_name,
                          self.variable_name, mask,
                          self.hex(rol.lhs()),
                          self.variable_name, self.hex(rol.rhs()),
                          mask))
        sb.append("\n")

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        mask = self.hex(ror.mask)
        sb.append("\t")
        sb.append(self.ae("{} = ((({} & {}) << {}) | ({} >> {})) & {}",
                          self.variable_name,
                          self.variable_name, mask,
                          self.hex(ror.lhs()),
                          self.variable_name, self.hex(ror.rhs()),
                          mask))
        sb.append("\n")

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        if sub.value == 1:
            sb.append("\t").append(self.ae("{}--", self.variable_name)).append("\n")
            return
        sb.append("\t")
        sb.append(self.ae("{} -= {}", self.variable_name, self.hex(sub.value)))
        sb.append("\n")

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\t")
        sb.append(self.ae("{} ^= {}", self.variable_name, self.hex(xor.value)))
        sb.append("\n")


##############
# C# Visitor #
##############


class CSharpVisitor(LanguageVisitor):

    def __init__(self):
        super().__init__()
        self.variable = None
        self.temp = None
        self.i = None
        self.result = None

    def initialise(self, ctx: Context) -> StringBuilder:
        # Generate var names
        self.variable = self.generate_name()
        self.temp = self.generate_name()
        self.i = self.generate_name()
        self.result = "str"
        # Write bytes in string
        sb = StringBuilder()
        sb.append("var " + self.result + " = new System.Text.StringBuilder(\"")
        sb.append("".join(["\\u" + "{:04x}".format(b) for b in ctx.bytes]))
        sb.append("\");\n")
        # Write for loop
        permutation = ""
        if ctx.reverse.contains_permutation():
            permutation = ", " + self.temp
        sb.append("for (int {}=0, {}{}; {} < {}.Length; {}++) {{\n".format(self.i, self.variable, permutation, self.i,
                                                                           self.result, self.i))
        sb.append("\t" + self.variable + " = " + self.result + "[" + self.i + "];\n")
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        sb.append("\t{}[{}] = (char) {};\n".format(self.result, self.i, self.variable))
        sb.append("}\n")
        sb.append("Console.WriteLine(" + self.result + ");")

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        if add.value == 1:
            sb.append("\t").append(self.variable).append("++;\n")
            return
        sb.append("\t" + self.variable + " += " + self.hex(add.value) + ";\n")

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = ")
        sb.append("(" + self.variable + " * " + self.hex(mm.value) + ") % " + self.hex(mm.modulo))
        sb.append(";\n")

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = ~" + self.variable + " & " + self.hex(negation.mask) + ";\n")

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        sb.append("\t" + self.temp + " = ")
        sb.append("((" + self.variable + " >> " + self.hex(permutation.pos1) + ")")
        sb.append(" ^ (" + self.variable + " >> " + self.hex(permutation.pos2) + ")) & ((1 << ")
        sb.append(self.hex(permutation.bits) + ") - 1);\n")
        sb.append("\t" + self.variable + " ^= ")
        sb.append("(" + self.temp + " << " + self.hex(permutation.pos1) + ") | (" + self.temp + " << ")
        sb.append(self.hex(permutation.pos2) + ");\n")

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        mask = self.hex(rol.mask)
        sb.append("\t" + self.variable + " = ")
        sb.append("(((" + self.variable + " & " + mask + ") >> " + self.hex(rol.lhs()) + ") | (")
        sb.append(self.variable + " << " + self.hex(rol.rhs()) + ")) & " + mask + ";\n")

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        mask = self.hex(ror.mask)
        sb.append("\t" + self.variable + " = ")
        sb.append("(((" + self.variable + " & " + mask + ") << " + self.hex(ror.lhs()) + ") | (")
        sb.append(self.variable + " >> " + self.hex(ror.rhs()) + ")) & " + mask + ";\n")

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        if sub.value == 1:
            sb.append("\t" + self.variable + "--;\n")
            return
        sb.append("\t" + self.variable + " -= " + self.hex(sub.value) + ";\n")

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " ^= " + self.hex(xor.value) + ";\n")


#############
# C Visitor #
#############


class CVisitor(LanguageVisitor):

    def __init__(self):
        super().__init__()
        self.variable = None
        self.temp = None
        self.i = None
        self.result = None

    def initialise(self, ctx: Context) -> StringBuilder:
        # Generate variable names
        self.variable = self.generate_name()
        self.temp = self.generate_name()
        self.i = self.generate_name()
        self.result = "string"
        # Write bytes in string
        sb = StringBuilder()
        sb.append("wchar_t " + self.result + "[" + str(len(ctx.bytes)) + "] = {")
        sb.append(",".join([self.hex(b) for b in ctx.bytes]))
        sb.append("};\n")
        # Write for loop
        permutation = ""
        if ctx.reverse.contains_permutation():
            permutation = ", " + self.temp
        sb.append("for (unsigned int {}=0, {}{}; {} < {}; {}++) {{\n".format(self.i, self.variable, permutation, self.i,
                                                                             len(ctx.bytes), self.i))
        sb.append("\t" + self.variable + " = " + self.result + "[" + self.i + "];\n")
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        sb.append("\t{}[{}] = {};\n".format(self.result, self.i, self.variable))
        sb.append("}\n")
        sb.append("wprintf(" + self.result + ");")

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        if add.value == 1:
            sb.append("\t" + self.variable + "++;\n")
            return
        sb.append("\t" + self.variable + " += " + self.hex(add.value) + ";\n")

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = ")
        sb.append("(" + self.variable + " * " + self.hex(mm.value) + ") % " + self.hex(mm.modulo) + ";\n")

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = ~" + self.variable + " & " + self.hex(negation.mask) + ";\n")

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        sb.append("\t" + self.temp + " = ")
        sb.append("((" + self.variable + " >> " + self.hex(permutation.pos1) + ")")
        sb.append(" ^ (" + self.variable + " >> " + self.hex(permutation.pos2) + ")) & ((1 << ")
        sb.append(self.hex(permutation.bits) + ") - 1);\n")
        sb.append("\t" + self.variable + " ^= ")
        sb.append("(" + self.temp + " << " + self.hex(permutation.pos1) + ") | (" + self.temp + " << ")
        sb.append(self.hex(permutation.pos2) + ");\n")

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        mask = self.hex(rol.mask)
        sb.append("\t" + self.variable + " = ")
        sb.append("(((" + self.variable + " & " + mask + ") >> " + self.hex(rol.lhs()) + ") | (")
        sb.append(self.variable + " << " + self.hex(rol.rhs()) + ")) & " + mask + ";\n")

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        mask = self.hex(ror.mask)
        sb.append("\t" + self.variable + " = ")
        sb.append("(((" + self.variable + " & " + mask + ") << " + self.hex(ror.lhs()) + ") | (")
        sb.append(self.variable + " >> " + self.hex(ror.rhs()) + ")) & " + mask + ";\n")

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        if sub.value == 1:
            sb.append("\t" + self.variable + "--;\n")
            return
        sb.append("\t" + self.variable + " -= " + self.hex(sub.value) + ";\n")

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " ^= " + self.hex(xor.value) + ";\n")


##############
# JS Visitor #
##############


class JavaScriptVisitor(LanguageVisitor):

    def __init__(self):
        super().__init__()
        self.variable = None
        self.temp = None
        self.i = None
        self.result = None

    def initialise(self, ctx: Context) -> StringBuilder:
        # Generate variables
        self.variable = self.generate_name()
        self.temp = self.generate_name()
        self.i = self.generate_name()
        self.result = "string"
        # Write bytes string
        sb = StringBuilder()
        sb.append("var " + self.result + " = [")
        sb.append(",".join([self.hex(b) for b in ctx.bytes]))
        sb.append("];\n")
        # Write for loop
        permutation = ""
        if ctx.reverse.contains_permutation():
            permutation = ", " + self.temp
        sb.append("for (var {}=0, {}{}; {} < {}.length; {}++) {{\n".format(self.i, self.variable, permutation, self.i,
                                                                           self.result, self.i))
        sb.append("\t" + self.variable + " = " + self.result + "[" + self.i + "];\n")
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        sb.append("\t{}[{}] = {};\n".format(self.result, self.i, self.variable))
        sb.append("}\n" + self.result + " = String.fromCodePoint(..." + self.result + ");\n")
        sb.append("console.log(" + self.result + ");\n")

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        if add.value == 1:
            sb.append("\t" + self.variable + "++;\n")
            return
        sb.append("\t" + self.variable + " += " + self.hex(add.value) + ";\n")

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = ")
        sb.append("(" + self.variable + " * " + self.hex(mm.value) + ") % " + self.hex(mm.modulo) + ";\n")

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = ~" + self.variable + " & " + self.hex(negation.mask) + ";\n")

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        sb.append("\t" + self.temp + " = ")
        sb.append("((" + self.variable + " >> " + self.hex(permutation.pos1) + ") ^ (")
        sb.append(self.variable + " >> " + self.hex(permutation.pos2) + ")) & ((1 << " + self.hex(permutation.bits))
        sb.append(") - 1);\n")
        sb.append("\t" + self.variable + " ^= (" + self.temp + " << " + self.hex(permutation.pos1) + ") | (")
        sb.append(self.temp + " << " + self.hex(permutation.pos2) + ");\n")

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        mask = self.hex(rol.mask)
        sb.append("\t" + self.variable + " = (((" + self.variable + " & " + mask + ") >> " + self.hex(rol.lhs()))
        sb.append(") | (" + self.variable + " << " + self.hex(rol.rhs()) + ")) & " + mask + ";\n")

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        mask = self.hex(ror.mask)
        sb.append("\t" + self.variable + " = (((" + self.variable + " & " + mask + ") << " + self.hex(ror.lhs()))
        sb.append(") | (" + self.variable + " >> " + self.hex(ror.rhs()) + ")) & " + mask + ";\n")

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        if sub.value == 1:
            sb.append("\t" + self.variable + "--;\n")
            return
        sb.append("\t" + self.variable + " -= " + self.hex(sub.value) + ";\n")

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " ^= " + self.hex(xor.value) + ";\n")


################
# Java Visitor #
################


class JavaVisitor(LanguageVisitor):

    def __init__(self):
        super().__init__()
        self.variable = None
        self.temp = None
        self.i = None
        self.result = None

    def initialise(self, ctx: Context) -> StringBuilder:
        # Generate variable names
        self.variable = self.generate_name()
        self.temp = self.generate_name()
        self.i = self.generate_name()
        self.result = "string"
        # Write bytes in string
        sb = StringBuilder()
        sb.append("StringBuilder " + self.result + " = new StringBuilder(\"")
        sb.append("".join(["\\u{:04x}".format(b) for b in ctx.bytes]))
        sb.append("\");\n")
        # Write for loop
        permutation = ""
        if ctx.reverse.contains_permutation():
            permutation = ", " + self.temp
        sb.append("for (int {}=0, {}{}; {} < {}.length(); {}++) {{\n".format(self.i, self.variable, permutation, self.i,
                                                                             self.result, self.i))
        sb.append("\t" + self.variable + " = " + self.result + ".charAt(" + self.i + ");\n")
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        sb.append("\t{}.setCharAt({}, (char) {});\n".format(self.result, self.i, self.variable))
        sb.append("}\nSystem.out.println(" + self.result + ");")

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        if add.value == 1:
            sb.append("\t" + self.variable + "++;\n")
            return
        sb.append("\t" + self.variable + " += " + self.hex(add.value) + ";\n")

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = (" + self.variable + " * " + self.hex(mm.value) + ") % ")
        sb.append(self.hex(mm.modulo) + ";\n")

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = ~" + self.variable + " & " + self.hex(negation.mask) + ";\n")

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        sb.append("\t" + self.temp + " = ((" + self.variable + " >> " + self.hex(permutation.pos1))
        sb.append(") ^ (" + self.variable + " >> " + self.hex(permutation.pos2) + ")) & ((1 << ")
        sb.append(self.hex(permutation.bits) + ") - 1);\n")
        sb.append("\t" + self.variable + " ^= (" + self.temp + " << " + self.hex(permutation.pos1))
        sb.append(") | (" + self.temp + " << " + self.hex(permutation.pos2) + ");\n")

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        mask = self.hex(rol.mask)
        sb.append("\t" + self.variable + " = (((" + self.variable + " & " + mask + ") >> " + self.hex(rol.lhs()))
        sb.append(") | (" + self.variable + " << " + self.hex(rol.rhs()) + ")) & " + mask + ";\n")

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        mask = self.hex(ror.mask)
        sb.append("\t" + self.variable + " = (((" + self.variable + " & " + mask + ") << " + self.hex(ror.lhs()))
        sb.append(") | (" + self.variable + " >> " + self.hex(ror.rhs()) + ")) & " + mask + ";\n")

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        if sub.value == 1:
            sb.append("\t" + self.variable + "--;\n")
            return
        sb.append("\t" + self.variable + " -= " + self.hex(sub.value) + ";\n")

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " ^= " + self.hex(xor.value) + ";\n")


##################
# MASM64 Visitor #
##################


class Masm64Visitor(LanguageVisitor):
    # Static variables related to masm
    IMMEDIATE_SIZES = [2, 4, 8, 16]
    DATA_TYPES = ["db", "dw", "dd", "dq"]
    DATA_TYPES_PTR = ["byte", "word", "dword", "qword"]
    REGISTERS = [
        ["al", "ax", "eax", "rax"],
        ["bl", "bx", "ebx", "rbx"],
        ["cl", "cx", "ecx", "rcx"],
        ["dl", "dx", "edx", "rdx"],
        ["dil", "di", "edi", "rdi"],
        ["sil", "si", "esi", "rsi"],
        ["bpl", "bp", "ebp", "rbp"],
        ["spl", "sp", "esp", "rsp"],
        ["r8l", "r8w", "r8d", "r8"],
        ["r9l", "r9w", "r9d", "r9"],
        ["r10l", "r10w", "r10d", "r10"],
        ["r11l", "r11w", "r11d", "r11"],
        ["r12l", "r12w", "r12d", "r12"],
        ["r13l", "r13w", "r13d", "r13"],
        ["r14l", "r14w", "r14d", "r14"],
        ["r15l", "r15w", "r15d", "r15"],
    ]

    RAX = 0
    RBX = 1
    RCX = 2
    RDX = 3
    RDI = 4
    RSI = 5
    RBP = 6
    RSP = 7
    R8 = 8
    R9 = 9
    R10 = 10
    R11 = 11
    R12 = 12
    R13 = 13
    R14 = 14
    R15 = 15

    def __init__(self):
        super().__init__()
        self.block = None
        self.size = None
        self.shadow_space = None
        self.increment = None
        self.result = None
        self.loop_name = None
        self.i = None
        self.variable = None

    # Convenience methods

    def reg(self, id: int) -> str:
        return self.REGISTERS[id][self.block]

    def hex(self, l: int) -> str:
        return ("0{:0" + str(self.IMMEDIATE_SIZES[self.block]) + "x}h").format(l)

    # Visitor methods

    # RBX = data array address
    # RCX = i loop counter
    # RDX = data variable for transformations
    def initialise(self, ctx: Context) -> StringBuilder:
        # Calculate correct data sizes and registers
        self.block = (ctx.max_bits - 1) // 8
        self.increment = self.IMMEDIATE_SIZES[self.block] // 2
        self.result = "string"
        self.loop_name = self.generate_name()
        self.shadow_space = 32
        self.i = self.reg(self.RCX)
        self.variable = self.reg(self.RDX)
        self.size = len(ctx.bytes)
        sb = StringBuilder()
        # Write imports
        sb.append("extern GetStdHandle: proc\n"
                  + "extern WriteFile: proc\n"
                  + "extern GetFileType: proc\n"
                  + "extern WriteConsoleW: proc\n\n")
        # Write bytes in data section
        sb.append(".data?\n"
                  + "\tstdout\tdq ?\n"
                  + "\twritten\tdq ?\n")
        sb.append(".data\n")
        sb.append("\t" + self.result + " " + self.DATA_TYPES[self.block] + " ")
        sb.append(",".join([self.hex(b) for b in ctx.bytes]))
        sb.append("\n\tlen\tequ $-" + self.result + "\n")
        # Write code section and prolog
        sb.append(".code\n")
        sb.append("main proc\n")
        sb.append("\tpush\trbp\n")
        sb.append("\tmov\trbp, rsp\n")
        sb.append("\tsub\trsp, {}\n".format(self.shadow_space))
        sb.append("\tand\trsp, -10h\n\n")
        # Loop initialisation
        sb.append("\tmov\trbx, offset {}\n".format(self.result))
        sb.append("\txor\trcx, rcx\n")
        sb.append(self.loop_name + ":\n")
        sb.append("\txor\trax, rax\n"
                  + "\txor\trdx, rdx\n"
                  + "\txor\tr8, r8\n"
                  + "\txor\tr9, r9\n"
                  + "\txor\tr10, r10\n")
        sb.append(
            "\tmov\t{}, {} ptr [rbx + rcx*{}]\n".format(self.variable, self.DATA_TYPES_PTR[self.block], self.increment))
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        # End of loop
        sb.append(
            "\tmov\t{} ptr [rbx + rcx*{}], {}\n".format(self.DATA_TYPES_PTR[self.block], self.increment, self.variable))
        sb.append("\tinc\t{}\n".format(self.i))
        sb.append("\tcmp\t{}, {}\n".format(self.i, self.size))
        sb.append("\tjne\t{}\n\n".format(self.loop_name))
        # Print output accordingly
        sb.append("\t; Printing code\n"
                  + "\txor\trax, rax\n"
                  + "\txor\trcx, rcx\n"
                  + "\txor\trdx, rdx\n"
                  + "\txor\tr8, r8\n"
                  + "\txor\tr9, r9\n"
                  + "\tmov\trcx, -11\n"
                  + "\tcall\tGetStdHandle\n"
                  + "\tmov\t[stdout], rax\n"
                  + "\tmov\trcx, rax\n"
                  + "\tcall\tGetFileType\n"
                  + "\tcmp\trax, 1\n"
                  + "\tje\tfileWrite\n"
                  + "\tmov\trcx, [stdout]\n"
                  + "\tmov\trdx, rbx\n"
                  + "\tmov\tr8, len\n"
                  + "\tmov\tr9, written\n"
                  + "\tcall\tWriteConsoleW\n"
                  + "\tjmp\tepilog\n"
                  + "fileWrite:\n"
                  + "\tmov\trcx, [stdout]\n"
                  + "\tmov\trdx, rbx\n"
                  + "\tmov\tr8, len\n"
                  + "\tmov\tr9, written\n"
                  + "\tcall\tWriteFile\n"
                  + "epilog:\n"
                  + "\tadd\trsp, " + str(self.shadow_space) + "\n"
                  + "\tmov\trsp, rbp\n"
                  + "\tpop\trbp\n"
                  + "\tret\n"
                  + "main endp\n"
                  + "end")

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        sb.append("\tadd\t{}, {}\n".format(self.variable, add.value))

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        rax, rdx, r8 = self.reg(self.RAX), self.reg(self.RDX), self.reg(self.R8)
        # Multiplication
        sb.append("\tmov\t{}, {}\n".format(rax, rdx))
        sb.append("\txor\t{}, {}\n".format(rdx, rdx))
        sb.append("\tmov\t{}, {}\n".format(r8, mm.value))
        sb.append("\tmul\t{}\n".format(r8))
        sb.append("\tmov\t{}, {}\n".format(rdx, rax))
        # Remainder
        sb.append("\tmov\t{}, {}\n".format(rax, rdx))
        sb.append("\txor\t{}, {}\n".format(rdx, rdx))
        sb.append("\tmov\t{}, {}\n".format(r8, mm.modulo))
        sb.append("\tdiv\t{}\n".format(r8))
        sb.append("\tmov\t{}, {}\n".format(rdx, rax))

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\tnot\t{}\n".format(self.variable))

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        r8, r9, r10 = self.reg(self.R8), self.reg(self.R9), self.reg(self.R10)
        sb.append("\tmov\t{}, {}\n".format(r8, self.variable))
        sb.append("\tshr\t{}, {}\n".format(r8, permutation.pos1))
        sb.append("\tmov\t{}, {}\n".format(r9, self.variable))
        sb.append("\tshr\t{}, {}\n".format(r9, permutation.pos2))
        sb.append("\txor\t{}, {}\n".format(r8, r9))
        sb.append("\tmov\t{}, {}\n".format(r9, 1))
        sb.append("\tshl\t{}, {}\n".format(r9, permutation.bits))
        sb.append("\tsub\t{}, {}\n".format(r9, 1))
        sb.append("\tand\t{}, {}\n".format(r8, r9))
        sb.append("\tmov\t{}, {}\n".format(r9, r8))
        sb.append("\tshl\t{}, {}\n".format(r9, permutation.pos1))
        sb.append("\tmov\t{}, {}\n".format(r10, r8))
        sb.append("\tshl\t{}, {}\n".format(r10, permutation.pos2))
        sb.append("\tor\t{}, {}\n".format(r9, r10))
        sb.append("\txor\t{}, {}\n".format(self.variable, r9))

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        sb.append("\trol\t{}, {}\n".format(self.variable, rol.value))

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        sb.append("\tror\t{}, {}\n".format(self.variable, ror.value))

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        sb.append("\tsub\t{}, {}\n".format(self.variable, sub.value))

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\txor\t{}, {}\n".format(self.variable, xor.value))

######################
# PowerShell Visitor #
######################


class PowerShellVisitor(LanguageVisitor):

    def __init__(self):
        super().__init__()
        self.variable = None
        self.temp = None
        self.i = None
        self.array = None
        self.result = None
        self.mask = None
        self.has_permutation = None

    def initialise(self, ctx: Context) -> StringBuilder:
        # Generate variable names
        self.variable = "$" + self.generate_name()
        self.temp = "$" + self.generate_name()
        self.i = "$" + self.generate_name()
        self.array = "$" + self.generate_name()
        self.result = "$string"
        self.mask = self.hex(ctx.mask)
        self.has_permutation = ctx.reverse.contains_permutation()
        # Write bytes in string
        sb = StringBuilder()
        sb.append("[uint64[]]" + self.array + " = ")
        sb.append(",".join([self.hex(b) for b in ctx.bytes]))
        sb.append("\n" + self.result + " = [System.Text.StringBuilder]::new()\n")
        # Write for loop
        sb.append("for ({} = 0; {} -lt {}.Length; {}++) {{\n".format(self.i, self.i, self.array, self.i))
        sb.append("\t" + self.variable + " = " + self.array + "[" + self.i + "]\n")
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        delete_format = "{0} = [void]{0}\n"
        sb.append("\t[void]{}.Append([char]({} -band {}))\n".format(self.result, self.variable, self.mask))
        sb.append("}\n")
        sb.append(delete_format.format(self.variable))
        sb.append(delete_format.format(self.i))
        sb.append(delete_format.format(self.array))
        if self.has_permutation:
            sb.append(delete_format.format(self.temp))
        sb.append("{} = {}.ToString()\n".format(self.result, self.result))
        sb.append("Write-Host " + self.result)

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        if add.value == 1:
            sb.append("\t" + self.variable + "++\n")
            return
        sb.append("\t" + self.variable + " += " + self.hex(add.value) + "\n")

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = (" + self.variable + " * " + self.hex(mm.value) + ") % ")
        sb.append(self.hex(mm.modulo) + "\n")

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = -bnot " + self.variable + " -band " + self.hex(negation.mask) + "\n")

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        sb.append("\t" + self.temp + " = ((" + self.variable + " -shr " + self.hex(permutation.pos1) + " ) -bxor (")
        sb.append(self.variable + " -shr " + self.hex(permutation.pos2) + ")) -band ((1 -shl ")
        sb.append(self.hex(permutation.bits) + ") - 1)\n")
        sb.append("\t" + self.variable + " = " + self.variable + " -bxor ((" + self.temp + " -shl ")
        sb.append(self.hex(permutation.pos1) + ") -bor (" + self.temp + " -shl " + self.hex(permutation.pos2) + "))\n")

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        mask = self.hex(rol.mask)
        sb.append("\t" + self.variable + " = (((" + self.variable + " -band " + mask + ") -shr " + self.hex(rol.lhs()))
        sb.append(") -bor (" + self.variable + " -shl " + self.hex(rol.rhs()) + ")) -band " + mask + "\n")

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        mask = self.hex(ror.mask)
        sb.append("\t" + self.variable + " = (((" + self.variable + " -band " + mask + ") -shl " + self.hex(ror.lhs()))
        sb.append(") -bor (" + self.variable + " -shr " + self.hex(ror.rhs()) + ")) -band " + mask + "\n")

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        if sub.value == 1:
            sb.append("\t" + self.variable + "--\n")
            return
        sb.append("\t" + self.variable + " -= " + self.hex(sub.value) + "\n")

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = " + self.variable + " -bxor " + self.hex(xor.value) + "\n")

##################
# Python Visitor #
##################


class PythonVisitor(LanguageVisitor):

    def __init__(self):
        super().__init__()
        self.variable = None
        self.temp = None
        self.i = None
        self.result = None
        self.mask = None
        self.has_permutation = None

    def initialise(self, ctx: Context) -> StringBuilder:
        # Generate var names
        self.variable = self.generate_name()
        self.temp = self.generate_name()
        self.i = self.generate_name()
        self.mask = self.hex(ctx.mask)
        self.result = "string"
        self.has_permutation = ctx.reverse.contains_permutation()
        # Write bytes in string
        sb = StringBuilder()
        sb.append(self.result + " = [")
        sb.append(",".join([self.hex(b) for b in ctx.bytes]))
        sb.append("]\n")
        # Write for loop
        sb.append("for {} in range(len({})):\n".format(self.i, self.result))
        sb.append("\t" + self.variable + " = " + self.result + "[" + self.i + "]\n")
        return sb

    def finalise(self, sb: StringBuilder) -> None:
        sb.append("\t{}[{}] = chr({} & {})\n".format(self.result, self.i, self.variable, self.mask))
        if self.has_permutation:
            sb.append("del {}, {}, {}\n".format(self.i, self.variable, self.temp))
        else:
            sb.append("del {}, {}\n".format(self.i, self.variable))
        sb.append("{} = ''.join({})\n".format(self.result, self.result))
        sb.append("print(" + self.result + ")")

    def visit_add(self, add: Add, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " += " + self.hex(add.value) + "\n")

    def visit_mul_mod(self, mm: MulMod, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = (" + self.variable + " * " + self.hex(mm.value) + ") % ")
        sb.append(self.hex(mm.modulo) + "\n")

    def visit_mul_mod_inv(self, mmi: MulModInv, sb: StringBuilder) -> None:
        self.visit_mul_mod(mmi, sb)

    def visit_not(self, negation: Not, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " = ~" + self.variable + " & " + self.hex(negation.mask) + "\n")

    def visit_permutation(self, permutation: Permutation, sb: StringBuilder) -> None:
        sb.append("\t" + self.temp + " = ((" + self.variable + " >> " + self.hex(permutation.pos1) + ") ^ (")
        sb.append(self.variable + " >> " + self.hex(permutation.pos2) + ")) & ((1 << " + self.hex(permutation.bits))
        sb.append(") - 1)\n")
        sb.append("\t" + self.variable + " ^= (" + self.temp + " << " + self.hex(permutation.pos1) + ") | (")
        sb.append(self.temp + " << " + self.hex(permutation.pos2) + ")\n")

    def visit_rotate_left(self, rol: RotateLeft, sb: StringBuilder) -> None:
        mask = self.hex(rol.mask)
        sb.append("\t" + self.variable + " = (((" + self.variable + " & " + mask + ") >> " + self.hex(rol.lhs()))
        sb.append(") | (" + self.variable + " << " + self.hex(rol.rhs()) + ")) & " + mask + "\n")

    def visit_rotate_right(self, ror: RotateRight, sb: StringBuilder) -> None:
        mask = self.hex(ror.mask)
        sb.append("\t" + self.variable + " = (((" + self.variable + " & " + mask + ") << " + self.hex(ror.lhs()))
        sb.append(") | (" + self.variable + " >> " + self.hex(ror.rhs()) + ")) & " + mask + "\n")

    def visit_substract(self, sub: Substract, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " -= " + self.hex(sub.value) + "\n")

    def visit_xor(self, xor: Xor, sb: StringBuilder) -> None:
        sb.append("\t" + self.variable + " ^= " + self.hex(xor.value) + "\n")
