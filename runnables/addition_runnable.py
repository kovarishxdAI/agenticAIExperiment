from typing import TypeVar, Iterable
from collections.abc import Mapping
from .my_runnable import Runnable
from utils.my_utils import flatten_numbers
import asyncio

NumberT = TypeVar("NumberT", int, float)
ConfigT = TypeVar("ConfigT", bound=Mapping)

class AdditionRunnable (Runnable[NumberT | Iterable, NumberT, ConfigT]):
    def __init__(self, *values: NumberT | Iterable) -> None:
        super().__init__()
        self.name = self.__class__.__name__
        self.values = flatten_numbers(values)


    async def _call(self, input: NumberT | Iterable[NumberT], config: ConfigT | None = None) -> NumberT:
        nums = self.values + flatten_numbers([input])
        return sum(nums)
    
def testing():
    print('Testing AdditionRunnable:\n')

    try:
        print('Test 1: Sequence of numeric inputs.')
        test1 = AdditionRunnable(1, 2, 3)
        results1 = asyncio.run(test1.invoke(4))
        assert results1 == 10, f"Expected 10, got {results1}"
        print(f"Passed 1, 2, 3 in constructor and 4 in invoke, got {results1}. Test 1 passed.\n")

        print('Test 2: List of numeric inputs.')
        test2 = AdditionRunnable([1, 2.3, 3])
        results2 = asyncio.run(test2.invoke([5]))
        assert results2 == 11.3, f"Expected 11.3, got {results2}"
        print(f"Passed [1, 2, 3] in constructor and [5] in invoke, got {results2}. Test 2 passed.\n")

        print('Test 3: Mix between numeric and iterable inputs, including strings, empty lists, and lists of lists.')
        test3 = AdditionRunnable([1, 2, [3, "c", []]])
        results3 = asyncio.run(test3.invoke(["c", 4]))
        assert results3 == 10, f"Expected 10, got {results3}"
        print(f"Passed [1, 2, [3, \"c\", []]] in constructor and [\"c\", 4] in invoke, got {results3}. Test 3 passed.\n")

        print("Yeap, all AdditionRunnable tests passed.\n")

    except AssertionError as e:
        print('Test failed: ', e)
    except Exception as e:
        print('Unexpected error: : ', e)

if __name__ == "__main__":
    testing()