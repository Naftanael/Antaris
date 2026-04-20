import sys
import os
from pathlib import Path

def _resolve_adapter_root():
    """Localiza o pacote `agent` sem depender de caminhos legados."""
    env_override = os.getenv("GEMINI_CLOUDCODE_PATH")
    candidate_paths = []

    if env_override:
        candidate_paths.append(Path(env_override).expanduser())

    base_dir = Path(__file__).resolve().parent
    candidate_paths.extend([
        base_dir,
        base_dir / ".agent",
        base_dir.parent,
        Path.cwd(),
    ])

    for candidate in candidate_paths:
        adapter_file = candidate / "agent" / "gemini_cloudcode_adapter.py"
        if adapter_file.is_file():
            sys.path.append(str(candidate))
            return candidate

    raise ModuleNotFoundError(
        "Não foi possível localizar 'agent/gemini_cloudcode_adapter.py'. "
        "Defina GEMINI_CLOUDCODE_PATH com o diretório que contém o pacote 'agent'."
    )

adapter_root = _resolve_adapter_root()

from agent.gemini_cloudcode_adapter import GeminiCloudCodeClient

try:
    client = GeminiCloudCodeClient()
    print(f"Initializing client from: {adapter_root}")
    
    # Simple non-streaming call
    response = client.chat.completions.create(
        model="gemini-2.5-pro",
        messages=[{"role": "user", "content": "Hi, are you working?"}]
    )
    
    print("\nSuccess!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"\nFailed: {e}")
    if hasattr(e, 'code'):
        print(f"Error Code: {e.code}")
    import traceback
    traceback.print_exc()
