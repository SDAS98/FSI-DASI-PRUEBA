from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Para pruebas en casa usa 127.0.0.1, en clase la 147.96.80.224
    SERVER_URL: str = "http://127.0.0.1:7719/" 
    OLLAMA_URL: str = "http://localhost:11434/api/chat"
    DEFAULT_MODEL: str = "ministral-3:8B"
    
    MI_ALIAS: str = "L-S" 
    MI_PUERTO: int = 7720
    
    SLEEP_TIME: int = 30  # Tiempo entre escaneos del monitor
    PING_TIME: int = 60   # Tiempo para re-notificar a un rival

settings = Settings()