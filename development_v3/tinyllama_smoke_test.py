from llama_cpp import Llama

model = Llama(
    model_path="/models/TinyLlama-1.1B-Chat-v1.0-Q2_K.gguf",
    n_ctx=256,
    n_batch=32,
    n_threads=2,
    n_gpu_layers=0,
    verbose=False,
)

result = model.create_completion(
    "The capital of France is",
    max_tokens=16,
    temperature=0.1,
)

print("INFERENCE_OK:", result["choices"][0]["text"].strip())
