import string
from dataclasses import dataclass
from typing import Optional
from typing import Set

from ._categories import Category
from ._categories import covers_any
from ._categories import list_category
from ._ranges import Range
from ._ranges import lits_to_ranges


@dataclass(frozen=True)
class Character:
    literals: Optional[Set[int]] = None
    categories: Optional[Set[Category]] = None
    positive: bool = True

    @staticmethod
    def ANY() -> "Character":
        return Character()

    @staticmethod
    def LITERAL(literal: int) -> "Character":
        return Character({literal})

    @property
    def minimum_length(self) -> int:
        return 1

    @property
    def starriness(self) -> int:
        return 0

    def __hash__(self) -> int:
        return hash(
            (
                self.positive,
                tuple(sorted(self.literals)) if self.literals else None,
                tuple(sorted(self.categories)) if self.categories else None,
            )
        )

    def exact_character_class(self) -> "Character":
        return self

    def overall_character_class(self) -> "Character":
        return self

    def maximal_character_class(self) -> "Character":
        return self

    @property
    def is_any(self) -> bool:
        return self.literals is None and self.categories is None and self.positive

    @property
    def _is_positive_literal(self) -> bool:
        return self.positive and self.literals is not None and self.categories is None

    @property
    def _is_negative_literal(self) -> bool:
        return not self.positive and self.literals is not None and self.categories is None

    @property
    def _is_positive_category(self) -> bool:
        return self.positive and self.literals is None and self.categories is not None

    @property
    def _is_negative_category(self) -> bool:
        return not self.positive and self.literals is None and self.categories is not None

    def expand_categories(self) -> "Character":
        """
        This is the nuclear option where we expand the categories into literals.
        Can be huge in unicode.
        """
        if self.categories:
            lits: Set[int] = set(self.literals) if self.literals else set()
            for c in self.categories:
                lits.update(list_category(c))
            return Character(literals=lits, positive=self.positive)

        return self

    def __and__(self, other: "Optional[Character]") -> "Optional[Character]":  # noqa: C901
        if other is None:
            return None
        if self.is_any:
            return other
        if other.is_any:
            return self

        # [ab] & [bc] -> [c]
        if self._is_positive_literal and other._is_positive_literal:
            lits = self.literals & other.literals
            if not lits:
                return None
            return Character(literals=lits)
        if self._is_positive_category and other._is_positive_category:
            cats = self.categories & other.categories
            if not cats:
                return None
            return Character(categories=cats)
        # [^ab] & [^bc] -> [^abc]
        if self._is_negative_literal and other._is_negative_literal:
            return Character(literals=self.literals | other.literals, positive=False)
        if self._is_negative_category and other._is_negative_category:
            categories = self.categories | other.categories
            if covers_any(categories):  # [^\d] & [^\D] = nothing
                return None
            return Character(categories=categories, positive=False)
        # [ab] & [^bc] -> [a]
        if self._is_positive_literal and other._is_negative_literal:
            lits = self.literals - other.literals
            if not lits:
                return None
            return Character(literals=lits)
        if other._is_positive_literal and self._is_negative_literal:
            lits = other.literals - self.literals
            if not lits:
                return None
            return Character(literals=lits)

        # TODO: be less lazy and sort out the general case without expanding everything if possible  # noqa: T101
        return self.expand_categories() & other.expand_categories()

    def __rand__(self, other: "Optional[Character]") -> "Optional[Character]":
        return self & other

    def __or__(self, other: "Optional[Character]") -> "Optional[Character]":
        if other is None:
            return self
        if self.is_any or other.is_any:
            return Character.ANY()
        if self == other:
            return self
        if nor := (self.negate() & other.negate()):  # Slow, but logical
            return nor.negate()
        else:
            return Character.ANY()

    def __ror__(self, other: "Optional[Character]") -> "Optional[Character]":
        return self | other

    def __repr__(self) -> str:
        if self.is_any:
            return "."
        result = "["
        if not self.positive:
            result += "^"
        more = False
        if self.literals is not None:
            lits, ranges = lits_to_ranges(self.literals)
            result += ",".join(literal_repr(o) for o in lits)
            if lits and ranges:
                result += ","
            result += ",".join(range_repr(r) for r in ranges)
            more = True
        if self.categories is not None:
            if more:
                result += ";"
            result += ",".join(c.name for c in self.categories)
            more = True
        return result + "]"

    def example(self) -> str:
        for c in nice_characters():
            if self.matches(c):
                return chr(c)

        if self.positive:
            if self.literals:
                if len(self.literals) > 1:
                    # Try to avoid \n due to false positives with the . character and flags
                    return chr(next(o for o in self.literals if o != 0xA))
                return chr(next(iter(self.literals)))
            elif self.categories:
                return sorted(self.categories, key=lambda c: 0 if c.is_positive else 1)[
                    0
                ].example()

        raise NotImplementedError(self)

    def negate(self) -> "Optional[Character]":
        if self.is_any:
            return None
        return Character(
            literals=self.literals,
            categories=self.categories,
            positive=not self.positive,
        )

    def contains(self, subgroup: "Character") -> bool:
        if self.is_any:
            return True
        if subgroup.is_any:
            return False
        if subgroup == self:
            return True

        if self._is_positive_literal and subgroup._is_positive_literal:
            return not (subgroup.literals - self.literals)
        if self._is_positive_category and subgroup._is_positive_category:
            return not (subgroup.categories - self.categories)

        raise NotImplementedError  # Lazy, TODO: do full match  # noqa: T101

    def matches(self, literal: int) -> bool:
        if self.is_any:
            return True
        if self.literals is not None and literal in self.literals:
            return self.positive
        if self.categories:
            for cat in self.categories:
                if cat.contains(literal):
                    return self.positive
        return not self.positive


def nice_characters():
    for c in string.printable[:-5]:
        yield ord(c)


def literal_repr(literal: int) -> str:
    c = chr(literal)
    if c in string.digits or c in string.ascii_letters:
        return c
    elif c in string.punctuation:
        return f"{literal:02x}:{c}"
    return f"{literal:02x}"


def range_repr(r: Range) -> str:
    return "[{}-{}]".format(literal_repr(r.min_val), literal_repr(r.max_val))
