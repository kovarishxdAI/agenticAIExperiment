import time
from llama_cpp import Llama, ChatCompletionRequestMessage
from messages import ChatHistory, SystemMessage, ToolMessage, HumanMessage, AIMessage
from runnables import AdditionRunnable, SubtractionRunnable, MultiplicationRunnable, DivisionRunnable

MODEL_PATH = "models/Qwen3-1.7B-Q8.gguf"

system_prompt = SystemMessage("End your response immediately after providing the answer. Ensure no extra text follows.")
user_prompt = HumanMessage("Explain why the sky is blue in one short paragraph.")

chat = ChatHistory()
chat.add_message([system_prompt, user_prompt])
chat_messages = chat.to_prompt_format()

print("Loading model...")

start_load = time.time()
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=32768,        # Context window size in tokens
    n_gpu_layers=-1,   # Offload all threads to the GPU
    n_threads=4,       # Threads used for inference
    verbose=False       # Metal logs for debugging
)
load_time = time.time() - start_load
print(f"Model loaded in {load_time:.2f} seconds\n")

## ================//=========//================
## Simple inference test
## ================//=========//================
print("Running inference...")
start_infer = time.time()
output = llm.create_chat_completion(
    messages = chat_messages,
    max_tokens=512,
    temperature=0.7,
    top_p=0.8,
    top_k=20
)
infer_time = time.time() - start_infer
print(f"Inference time: {infer_time:.2f} seconds")

full_response = output["choices"][0]["message"]["content"].removeprefix("<think>").split("</think>\n\n")
response = full_response[-1]
thinking_text = full_response[0] if len(full_response) > 1 else []

first_ai_msg = AIMessage(response)
chat.add_message(first_ai_msg)

new_prompt = HumanMessage("And during sunset?")
chat.add_message(new_prompt)

print("Running second inference...")
start_infer = time.time()
output = llm.create_chat_completion(
    messages = chat.to_prompt_format(),
    max_tokens=512,
    temperature=0.7,
    top_p=0.8,
    top_k=20
)
infer_time = time.time() - start_infer
print(f"Inference time: {infer_time:.2f} seconds")

full_response = output["choices"][0]["message"]["content"].removeprefix("<think>").split("</think>\n\n")
response = full_response[-1]

second_ai_msg = AIMessage(response)
chat.add_message(second_ai_msg)

chat.print_chat_history()
