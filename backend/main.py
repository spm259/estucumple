from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os

from . import models, schemas, crud, wati_client
from .database import engine, Base, get_db

# Load environment variables from the .env file
load_dotenv()

# Instantiate the FastAPI app
app = FastAPI()

# Create database tables
Base.metadata.create_all(bind=engine)

# Endpoint to add a new contact
@app.post("/contacts/", response_model=schemas.Contact)
def add_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    # Create contact in the database
    db_contact = crud.create_contact(db=db, contact=contact, user_id=1)  # Assuming user_id = 1 for simplicity
    # Send a birthday reminder using WATI API
    wati_client.send_birthday_reminder(contact.name, db_contact.birthday)
    return db_contact

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Hello World!"}
