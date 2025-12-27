from math import prod
from typing import TypeVar, Iterable
from collections.abc import Mapping
from my_runnable import Runnable
from my_utils import flatten_numbers
import asyncio

NumbersT = TypeVar("NumbersT", int, float)
ConfigT = ConfigT = TypeVar("ConfigT", bound=Mapping)


class MultiplicationRunnable(Runnable[NumbersT | Iterable, NumbersT, ConfigT]):
    def __init__(self, *values: NumbersT | Iterable) -> None:
        super().__init__()
        self.name = self.__class__.__name__
        self.values = flatten_numbers(values, {"emptyListFiller": 1})

    async def _call(self, input: NumbersT | Iterable, config: ConfigT | None = None) -> NumbersT:
        nums = self.values + flatten_numbers([input], {"emptyListFiller": 1})
        return prod(nums)
    
def testing():
    try:
        print("Testing MultiplicationRunnable:\n")

        print('Test 1: Sequence of numeric inputs.')
        test1 = MultiplicationRunnable(1, 2, 3)
        results1 = asyncio.run(test1.invoke([3]))
        assert results1 == 18, f"Expected 18, got {results1}."
        print(f"Passed 1, 2, 3 in constructor and [5] in invoke, got {results1}. Test 1 passed.\n")

        print('Test 2: Pipeline of two Runnables receiving a mix numberic values and list of lists.')
        test2a = MultiplicationRunnable([1, 2, 3])
        test2b = MultiplicationRunnable(1, [2, [3], ["c", [1.2], []]])
        test2seq = test2a.pipe(test2b)
        results2 = asyncio.run(test2seq.invoke([[3],1]))
        assert results2 == 129.6, f"Expected 108, got {results2}."
        print(f"Passed [1, 2, 3] in the first constructor, 1, [2, [3], [\"c\", [1.2]]] in the second, and [[3],1] in invoke, got {results2}. Test 2 passed.\n")

        print("Yeap, all tests passed.")

    except AssertionError as e:
        print('Test failed: ', e)
    except Exception as e:
        print('Unexpected error: ', e)

if __name__ == "__main__":
    testing()
