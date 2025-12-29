from typing import Iterable, TypeVar, Union, Any
from collections.abc import Mapping
from datetime import date, datetime
import base64

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


def default_serializer(obj: Any) -> Mapping:

    if isinstance(obj, bytes | bytearray):
        return {
            "type": "byte",
            "value": base64.b64encode(obj).decode("utf-8"),
        }
    
    if isinstance(obj, set):
        return list(obj)
    
    if isinstance(obj, date | datetime):
        return obj.isoformat()
    
    if hasattr(obj, "__dict__"):
        return obj.__dict__

    return str(obj)