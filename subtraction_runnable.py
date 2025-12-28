import asyncio
from my_runnable import Runnable
from my_utils import flatten_numbers
from typing import TypeVar, Iterable, Generic
from collections.abc import Mapping

NumberT = TypeVar("NumberT", int, float)
ConfigT = TypeVar("ConfigT", bound=Mapping)

class SubtractionRunnable(Runnable[NumberT, NumberT, ConfigT]):
    def __init__(self, input: NumberT) -> None:
        super().__init__()
        self.name = self.__class__.__name__
        self.value = input

    async def _call(self, input: NumberT | Iterable, config: ConfigT | None = None) -> NumberT:
        nums = flatten_numbers([input])
        return self.value - sum(nums)

def testing():
    try:
        print('Test')

        print('Test 1: Sequence of numeric inputs.')
        test1 = SubtractionRunnable(10)
        results1 = asyncio.run(test1.invoke(4))
        assert results1 == 6, f"Expected 6, got {results1}"
        print(f"Passed 10 in constructor and 4 in invoke, got {results1}. Test 1 passed.\n")

        print('Test 2: Mix between numeric and iterable inputs.')
        test2 = SubtractionRunnable(10)
        results2 = asyncio.run(test2.invoke([5, [1.3, "c", []]]))
        assert results2 == 3.7, f"Expected 3.7, got {results2}"
        print(f"Passed 10 in constructor and [5, [1.3, \"c\", []]] in invoke, got {results2}. Test 2 passed.\n")

        print('Test 3: Mix between numeric and iterable inputs, and a sequence of runnables')
        test3a = SubtractionRunnable(10)
        test3b = SubtractionRunnable(100)
        test3seq = test3a.pipe(test3b)
        results3 = asyncio.run(test3seq.invoke(["c", [4]]))
        assert results3 == 94, f"Expected 94, got {results3}"
        print(f"Passed 10 in constructor, 100 in the second, and [\"c\", [4]] in invoke, got {results3}. Test 3 passed.\n")

        print("Yeap, all tests passed.")

    except AssertionError as e:
        print('Test failed: ', e)
    except Exception as e:
        print('Unexpected error: : ', e)

if __name__ == "__main__":
    testing()