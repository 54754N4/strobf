import logging
import os
import subprocess
import unittest
import shutil

from core.engine import PolymorphicEngine
from core.visitors import *

# All these tests were made to be run ON Windows with the correct dependencies installed. e.g:
# Bash          -> WSL and a linux distro installed
# C/CPP         -> Visual Studio installed + ADMIN RIGHTS (to access VS installation folder)
# C#            -> .NET and Visual Studio installed
# Java          -> Java SDK installed and in PATH
# JS            -> Node.js installed and in PATH
# Masm64        -> Visual Studio installed + Windows Driver kit
# PowerShell    -> Windows or just powershell installed. Duh
# Python        -> Python in PATH

# Setup config

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(module)s %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

decryption_routines = 100        # How many routines to generate per test case/target


# Convenience methods


def run(args: str, verbose: bool = False) -> tuple[str, str]:
    if verbose:
        logger.info("Running: " + str(args))
    result = subprocess.run(args=args, capture_output=True, text=True, shell=True)
    return result.stdout.strip(), result.stderr.strip()  # trim trailing newlines


# Unit tests module

class BashEngineTest(unittest.TestCase):
    def test_bash_generation(self) -> None:
        logger.info("Starting bash code generation test..")
        # Check valid interpreter location
        shebang = "#!/bin/bash\n\n"
        out, err = run("bash --help")
        self.assertTrue(out.lower().startswith("gnu bash"))

        # Generate engine and bash target generator
        engine = PolymorphicEngine(10, 10, 16)
        visitor = BashVisitor()
        message = "Hello World!"

        # Test multiple decryption routines
        for i in range(decryption_routines):
            # Generate new code
            ctx = engine.transform(message)
            code = visitor.visit(ctx)

            # Run code and test
            filename = "main.sh"
            try:
                with open(filename, "w", newline='\n') as f:
                    f.write(shebang + code)
                windows_path = os.path.abspath(filename)
                out, err = run("wsl wslpath -a \"{}\"".format(windows_path))
                self.assertTrue(out.startswith("/mnt"))
                linux_path = out.strip()
                out, err = run("wsl \"{}\"".format(linux_path))
                self.assertEqual(message, out, code)
            finally:
                os.remove(filename)


class CEngineTest(unittest.TestCase):
    VS_VERSION = "14.34.31933"
    ENV_BUILD_VARS = "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Auxiliary\\Build\\vcvars64.bat"
    COMPILER_DIR = f"C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Tools\\MSVC\\{VS_VERSION}\\bin\\Hostx64\\x64"

    @staticmethod
    def create_main_file(imports: str, body: str) -> str:
        with StringBuilder() as sb:
            sb.append(imports + "\n\n")
            sb.append("int main(int argc, char**argv) {\n\t")
            sb.append(body.replace("\n", "\n\t"))
            sb.append("\n\treturn 0;\n}\n")
            return sb.to_string()

    def test_c_generation(self) -> None:
        logger.info("Starting c code generation test..")
        # Check valid compiler location
        out, err = run("\"{}\\cl.exe\"".format(self.COMPILER_DIR))
        self.assertTrue(out.lower().startswith("usage: cl"))

        # Create engine and C/C++ target generator
        engine = PolymorphicEngine(10, 10, 16)
        visitor = CVisitor()
        message = "Hello World!"

        # Test multiple decryption routines
        for i in range(decryption_routines):
            # Generate new code
            ctx = engine.transform(message)
            code = visitor.visit(ctx)

            # Compile and test code
            filename = "main"
            generated = self.create_main_file("#include <stdio.h>;", code)
            try:
                with open(filename + ".cpp", "w", newline='\n') as f:
                    f.write(generated)
                path = os.path.abspath(filename + ".cpp")
                run("call \"{}\" && \"{}\\cl\" \"{}\"".format(self.ENV_BUILD_VARS, self.COMPILER_DIR, path))
                out, err = run(".\\{}.exe".format(filename))
                self.assertEqual(message, out, code)
            finally:
                try:
                    if os.path.exists(filename + ".cpp"):
                        os.remove(filename + ".cpp")
                    if os.path.exists(filename + ".exe"):
                        os.remove(filename + ".exe")
                    if os.path.exists(filename + ".obj"):
                        os.remove(filename + ".obj")
                except PermissionError:
                    pass  # Ignore, next iteration will overwrite all


