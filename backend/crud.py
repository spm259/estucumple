from sqlalchemy.orm import Session
from . import models, schemas

# Function to create a new contact for a user
def create_contact(db: Session, contact: schemas.ContactCreate, user_id: int):
    db_contact = models.Contact(**contact.dict(), user_id=user_id)
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

# Function to get a contact by its ID
def get_contact_by_id(db: Session, contact_id: int):
    return db.query(models.Contact).filter(models.Contact.id == contact_id).first()

# Function to get all contacts for a specific user
def get_contacts_by_user(db: Session, user_id: int):
    return db.query(models.Contact).filter(models.Contact.user_id == user_id).all()

# Function to delete a contact by its ID
def delete_contact(db: Session, contact_id: int):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact
