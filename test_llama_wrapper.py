import time
from llama_cpp import Llama

MODEL_PATH = "models/Qwen3-1.7B-Q8.gguf"

print("Loading model...")

start_load = time.time()

llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=4096,
    n_gpu_layers=-1,   # Force Metal
    n_threads=4,
    verbose=True       # Metal logs for debugging
)

load_time = time.time() - start_load
print(f"Model loaded in {load_time:.2f} seconds\n")

# Simple inference test
prompt = "Explain why the sky is blue in one short paragraph."

print("Running inference...")
start_infer = time.time()

output = llm(
    prompt,
    max_tokens=128,
    temperature=0.7,
    top_p=0.9,
    stop=["</s>"]
)

infer_time = time.time() - start_infer

print("\n--- MODEL OUTPUT ---")
print(output["choices"][0]["text"])
print("--------------------\n")

print(f"Inference time: {infer_time:.2f} seconds")
print("Metal inference test completed successfully.")
