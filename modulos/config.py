from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # IP Butler y Ollama
    BUTLER_URL: str = "http://147.96.80.224:7719/"
    OLLAMA_URL: str = "http://localhost:11434/api/chat"
    DEFAULT_MODEL: str = "ministral-3:8B"
    
    # Tiempos de ciclo
    SLEEP_TIME: int = 30 
    PING_TIME: int = 60 

settings = Settings()