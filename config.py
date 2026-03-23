import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./output")
    ANCHOR_VERSION: str = os.getenv("ANCHOR_VERSION", "0.30.0")
    SOLANA_CLUSTER: str = os.getenv("SOLANA_CLUSTER", "localnet")
    GENERATE_CLIENT: bool = os.getenv("GENERATE_CLIENT", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def ai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY)

config = Config()
