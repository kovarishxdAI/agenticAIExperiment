from __future__ import annotations
from typing import TypeVar, Generic, Sequence, AsyncGenerator
from collections.abc import Mapping
import RunnableSequence
import asyncio


InputT = TypeVar("InputT")
MidT = TypeVar("MidT")
OutputT = TypeVar("OutputT")
ConfigT = TypeVar("ConfigT", bound=Mapping)


class Runnable(Generic[InputT, OutputT, ConfigT]):
    def __init__(self) -> None:
        self.name = self.__class__.__name__
    
    def __str__(self) -> str:
        return self.name

    async def _call (self, input: InputT, config: ConfigT | None =None) -> OutputT:
        raise NotImplementedError(
            f"Method not implemented. The class {self.__class__.__name__} must itself implement the _call() method."
        )

    async def _stream(self, input: InputT, config: ConfigT | None = None) -> AsyncGenerator[OutputT, None]:
        yield await self._call(input, config)


    async def invoke(self, input: InputT, config: ConfigT | None =None) -> OutputT:
        return await self._call(input, config)
    
    async def stream(self, input: InputT, config: ConfigT | None = None) -> AsyncGenerator[OutputT, None]:
        yield await self.invoke(input, config)

    async def batch(self, inputs: Sequence[InputT], config: ConfigT | None = None) -> list[OutputT]:
        if config is None:
            config = {}  # type: ignore[misc]
        tasks = [self.invoke(input, config) for input in inputs]
        return await asyncio.gather(*tasks)
    
    def pipe(self, newRunnable: Runnable[OutputT, MidT, ConfigT]) -> RunnableSequence[InputT, MidT, ConfigT]:
        return RunnableSequence([self, newRunnable])


