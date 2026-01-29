from .my_runnable import Runnable, RunnableSequence
from .dictionary_runnable import DictRunnable
from typing import TypeVar
from collections.abc import Mapping
from textwrap import dedent
import asyncio

InputT = TypeVar("InputT")
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
## defer the formatting of the prompt to when all parameters are known. Here I try to mimic that
## behaviour by implementing a small, MVP version of it.
## ===================================//====================//===================================
class PromptFormatterRunnable(Runnable[InputT, OutputT, ConfigT]):
    def __init__(self, template: str, config:ConfigT = None) -> None:
        """On invoke, will search in the template string for all unresolved parameters and replace
        those values according to the input dictionary using a safe format_map implementation."""
        super().__init__(config)
        self.name = self.__class__.__name__
        self.template = template

    async def _call(self, input: InputT = None, config: ConfigT = None) -> str:

        class SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"
            
        return self.template.format_map(SafeDict(input))
    
    def __or__(self, right_operand):
        if isinstance(right_operand, Runnable):
            return self.pipe(right_operand)
        else:
            raise NotImplemented("Not possible to use the pipe operator for this combination or types.")

    def __ror__(self, left_operand):
        if isinstance(left_operand, dict):
            dict_runnable = DictRunnable(left_operand)
            return RunnableSequence([dict_runnable, self])
        else:
            raise NotImplemented("Not possible to use the pipe operator for this combination or types.")
    


def testing():
    print("Testing PromptFormatterRunnable:\n")
    
    try:
        print("Test 1: Sequence of prompt formatters with a dictionary as input.")

        expected_result = dedent("""\
            Transform the following specifications into a JSON object with 'cpu', 'memory', and 'storage' as keys:
            
            Extract the technical specifications from the following text:
            
            The new laptop model features a 3.5 GHz octa-core processor, 16GB of RAM, and a 1TB NVMe SSD.""")

        prompt_extract = PromptFormatterRunnable("Extract the technical specifications from the following text:\n\n{text_input}")
        prompt_transform = PromptFormatterRunnable("Transform the following specifications into a JSON object with 'cpu', 'memory', and 'storage' as keys:\n\n{specifications}")

        pipeline = {"specifications": prompt_extract} | prompt_transform
        text_input = "The new laptop model features a 3.5 GHz octa-core processor, 16GB of RAM, and a 1TB NVMe SSD."
        result = asyncio.run(pipeline.invoke({"text_input": text_input}))

        assert expected_result == result, "Result differs from the expected result."
        print("Test 1 passed, as pipeline output is equal to expected result.")

        print("Yeap, all PromptFormatterRunnable tests passed.\n")

    except AssertionError as e:
        print("Test failed: ", e) 

    except Exception as e:
        raise print("Unexpected error: ", e)


if __name__ == "__main__":
    testing()