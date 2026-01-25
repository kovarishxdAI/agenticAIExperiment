import time
from typing import Mapping, Tuple, List
from llama_cpp import Llama, ChatCompletionRequestMessage
from messages import ChatHistory, SystemMessage, ToolMessage, HumanMessage, AIMessage, BaseMessage
from runnables import AdditionRunnable, SubtractionRunnable, MultiplicationRunnable, DivisionRunnable


class ChatRunner():
    def __init__(self):
        self.MODEL_PATH = "models/Qwen3-1.7B-Q8.gguf"
        self.llm = Llama(
            model_path=self.MODEL_PATH,
            n_ctx=32768,        # Max number of tokens processed per inference
            n_gpu_layers=-1,   # Offload all threads to the GPU
            n_threads=4,       # Threads used for inference
            verbose=False       # Metal logs for debugging
        )
        self.chat = ChatHistory()

    def agent_message_parser(self, raw_output: Mapping) -> Tuple[str, str, str]:
        """Splits the LLM response into its components."""
        full_response = raw_output["choices"][0]["message"]["content"]
        response_breakdown = full_response.removeprefix("<think>").split("</think>\n\n")
        response = response_breakdown[-1]
        thinking_text = response_breakdown[0] if len(response_breakdown) > 1 else []
        return full_response, response, thinking_text

    def run_prompt(self, prompt: str) -> Tuple[Mapping, float]:
        """Runs the LLM passing the provided prompt and returns the output and inference time"""
        start_infer = time.time()
        output = self.llm.create_chat_completion(
            messages = prompt,
            max_tokens=512,
            temperature=0.7,
            top_p=0.8,
            top_k=20
        )
        infer_time = time.time() - start_infer
        return output, infer_time
    
    def add_messages(self, messages: List[BaseMessage] | None) -> None:
        for msg in messages:
            self.chat.add_message(msg)
            print("\n", msg)

            if isinstance(msg, SystemMessage):
                continue

            output, infer_time = self.run_prompt(self.chat.to_prompt_format())
            full_response, response, thinking_text = self.agent_message_parser(output)
            ai_msg = AIMessage(full_response)
            self.chat.add_message(ai_msg)
            print(ai_msg)


def testing():

    chat = ChatRunner()

    try:
        print("Test 1: Two consecutive prompts.\n")
        system_prompt = SystemMessage("End your response immediately after providing the answer. Ensure no extra text follows.")
        first_user_prompt = HumanMessage("Explain why the sky is blue in one short paragraph.")
        second_user_prompt = HumanMessage("And during sunset?")

        chat.add_messages([system_prompt, first_user_prompt, second_user_prompt])
        print("Test 1 completed successfully.\n")

    except Exception as e:
        print(f'Chat runner failed with unexpected error: ', e)

if __name__ == "__main__":
    testing()