class CSharpEngineTest(unittest.TestCase):
    CSPROJ = "<Project Sdk=\"Microsoft.NET.Sdk\">\r\n\r\n" \
             + "  <PropertyGroup>\r\n" \
             + "    <OutputType>Exe</OutputType>\r\n" \
             + "    <TargetFramework>net6.0</TargetFramework>\r\n" \
             + "    <ImplicitUsings>enable</ImplicitUsings>\r\n" \
             + "    <Nullable>enable</Nullable>\r\n" \
             + "  </PropertyGroup>\r\n\r\n" \
             + "</Project>\r\n"

    def test_c_sharp_generation(self) -> None:
        logger.info("Starting c# code generation test..")
        # Check valid compiler location
        out, err = run("dotnet --info")
        self.assertTrue(out.lower().startswith(".net"))

        # Create engine and C# target generator
        engine = PolymorphicEngine(10, 10, 16)
        visitor = CSharpVisitor()
        message = "Hello World!"

        # Test multiple decryption routines
        for i in range(decryption_routines):
            # Generate new code
            ctx = engine.transform(message)
            code = visitor.visit(ctx)

            # Compile and test code
            filename = "build/CSharpTest"
            build_dir = "build"
            csproj = filename + ".csproj"
            cs = filename + ".cs"
            try:
                if not os.path.exists(build_dir):
                    os.mkdir(build_dir)
                with open(csproj, "w") as f:
                    f.write(self.CSPROJ)
                with open(cs, "w") as f:
                    f.write(code)
                out, err = run("dotnet run --project {}".format(csproj))
                self.assertEqual(message, out, code)
            finally:
                if os.path.exists(build_dir):
                    shutil.rmtree(build_dir)


class JavaEngineTest(unittest.TestCase):

    @staticmethod
    def create_test_class(class_name: str, body: str):
        with StringBuilder() as sb:
            sb.append("class " + class_name + " {\n")
            sb.append("\tpublic static void main(String[] args) {\n\t\t")
            sb.append(body.replace("\n", "\n\t\t"))
            sb.append("\n\t}\n")
            sb.append("}\n")
            return sb.to_string()

    def test_java_generation(self) -> None:
        logger.info("Starting java code generation test..")
        # Check valid compiler location
        out, err = run("java -version")
        self.assertTrue(err.lower().startswith("java version"))

        # Create engine and java target generator
        engine = PolymorphicEngine(10, 10, 16)
        visitor = JavaVisitor()
        message = "Hello World!"

        # Test multiple decryption routines
        for i in range(decryption_routines):
            # Generate new code
            ctx = engine.transform(message)
            code = visitor.visit(ctx)

            # Compile and run java code
            filename = "JavaTest"
            generated = self.create_test_class(filename, code)
            path = filename + ".java"
            try:
                with open(path, "w") as f:
                    f.write(generated)
                out, err = run("javac {}.java".format(filename))
                out, err = run("java {}".format(filename))
                self.assertEqual(message, out, code)
            finally:
                if os.path.exists(path):
                    os.remove(path)
                if os.path.exists(filename + ".class"):
                    os.remove(filename + ".class")


class JavaScriptEngineTest(unittest.TestCase):
    def test_js_generation(self):
        logger.info("Starting js code generation test..")
        # Check valid compiler location
        out, err = run("node --help")
        self.assertTrue(out.lower().startswith("usage:"))

        # Create engine and js target generator
        engine = PolymorphicEngine(10, 10, 16)
        visitor = JavaScriptVisitor()
        message = "Hello World!"

        # Test multiple decryption routines
        for i in range(decryption_routines):
            # Generate new code
            ctx = engine.transform(message)
            code = visitor.visit(ctx)

            # Generate and run JS code
            filename = "main.js"
            try:
                with open(filename, "w") as f:
                    f.write(code)
                out, err = run("node {}".format(filename))
                self.assertEqual(message, out, code)
            finally:
                if os.path.exists(filename):
                    os.remove(filename)


