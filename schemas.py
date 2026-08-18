from pydantic import BaseModel, Field

from datetime import date


class BookingResponse(BaseModel):
    id: int = Field(title="Unique ID of booking")
    guest_name: str = Field(title="Guest full name")
    booking_date: date = Field(title="Date of booking")
    length_of_stay: int = Field(title="Length of stay at the hotel")
    daily_rate: float = Field(title="Profit of a one-day stay at the hotel")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "guest_name": "Ernest Barnes",
                "booking_date": "2015-07-01",
                "length_of_stay": 0,
                "daily_rate": 0,
            }
        }