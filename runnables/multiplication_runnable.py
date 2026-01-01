from math import prod, isclose
from typing import TypeVar, Iterable
from collections.abc import Mapping
from .my_runnable import Runnable
from utils.my_utils import flatten_numbers
import asyncio

NumbersT = TypeVar("NumbersT", int, float)
ConfigT = ConfigT = TypeVar("ConfigT", bound=Mapping)


class MultiplicationRunnable(Runnable[NumbersT | Iterable, NumbersT, ConfigT]):
    def __init__(self, *values: NumbersT | Iterable) -> None:
        super().__init__()
        self.name = self.__class__.__name__
        self.values = flatten_numbers(values, {"empty_list_filler": 1})

    async def _call(self, input: NumbersT | Iterable, config: ConfigT | None = None) -> NumbersT:
        nums = self.values + flatten_numbers([input], {"empty_list_filler": 1})
        return prod(nums)
    
def testing():
    print("Testing MultiplicationRunnable:\n")

    try:
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

        print('Test 3: Sequence of numeric inputs, using batch.')
        results3 = asyncio.run(test1.batch([3, 5]))
        assert all(isclose(a, b) for a, b in zip(results3, [18, 30])), f"Expected [18, 30], got {results3}."
        print(f"Passed 1, 2, 3 in constructor and [3, 5] in invoke, got {results3}. Test 3 passed.\n")

        print('Test 4: Pipeline of two Runnables receiving a mix numberic values and list of lists, using batch.')
        results4 = asyncio.run(test2seq.batch([3, 1]))
        assert all(isclose(a, b) for a, b in zip(results4, [129.6, 43.2])), f"Expected [129.6, 43.2], got [" + ", ".join(f"{x:g}" for x in results4) + "]."
        print(f"Passed [1, 2, 3] in the first constructor, 1, [2, [3], [\"c\", [1.2]]] in the second, and [[3],1] in invoke, got [" + ", ".join(f"{x:g}" for x in results4) + "].\n")

        print("Yeap, all MultiplicationRunnable tests passed.\n")

    except AssertionError as e:
        print('Test failed: ', e)
    except Exception as e:
        print('Unexpected error: ', e)

if __name__ == "__main__":
    testing()