class Masm64EngineTest(unittest.TestCase):
    VS_VERSION = "14.34.31933"
    DRIVER_KIT_VERSION = "10.0.19041.0"
    ASSEMBLER = "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Tools\\MSVC\\" + VS_VERSION + "\\bin\\Hostx64\\x64\\ml64.exe"
    LINKER = "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Tools\\MSVC\\" + VS_VERSION + "\\bin\\Hostx64\\x64\\link.exe"
    LIB_PATH = "C:\\Program Files (x86)\\Windows Kits\\10\\Lib\\" + DRIVER_KIT_VERSION + "\\um\\x64"
    ASSEMBLE = "\"" + ASSEMBLER + "\" /c /nologo /Zi /Fo\"build\\main.obj\" /W3 /errorReport:prompt /Ta \"build\\main.asm\""
    LINK = "\"" + LINKER + "\" /SUBSYSTEM:CONSOLE \"build\\main.obj\" /DYNAMICBASE \"kernel32.lib\" \"user32.lib\" \"gdi32.lib\" \"winspool.lib\" \"comdlg32.lib\" \"advapi32.lib\" \"shell32.lib\" \"ole32.lib\" \"oleaut32.lib\" \"uuid.lib\" \"odbc32.lib\" \"odbccp32.lib\" " \
           + "/DEBUG /MACHINE:X64 /ENTRY:\"main\" /MANIFEST /NXCOMPAT /OUT:\"build\\main.exe\" /INCREMENTAL " \
           + "/LIBPATH:\"" + LIB_PATH + "\" /MANIFESTUAC:\"level='asInvoker' uiAccess='false'\" /ManifestFile:\"build\\main.exe.intermediate.manifest\" /ERRORREPORT:PROMPT /ILK:\"build\\main.ilk\" /NOLOGO /TLBID:1"

    def test_masm64_generation(self):
        logger.info("Starting masm64 code generation test..")
        # Check if assembler exists
        self.assertTrue(os.path.exists(self.ASSEMBLER), "masm assembler not found")

        # Create engine and masm target generator
        engine = PolymorphicEngine(10, 10, 16)
        visitor = Masm64Visitor()
        message = "Hello World!"

        # Test multiple decryption routines
        for i in range(decryption_routines):
            # Generate new code
            ctx = engine.transform(message)
            code = visitor.visit(ctx)

            # Generate, assemble, link and then run code to test
            asm = "build/main.asm"
            try:
                if not os.path.exists("build"):
                    os.mkdir("build")
                with open(asm, "w") as f:
                    f.write(code)
                run(self.ASSEMBLE)
                run(self.LINK)
                run(".\\build\\main.exe > output.txt")
                with open("output.txt", "r", encoding='utf-16-le') as f:
                    output = f.read()
                self.assertEqual(message, output, code)
            finally:
                if os.path.exists("build"):
                    shutil.rmtree("build")
                if os.path.exists("output.txt"):
                    os.remove("output.txt")


class PowerShellEngineTest(unittest.TestCase):
    def test_ps_generation(self):
        logger.info("Starting powershell code generation test..")
        # Check if running on windows
        self.assertEqual('nt', os.name, "This test case only runs on windows")

        # Create engine and powershell target generator
        engine = PolymorphicEngine(10, 10, 16)
        visitor = PowerShellVisitor()
        message = "Hello World!"

        # Test multiple decryption routines
        for i in range(decryption_routines):
            # Generate new code
            ctx = engine.transform(message)
            code = visitor.visit(ctx)

            # Run powershell code to test
            filename = "main.ps1"
            try:
                with open(filename, "w") as f:
                    f.write(code)
                path = os.path.abspath(filename)
                out, err = run("powershell -Command \"& '{}'\"".format(path))
                self.assertEqual(message, out, code)
            finally:
                if os.path.exists(filename):
                    os.remove(filename)


class PythonEngineTest(unittest.TestCase):
    def test_python_generation(self):
        logger.info("Starting python code generation test..")
        # Check compiler exists
        out, err = run("python --help")
        self.assertTrue(out.lower().startswith("usage:"))

        # Create engine and python target generator
        engine = PolymorphicEngine(10, 10, 16)
        visitor = PythonVisitor()
        message = "Hello World!"

        # Test multiple decryption routines
        for i in range(decryption_routines):
            # Generate new code
            ctx = engine.transform(message)
            code = visitor.visit(ctx)

            # Run python code to test
            filename = "main.py"
            try:
                with open(filename, "w") as f:
                    f.write(code)
                out, err = run("python {}".format(filename))
                self.assertEqual(message, out, code)
            finally:
                if os.path.exists(filename):
                    os.remove(filename)


if __name__ == '__main__':
    unittest.main()
