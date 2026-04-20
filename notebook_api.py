import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from podcastfy.client import PodcastfyClient

def _load_api_env():
    """Carrega o primeiro arquivo .env disponível sem depender de diretórios legados."""
    env_override = os.getenv("NOTEBOOK_API_ENV_FILE")
    candidate_paths = []

    if env_override:
        candidate_paths.append(Path(env_override).expanduser())

    base_dir = Path(__file__).resolve().parent
    candidate_paths.extend(parent / ".env" for parent in (base_dir, *base_dir.parents))
    candidate_paths.append(Path.home() / ".env")
    candidate_paths.extend(sorted(Path.home().glob("*/.env")))

    for env_path in candidate_paths:
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path)
            return env_path

    load_dotenv()
    return None

# Carrega chaves de API do primeiro arquivo .env disponível
loaded_env_path = _load_api_env()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    source_hint = f" ({loaded_env_path})" if loaded_env_path else ""
    raise ValueError(f"GEMINI_API_KEY não encontrada em um arquivo .env disponível{source_hint}")

# Configura o novo SDK do Gemini (Google GenAI)
client = genai.Client(api_key=GEMINI_API_KEY)

class NotebookLLM:
    def __init__(self):
        self.model_id = "gemini-2.0-flash"
        self.podcast_client = PodcastfyClient()

    def upload_source(self, file_path):
        """Faz o upload de um arquivo para o Gemini File API"""
        print(f"Enviando arquivo: {file_path}...")
        sample_file = client.files.upload(file=file_path)
        print(f"Upload concluído: {sample_file.uri}")
        
        # Aguarda o processamento do arquivo
        while sample_file.state == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(2)
            sample_file = client.files.get(name=sample_file.name)
            
        if sample_file.state == "FAILED":
            raise ValueError(f"Falha ao processar arquivo: {sample_file.name}")
            
        return sample_file

    def ask_notebook(self, files, query):
        """Faz uma pergunta baseada em um conjunto de arquivos (estilo NotebookLM)"""
        response = client.models.generate_content(
            model=self.model_id,
            contents=files + [query],
            config=genai.types.GenerateContentConfig(
                system_instruction="Você é um assistente de pesquisa estilo NotebookLM. Use os arquivos fornecidos como única fonte de verdade."
            )
        )
        return response.text

    def generate_audio_overview(self, urls=None, files=None):
        """Gera um Audio Overview (podcast) usando podcastfy"""
        print("Gerando Audio Overview (isso pode levar alguns minutos)...")
        audio_path = self.podcast_client.generate_podcast(
            urls=urls,
            files=files,
            llm_model_name="gemini-2.0-flash"
        )
        return audio_path

if __name__ == "__main__":
    print("API do Notebook LLM carregada com sucesso (usando Google GenAI SDK).")
