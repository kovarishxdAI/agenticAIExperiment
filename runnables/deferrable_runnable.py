from .my_runnable import Runnable
from typing import TypeVar, Any, Mapping

ConfigT = TypeVar("ConfigT", bound=Mapping)

# ==========================//=======================//==========================
# When the LLM deals with longer formulae, it might need to defer the creation
# of a runnable until the result of the previous one is finished. In these cases,
# if we have an external memory we can draw from (get_b) and instructions to 
# which runnable to create (factory), it is possible to fetch the necessary
# arguments for the constructor when the invoke method is called.
# ==========================//=======================//==========================
class DeferredRunnable(Runnable[Any, Any, ConfigT]):
    def __init__(self, factory, get_constructor_args: Any) -> None:
        self._factory = factory
        self._get_constructor_args = get_constructor_args
        self.name = self.__class__.__name__

    async def _call(self, input, config: ConfigT | None = None):
        b = self._get_constructor_args(config)
        runnable = self._factory(b)
        return await runnable.invoke(input)