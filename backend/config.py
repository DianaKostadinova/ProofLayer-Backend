from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "ProofLayer API"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/prooflayer"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Pinata (IPFS)
    pinata_api_key: str = ""
    pinata_secret_key: str = ""
    pinata_jwt: str = ""

    # Solana
    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_program_id: str = ""
    solana_payer_secret_key: str = ""  # base58 encoded

    # AI Service
    ai_service_url: str = "http://localhost:8001"

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
