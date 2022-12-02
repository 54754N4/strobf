from core.engine.PolymorphicEngine import PolymorphicEngine
from core.visitors.visitors import *

if __name__ == '__main__':
    min_ops = 5
    max_ops = 10
    max_bits = 16
    engine = PolymorphicEngine(min_ops, max_ops, max_bits)

    text = "Hello World!"
    ctx = engine.transform(text)
    # visitor = BashVisitor()
    # visitor = CSharpVisitor()
    # visitor = CVisitor()
    # visitor = JavaScriptVisitor()
    visitor = JavaVisitor()
    print(visitor.visit(ctx))
