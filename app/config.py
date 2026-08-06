import os
from dotenv import load_dotenv
from sqlalchemy import URL

load_dotenv()  # reads the .env file in project root


class Settings:
    # ---- MySQL ----
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "flower_billing_db")

    # URL.create safely escapes special characters in credentials (for example, @).
    SQLALCHEMY_DATABASE_URL = URL.create(
        "mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    )

    # ---- JWT ----
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


settings = Settings()
