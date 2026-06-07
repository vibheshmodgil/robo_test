from openwakeword.model import Model

print("Loading model...")

model = Model(
    wakeword_models=["hey_jarvis"],
    inference_framework="onnx"
)

print("Loaded successfully")

print("Available models:")
print(model.models.keys())