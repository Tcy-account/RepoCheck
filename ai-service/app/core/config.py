import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "RepoCheck AI Service"
    VERSION: str = "1.0.0"

    # LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # GitHub
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # GitLab
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")

    # arXiv
    ARXIV_BASE_URL: str = "https://export.arxiv.org/api/query"


settings = Settings()
