from typing import TypeVar, Any
from collections.abc import Mapping
from .my_runnable import Runnable
from utils.my_utils import default_serializer
from datetime import datetime
import asyncio, json


ConfigT = TypeVar("ConfigT", bound=Mapping)


class JsonBuilderRunnable(Runnable[Any, str, ConfigT]):
    def __init__(self) -> None:
        super().__init__()
        self.name = self.__class__.__name__

    async def _call(self, input: Any, config: ConfigT | None = None) -> str:
        payload = {"result": input}
        return json.dumps(payload,default=default_serializer)
    

def testing():
    print('Testing JsonBuilderRunnable:\n')

    try:
        print('Test 1: Number serialisation.')
        test = JsonBuilderRunnable()
        results1 = asyncio.run(test.invoke(4.824))
        assert results1 == '{"result": 4.824}', f"Expected 10, got {results1}"
        print(f"Passed {{\"result\": 4.824}} in invoke, got {results1}. Test 1 passed.\n")

        print('Test 2: Object serialisation.')
        results2 = asyncio.run(test.invoke(test))
        assert results2 == '{"result": {"name": "JsonBuilderRunnable"}}', f"Expected JsonBuilderRunnable object, got {results2}"
        print(f"Passed the object JsonBuilderRunnable in invoke, got {results2}. Test 2 passed.\n")

        print('Test 3: Date serialisation.')
        results3 = asyncio.run(test.invoke(datetime(2026, 1, 1, 15, 0, 0)))
        assert results3 == '{"result": "2026-01-01T15:00:00"}', f"Expected 2026-01-01T15:00:00 object, got {results3}"
        print(f"Passed the datetime(2026, 1, 1, 15, 0, 0) in invoke, got {results3}. Test 3 passed.\n")

        print('Test 4: Date serialisation.')
        results4 = asyncio.run(test.invoke([1, 5.2, "c"]))
        assert results4 == '{"result": [1, 5.2, "c"]}', f"Expected [1, 5.2, \"c\"] object, got {results4}"
        print(f"Passed the [1, 5.2, \"c\"] in invoke, got {results4}. Test 4 passed.\n")

        print("Yeap, all JsonBuilderRunnable tests passed.\n")

    except AssertionError as e:
        print('Test failed: ', e)
    except Exception as e:
        print('Unexpected error: : ', e)

if __name__ == "__main__":
    testing()