from .my_runnable import Runnable
from typing import TypeVar, Any, Mapping, Callable, Dict

ConfigT = TypeVar("ConfigT", bound=Mapping)

# ==========================//=======================//==========================
# When the LLM formulates an execution plan where the result of upstream steps 
# are used as parameters for downstream steps, such as when the calculator deals 
# with longer formulae, it might need to defer the creationof a runnable until 
# the result of a previous one is available.
# ==========================//=======================//==========================
class DeferredRunnable(Runnable[Any, Any, ConfigT]):
    def __init__(
            self, 
            factory, 
            get_constructor_arg: Callable | None, 
            get_invoke_arg: Callable | None, 
            config: ConfigT | None = None
        ) -> None:

        super().__init__(config)
        self._factory = factory
        self._get_constructor_args = get_constructor_arg
        self.get_invoke_args = get_invoke_arg
        self.name = self.__class__.__name__

    async def _call(self, input: Any, config: ConfigT | None = None) -> Any:
        constructor_args = self._get_constructor_args(config)
        runnable = self._factory(constructor_args)

        local_input = self.get_invoke_args(config) if self.get_invoke_args else input
        output = await runnable.invoke(local_input)

        return output