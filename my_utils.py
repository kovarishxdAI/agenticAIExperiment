from typing import Iterable, TypeVar, Union
from collections.abc import Mapping

NumberT = TypeVar("NumberT", int, float)
ConfigT = TypeVar("ConfigT", bound=Mapping)

def flatten_numbers(items: Iterable[Union[NumberT, Iterable]], config: ConfigT | None= None) -> list[NumberT]:
   
    filler = config.get("empty_list_filler", 0) if config else 0
    
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