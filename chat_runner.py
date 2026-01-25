import time, re, asyncio
from collections import deque
from typing import Mapping, Tuple, List
from llama_cpp import Llama, ChatCompletionRequestMessage
from messages import ChatHistory, SystemMessage, ToolMessage, HumanMessage, AIMessage, BaseMessage
from runnables import AdditionRunnable, SubtractionRunnable, MultiplicationRunnable, DivisionRunnable
from calculator import Calculator


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

    def agent_message_parser(self, raw_output: Mapping) -> Tuple[str, str, str, str]:
        """Splits the LLM response into its components."""
        full_response = raw_output["choices"][0]["message"]["content"]
        response_breakdown = full_response.removeprefix("<think>").split("</think>\n\n")
        thinking_text = response_breakdown[0] if len(response_breakdown) > 1 else []
        response = response_breakdown[-1]

        execution_plan: str = None
        if response.find("<calculator>") != -1:
            match = re.search(r"<calculator>(.*?)</calculator>", response, re.DOTALL)
            execution_plan = match.group(1).strip() if match else None

        return full_response, response, thinking_text, execution_plan

    def run_prompt(self, prompt: str) -> Tuple[Mapping, float]:
        """Runs the LLM passing the provided prompt and returns the output and inference time"""
        start_infer = time.time()
        output = self.llm.create_chat_completion(
            messages = prompt,
            max_tokens=2048,
            temperature=0.7,
            top_p=0.8,
            top_k=20
        )
        infer_time = time.time() - start_infer
        return output, infer_time
    
    def process_messages(self, messages: List[BaseMessage] | None) -> None:
        message_queue = deque(messages)

        while message_queue:
            msg = message_queue.popleft()

            self.chat.add_message(msg)
            print("\n", msg)

            if isinstance(msg, SystemMessage) or isinstance(msg, ToolMessage):
                continue

            output, infer_time = self.run_prompt(self.chat.to_prompt_format())
            full_response, response, thinking_text, execution_plan = self.agent_message_parser(output)

            ai_msg = AIMessage(full_response)
            self.chat.add_message(ai_msg)
            print(ai_msg)

            if execution_plan is not None and execution_plan != "":
                calc = Calculator(execution_plan)
                result = asyncio.run(calc.execute_plan())
                new_msg = ToolMessage("Result: " + f'{result:.2f}' + ".", "calculator")
                message_queue.append(new_msg) 
                self.chat.add_message(new_msg)

    def erase_chat_history(self) -> None:
        """Erases the chat history."""
        self.chat.clear_history()


def test_one(chat: ChatRunner) -> None:
    print("Test 1: Two consecutive simple questions along with system question.\n")
    system_prompt = SystemMessage("End your response immediately after providing the answer. Ensure no extra text follows.")
    first_user_prompt = HumanMessage("Explain why the sky is blue in one short paragraph.")
    second_user_prompt = HumanMessage("And during sunset?")

    chat.process_messages([system_prompt, first_user_prompt, second_user_prompt])
    print("Test 1 completed successfully.\n")

