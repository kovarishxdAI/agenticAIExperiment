from .my_runnable import Runnable
from typing import TypeVar
from collections.abc import Mapping
import asyncio
import json


ConfigT = TypeVar("ConfigT", bound=Mapping)


class JsonParserRunnable(Runnable[str, Mapping, ConfigT]):
    def __init__(self, config: ConfigT | None = None) -> None:
        super().__init__(config)
        self.name = self.__class__.__name__
        self.error = config.get("error") if config else None

    async def _call(self, input: str, config: ConfigT | None = None) -> Mapping:
        if not input or not isinstance(input, str):
            return self.error
        
        try:
            return json.loads(input)
        except Exception as e:
            if self.error is not None:
                raise RuntimeError(self.error)
            return e


def testing():
    print("Testing JsonParserRunnable:\n")

    try:
        print('Test 1: Valid JSON object.')
        parser = JsonParserRunnable()
        results1 = asyncio.run(parser.invoke('{"band":"Dream Theater","music_length_min":25}'))
        assert results1['band'] == "Dream Theater", f"Expected Dream Theater, got {results1['band']}."
        assert results1['music_length_min'] == 25, f"Expected 25, got {results1['music_length_min']}."
        print(f"Passed \"band\":\"Dream Theater\",\"music_length_min\":25 in invoke, got {results1}. Test 1 passed.\n")

        print('Test 2: Valid JSON array.')
        results2 = asyncio.run(parser.invoke('[1, 2, 3, 4, 5]'))
        assert isinstance(results2, list), f"Input is not an array."
        assert len(results2) == 5, f"Input length is not 5."
        print(f"Passed [1, 2, 3, 4, 5] in invoke, got {results2}. Test 2 passed.\n")

        print('Test 3: Invalid JSON object.')
        results3 = asyncio.run(parser.invoke('Silly text.'))
        assert not results3, f"Did not return null."
        print(f"Passed \"Silly text.\" in invoke, got {results3}. Test 3 passed.\n")

        print('Test 4: Invalid JSON object.')
        results4 = asyncio.run(parser.invoke(''))
        assert not results4, f"Did not return null."
        print(f"Passed an empty string in invoke, got {results4}. Test 4 passed.\n")

        print('Test 5: Invalid JSON object with custom message.')
        parser2 = JsonParserRunnable('{"error":  "Not a valid JSON."}')
        results5 = asyncio.run(parser2.invoke('Silly text.'))
        assert results5 == "Not a valid JSON.", f"Did not return the right message."
        print(f"Passed an empty string in invoke, along with the default error message \"Not a valid JSON.\" in the constructor, got \"{results5}\". Test 5 passed.\n")

        print('Test 6: Nested valid JSON object.')
        results6 = asyncio.run(parser.invoke('{"band":"Dream Theater","music": {\"music_name\": \"Octavarium\", \"music_length_min\":25}}'))
        assert results6['band'] == "Dream Theater", f"Expected Dream Theater, got {results6['band']}."
        assert results6['music']['music_length_min'] == 25, f"Expected 25, got {results6['music']['music_length_min']}."
        print(f'Passed {{"band":"Dream Theater","music": {{"music_name": "Octavarium", "music_length_min":25}}}} in invoke, got {results6}. Test 6 passed.\n')

        print("Yeap, all JsonParserRunnable tests passed.\n")

    except AssertionError as e:
        print('Test failed: ', e)
    except Exception as e:
        print('Unexpected error: ', e)

if __name__ == "__main__":
    testing()