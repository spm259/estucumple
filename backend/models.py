from sqlalchemy import Column, Integer, String, Date
from .database import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)  # This field links the contact to the user who added it.
    name = Column(String, index=True)  # The name of the contact (e.g., a friend)
    birthday = Column(Date)  # The birthday of the contact (e.g., '1995-12-25')
