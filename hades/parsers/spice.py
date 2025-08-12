from lark import Transformer


class SpiceTransformer(Transformer):
    def NAME(self, d):
        return str(d)

    def NET(self, d):
        return str(d)
