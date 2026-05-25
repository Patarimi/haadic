from lark import Transformer


class SpiceTransformer(Transformer):
    """Lark transformer for parsed SPICE grammar tokens.

    This small transformer converts token nodes (NAME, NET) into Python strings
    so that the parsed tree contains native Python types instead of token objects.
    """

    def NAME(self, d):
        return str(d)

    def NET(self, d):
        return str(d)
