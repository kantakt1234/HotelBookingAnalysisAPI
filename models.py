from sqlalchemy import Column, Integer, String, Float, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_date = Column(Date, nullable=False)
    length_of_stay = Column(Integer, nullable=False)
    guest_name = Column(String(100), nullable=False)
    daily_rate = Column(Float, nullable=False)