from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

from models import Base


DATABASE_URL = "sqlite:///hotel.db"
DATA_FILE_PATH = 'hotel_booking_data.csv'

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def load_data_to_database():
    Base.metadata.create_all(bind=engine)
    load_df = pd.read_csv("hotel_booking_data.csv")

    load_df['booking_date'] = pd.to_datetime(
        load_df['arrival_date_year'].astype(str) + '-' +
        load_df['arrival_date_month'] + '-' +
        load_df['arrival_date_day_of_month'].astype(str)
    ).dt.date

    load_df['length_of_stay'] = load_df['stays_in_weekend_nights'] + load_df['stays_in_week_nights']

    load_df['guest_name'] = load_df['name']
    load_df['daily_rate'] = load_df['adr']
    load_df['hotel_type'] = load_df['hotel']

    columns = [
        'booking_date',
        'length_of_stay',
        'guest_name',
        'daily_rate'
    ]

    df_filtered = load_df[columns].copy()

    print(f"Load data to database...")
    df_filtered.to_sql(
        'bookings',
        engine,
        if_exists='replace',
        index_label='id'
    )
    print(f"Data is loaded to database!")