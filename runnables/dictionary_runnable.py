from __future__ import annotations
from typing import TypeVar, Generic, AsyncGenerator
from collections.abc import Mapping
from .my_runnable import Runnable, RunnableSequence
import asyncio

InputT = TypeVar("InputT", bound=Mapping)
MidT = TypeVar("MidT")
OutputT = TypeVar("OutputT")
ConfigT = TypeVar("ConfigT", bound=Mapping)

## ===================================//====================//===================================
## Langchain makes it possible to use the pipe operator between a dictionary and a ChatPromptTemplate
## Runnable. Moreover, it is possible to pass a dictionary containing Runnables as values. Example:
##
## extraction_chain = prompt_extract | llm | StrOutputParser()
## full_chain = {"specifications": extraction_chain} | prompt_transform | llm | StrOutputParser()
## Source: Agentic Design Patterns, by Antonio Gulli, page 30
##
## Both extraction_chain and prompt_transform are ChatPromptTemplate Runnables allowing users to
## defer the formatting of the prompt to when all parameters are known.
##
## To mimic this behaviour, not only I need to be able to ".pipe" Runnables with the pipe
## operand, but also do so when only the right-hand side is a Runnable, while deferring
## the usage of the dictionary to when the invoke function is called.
##
## Yet more interesting, the dictionary in that code snippet contains a Runnable inside of it,
## which must be resolved once it runs. To mimic this behaviour, I need to run every Runnable
## inside the dictionary, replacing it in the dictionary by its ".invoke" output once the full
## chain is invoked.
## ===================================//====================//===================================
class DictRunnable(Runnable[InputT, OutputT, ConfigT], Generic[InputT, OutputT, ConfigT]):
    def __init__(self, input_dict: dict) -> None:
        super().__init__()
        self.input_dict = input_dict
        self.name = self.__class__.__name__

    async def _call(self, input: InputT | None = None, config: ConfigT | None = None) -> OutputT:
        return await self._invoke_runnables_in_dict(input)

    async def _invoke_runnables_in_dict(self, data: dict) -> dict:
        """
        Recursively search for any `Runnable` values in a nested dictionary and invoke them.
        Returns a new dictionary with all `Runnable` values replaced by their results.
        """
        updated_data = {}

        for key, value in self.input_dict.items():
            if isinstance(value, dict):
                # If the value is a dictionary, recurse into it.
                updated_data[key] = await self._invoke_runnables_in_dict(value)
            elif isinstance(value, Runnable):
                # If the value is a Runnable, invoke it and replace it with the result.
                updated_data[key] = await value.invoke(data)
            elif isinstance(value, callable):
                # If the value is a Callable, raise an error.
                raise NotImplemented("Runnable dictionaries cannot contain callables.")
            else:
                # Otherwise, just keep the value as is.
                updated_data[key] = value

        return updated_data