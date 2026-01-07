import os
import configparser
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), "config.ini"))

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("POSTGRES_DB_URL") # "postgresql://user:password@host:port/dbname"
HCAPTCHA_SECRET_KEY = os.getenv("HCAPTCHA_SECRET_KEY")
HCAPTCHA_SITE_KEY = os.getenv("HCAPTCHA_SITE_KEY") #Este hay que eliminarlo.

LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
MODEL_NAME = os.getenv("MODEL")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CV_PATH = os.path.join(PROJECT_ROOT, "documents", "CV.pdf")
ABOUT_ME_PATH = os.path.join(PROJECT_ROOT, "documents", "about_me.txt")

llm = ChatOpenAI(model=MODEL_NAME, temperature=0.3, api_key=OPENAI_API_KEY)
embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME, api_key=OPENAI_API_KEY)

MAX_MESSAGES_PER_SESSION = int(os.getenv("MAX_MESSAGES_PER_SESSION", "15"))

if not OPENAI_API_KEY:
    raise ValueError("The OPENAI_API_KEY environment variable is not set.")
if not DATABASE_URL:
    raise ValueError("The POSTGRES_DB_URL environment variable is not set.")
if not MODEL_NAME:
    raise ValueError("The MODEL environment variable is not set.")
if not EMBEDDING_MODEL_NAME:
    raise ValueError("The EMBEDDING_MODEL_NAME environment variable is not set.")