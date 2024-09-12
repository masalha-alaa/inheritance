from fractions import Fraction
from math import lcm
from enum import Enum, auto


class HeirsOrderInHtml(Enum):
    HUSBAND = 0
    WIFE = auto()
    SON = auto()
    DAUGHTER = auto()
    FATHER = auto()
    MOTHER = auto()
    BROTHER = auto()
    SISTER = auto()
    RELATIVES = auto()


F = lambda a,b=1: Fraction(a).limit_denominator() / Fraction(b).limit_denominator()
LCD = lambda *f: lcm(*[frac.denominator for frac in f])

ROUND_PRECISION = 30
PRECISION_DISPLAY = 2

# Dictionaries for superscript and subscript numbers
superscripts = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
                '-': '⁻'}
subscripts = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉',
              '-': '₋'}


def _to_superscript(number):
    """Convert a number to its superscript equivalent."""
    return ''.join(superscripts[digit] for digit in str(number))


def _to_subscript(number):
    """Convert a number to its subscript equivalent."""
    return ''.join(subscripts[digit] for digit in str(number))


def display_fraction_in_unicode(fraction):
    """Display any Fraction object in Unicode characters."""

    # Convert numerator to superscript and denominator to subscript
    numerator = _to_superscript(fraction.numerator)
    denominator = _to_subscript(fraction.denominator)

    return f"{numerator}/{denominator}"
