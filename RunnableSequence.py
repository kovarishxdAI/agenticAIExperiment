from __future__ import annotations
from typing import TypeVar, AsyncGenerator, Generic, Sequence
from collections.abc import Mapping
from Runnable import Runnable

InputT = TypeVar("InputT")
MidT = TypeVar("MidT")
OutputT = TypeVar("OutputT")
ConfigT = TypeVar("ConfigT", bound=Mapping)

class RunnableSequence(Runnable[InputT, OutputT, ConfigT], Generic[InputT, OutputT, ConfigT]):
    def __init__(self, runnables: Sequence[Runnable[InputT, OutputT, ConfigT]]) -> None:
        super().__init__()
        self.runnables = runnables
        self.name = self.__class__.__name__
    
    def __str__(self) -> str:
        return " | ".join(str(runnableName) for runnableName in self.runnables)

    async def _call(self, input: InputT, config: ConfigT | None = None) -> OutputT:

        output: InputT | OutputT = input
        for runnable in self.runnables:
            output = await runnable.invoke(output, config)

        return output
    
    async def _stream(self, input, config: ConfigT | None = None) -> AsyncGenerator[OutputT, None]:

        output: InputT | OutputT = input
        for runnable in self.runnables[:-1]:
            output = await runnable.invoke(output, config)
        
        async for fragment in self.runnables[-1].stream(output, config):
            yield fragment

    def pipe(self, newRunnable: Runnable[OutputT, MidT, ConfigT]) -> RunnableSequence[InputT, MidT, ConfigT]:
        return RunnableSequence(self.runnables + [newRunnable])