def test_two(chat:ChatRunner) -> None:
    print("Test 2: Using Atom of Thought.")
    system_prompt = SystemMessage("""You are a mathematical planning assistant using Atom of Thought methodology.

        CRITICAL RULES:
        1. Extract every number from the user's question and put it in the "input" field.
        2. Each atom expresses EXACTLY ONE operation: add, subtract, multiply, divide.
        3. NEVER combine operations in one atom. For example, "(5 + 3) × 2" → must be TWO atoms: one for add, one for multiply.
        4. The "final" atom reports only the result of the last computational atom; it must NOT have its own input. Do not include an "input" field in final atoms.
        5. Use "<result_of_N>" to reference previous atom results; never invent calculations in the final atom.
        6. Output ONLY valid JSON matching the schema, with no explanation or extra text.
        7. Always include the <calculator> tag at the beginning and </calculator> tag at the end of your response.

        CORRECT EXAMPLE for "What is (15 + 7) × 3 - 10?":
        <calculator>
        {
            "atoms": [
                {"id": 1, "kind": "tool", "name": "add", "input": {"a": 15, "b": 7}, "dependsOn": []},
                {"id": 2, "kind": "tool", "name": "multiply", "input": {"a": "<result_of_1>", "b": 3}, "dependsOn": [1]},
                {"id": 3, "kind": "tool", "name": "subtract", "input": {"a": "<result_of_2>", "b": 10}, "dependsOn": [2]},
                {"id": 4, "kind": "final", "name": "report", "dependsOn": [3]}
            ]
        }
        </calculator>

        WRONG EXAMPLES:
        - Empty input: {"input": {}}
        - Missing parameters, such as a missing b parameter: {"input": {"a": "<result_of_1>"}}
        - Combined operations: "add then multiply" → must be TWO atoms
        - Final atom with input: {"kind": "final", "input": {"a": 5}} is INVALID
        - Missing <calculator> or </calculator> tags.

        Available tools: add, subtract, multiply, divide
        - Each tool requires: {"a": <number or reference>, "b": <number or reference>}
        - kind options: "tool", "decision", "final"
        - dependsOn: array of atom IDs that must complete first

        Always extract the actual numbers from the question and put them in the input fields! Never combine operations or invent calculations in final atoms.""")
    first_user_prompt = HumanMessage("What's 8 - 4 / 4?")

    chat.erase_chat_history()
    chat.process_messages([system_prompt, first_user_prompt])
    print("Test 2 executed.")

def test_three(chat:ChatRunner) -> None:
    print("Test 3: Using Atom of Thought for a more complex formula.")
    system_prompt = SystemMessage("""You are a mathematical planning assistant using Atom of Thought methodology.

        CRITICAL RULES:
        1. Extract every number from the user's question and put it in the "input" field.
        2. Each atom expresses EXACTLY ONE operation: add, subtract, multiply, divide.
        3. NEVER combine operations in one atom. For example, "(5 + 3) × 2" → must be TWO atoms: one for add, one for multiply.
        4. The "final" atom reports only the result of the last computational atom; it must NOT have its own input. Do not include an "input" field in final atoms.
        5. Use "<result_of_N>" to reference previous atom results; never invent calculations in the final atom.
        6. Output ONLY valid JSON matching the schema, with no explanation or extra text.
        7. Always include the <calculator> tag at the beginning and </calculator> tag at the end of your response.

        CORRECT EXAMPLE for "What is (15 + 7) × 3 - 10?":
        <calculator>
        {
            "atoms": [
                {"id": 1, "kind": "tool", "name": "add", "input": {"a": 15, "b": 7}, "dependsOn": []},
                {"id": 2, "kind": "tool", "name": "multiply", "input": {"a": "<result_of_1>", "b": 3}, "dependsOn": [1]},
                {"id": 3, "kind": "tool", "name": "subtract", "input": {"a": "<result_of_2>", "b": 10}, "dependsOn": [2]},
                {"id": 4, "kind": "final", "name": "report", "dependsOn": [3]}
            ]
        }
        </calculator>

        WRONG EXAMPLES:
        - Empty input: {"input": {}}
        - Missing parameters, such as a missing b parameter: {"input": {"a": "<result_of_1>"}}
        - Combined operations: "add then multiply" → must be TWO atoms
        - Final atom with input: {"kind": "final", "input": {"a": 5}} is INVALID
        - Missing <calculator> or </calculator> tags.

        Available tools: add, subtract, multiply, divide
        - Each tool requires: {"a": <number or reference>, "b": <number or reference>}
        - kind options: "tool", "decision", "final"
        - dependsOn: array of atom IDs that must complete first

        Always extract the actual numbers from the question and put them in the input fields! Never combine operations or invent calculations in final atoms.""")
    first_user_prompt = HumanMessage("What's (2 + 10 + 4 + 2) * (8 - 4 / 5)?")

    chat.erase_chat_history()
    chat.process_messages([system_prompt, first_user_prompt])
    print("Test 3 executed.")

def testing():

    chat = ChatRunner()

    try:
        ## Two consecutive simple questions along with system question.
        #test_one(chat)

        ## Using Atom of Thought.
        #test_two(chat)

        ## Using Atom of Thought for a more complex formula.
        test_three(chat)

    except Exception as e:
        print(f'Chat runner failed with unexpected error: ', e)

if __name__ == "__main__":
    testing()
