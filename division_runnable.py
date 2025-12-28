from my_runnable import Runnable
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
        return self.value / input
    
def testing():
    print('Testing AdditionRunnable:\n')

    try:
        print('Test 1: Int input in both constructor and invoke.')
        test1 = DivisionRunnable(1)
        results1 = asyncio.run(test1.invoke(4))
        assert results1 == 0.25, f"Expected 0.25, got {results1}"
        print(f"Passed 1 in constructor and 4 in invoke, got {results1}. Test 1 passed.\n")

        print('Test 2: Float input in both constructor and invoke.')
        test2 = DivisionRunnable(2.3)
        results2 = asyncio.run(test2.invoke(5.7653423465))
        rounded_result2 = round(results2, 2)
        assert rounded_result2 == 0.4, f"Expected 0.4, got {rounded_result2}"
        print(f"Passed 2.3 in constructor and 5.7653423465 in invoke, got {rounded_result2}. Test 2 passed.\n")

        print("Yeap, all tests passed.")

    except AssertionError as e:
        print('Test failed: ', e)
    except Exception as e:
        print('Unexpected error: : ', e)

if __name__ == "__main__":
    testing()