from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./es_tu_cumple.db")

# create an engine, which is responsible for managing the connection to the database.
# DATABASE_URL tells the engine which database to connect to.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for getting a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Why Use a Dependency?:
# In FastAPI, we use dependencies to inject things into our API functions. In this case, get_db() will inject a database session whenever it’s needed.
# This ensures that every time we make a request, we have a fresh session, and after the request is complete, the session is properly closed.