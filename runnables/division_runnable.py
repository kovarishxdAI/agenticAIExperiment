from .my_runnable import Runnable
from typing import TypeVar
from collections.abc import Mapping
import asyncio

NumberT = TypeVar("NumberT", int, float)
ConfigT = TypeVar("ConfigT", bound=Mapping)

class DivisionRunnable(Runnable[NumberT, NumberT, ConfigT]):
    def __init__(self, input: NumberT) -> None:
        super().__init__()
        self.value = input
        self.name = self.__class__.__name__

    async def _call(self, input: NumberT, config: ConfigT | None = None) -> NumberT:
        return input / self.value
    
def testing():
    print('Testing DivisionRunnable:\n')

    try:
        print('Test 1: Int input in both constructor and invoke.')
        test1 = DivisionRunnable(4)
        results1 = asyncio.run(test1.invoke(1))
        assert results1 == 0.25, f"Expected 0.25, got {results1}"
        print(f"Passed 4 in constructor and 1 in invoke, got {results1}. Test 1 passed.\n")

        print('Test 2: Float input in both constructor and invoke.')
        test2 = DivisionRunnable(5.7653423465)
        results2 = asyncio.run(test2.invoke(2.3))
        rounded_result2 = round(results2, 2)
        assert rounded_result2 == 0.4, f"Expected 0.4, got {rounded_result2}"
        print(f"Passed 5.7653423465 in constructor and 2.3 in invoke, got {rounded_result2}. Test 2 passed.\n")

        print("Yeap, all DivisionRunnable tests passed.\n")

    except AssertionError as e:
        print('Test failed: ', e)
    except Exception as e:
        print('Unexpected error: : ', e)

if __name__ == "__main__":
    testing()