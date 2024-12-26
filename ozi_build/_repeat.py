from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional

if TYPE_CHECKING:
    from ._char import Character


@dataclass(frozen=True)
class Repeat:
    repeat: Any
    minimum_repeats: int

    def example(self) -> str:
        if self.minimum_repeats == 0:
            return ""
        return self.repeat.example() * self.minimum_repeats

    @property
    def minimum_length(self) -> int:
        return self.minimum_repeats * self.repeat.minimum_length

    @property
    def starriness(self) -> int:
        return self.repeat.starriness  # ? and {1,30} are not that starry

    def exact_character_class(self) -> Optional[Character]:
        """
        Repeated character e.g. [bc] for [bc]*, or [a] for (aaa)*
        """
        return self.repeat.exact_character_class()

    def overall_character_class(self) -> Optional[Character]:
        """
        (23)+ -> None, (22)* -> 2
        """
        return self.repeat.overall_character_class()

    def maximal_character_class(self) -> Character:
        """
        (23)+ -> [23], (22)* -> 2, (23*)* -> [23]
        Useful for finding a way to kill a sequence like a(bc*)*$
        """
        return self.repeat.maximal_character_class()


@dataclass(frozen=True)
class InfiniteRepeat(Repeat):
    forced_starriness: Optional[int] = None

    @property
    def starriness(self) -> int:
        if self.forced_starriness is not None:
            return self.forced_starriness
        # a*a*a* is cubic whereas (a*)* is exponential but here we just call it 10
        return 1 + self.repeat.starriness * 10

    def __repr__(self) -> str:
        return f"{self.repeat}{{{self.minimum_repeats}+}}"

    def alter_repeat(self, repeat) -> "InfiniteRepeat":
        return InfiniteRepeat(repeat, self.minimum_repeats)


@dataclass(frozen=True)
class FiniteRepeat(Repeat):
    maximum_repeats: int

    def __repr__(self) -> str:
        return f"{self.repeat}{{{self.minimum_repeats},{self.maximum_repeats}}}"

    def alter_repeat(self, repeat) -> "FiniteRepeat":
        return FiniteRepeat(repeat, self.minimum_repeats, self.maximum_repeats)
