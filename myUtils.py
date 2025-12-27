from typing import Iterable, TypeVar, Union
from collections.abc import Mapping

NumberT = TypeVar("NumberT", int, float)
ConfigT = TypeVar("ConfigT", bound=Mapping)

def flatten_numbers(items: Iterable[Union[NumberT, Iterable]], config: ConfigT | None= None) -> list[NumberT]:
    filler = 0
    if config is None or "emptyListFiller" not in config:
        filler = 0
    else:
        filler = config.get("emptyListFiller", 0)
    
    # Recursively flatten numbers from any nested structure.
    result = []
    for item in items:
        if isinstance(item, Iterable) and not isinstance(item, (int, float, bytes, str)):
            result.extend(flatten_numbers(item, config))
        elif isinstance(item, (int, float)):
            result.append(item)

    if(len(result) == 0):
        result.append(filler)
    
    return result