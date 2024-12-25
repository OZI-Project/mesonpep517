from ._branch import Branch
from ._repeat import FiniteRepeat
from ._repeat import InfiniteRepeat
from ._sequence import Sequence


def subpattern_to_groupref(subpattern):
    if subpattern is None:
        return None
    if subpattern.starriness == 0:
        return subpattern
    if isinstance(subpattern, FiniteRepeat):
        return subpattern.alter_repeat(
            subpattern_to_groupref(subpattern.repeat),
        )
    if isinstance(subpattern, InfiniteRepeat):
        return FiniteRepeat(
            subpattern_to_groupref(subpattern.repeat),
            subpattern.minimum_repeats,
            subpattern.minimum_repeats + 1,
        )
    if isinstance(subpattern, Branch):
        return Branch(
            [subpattern_to_groupref(b) for b in subpattern.branches],
            subpattern.optional,
        )
    if isinstance(subpattern, Sequence):
        return Sequence([subpattern_to_groupref(e) for e in subpattern.elements])
    return subpattern
