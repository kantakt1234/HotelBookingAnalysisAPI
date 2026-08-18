from fastapi import Depends, HTTPException, Query, APIRouter, status, Path
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import pandas as pd

from schemas import BookingResponse
from models import Booking
from db import get_db, DATA_FILE_PATH
from auth import verify_credentials

df = pd.read_csv(DATA_FILE_PATH)

bookings_router = APIRouter(prefix="/bookings")


@bookings_router.get(
    '',
    tags=['bookings'],
    response_model=list[BookingResponse],
    summary="Get all bookings",
    description="Returns a list of all bookings from the database.",
)
def bookings(db: Session = Depends(get_db)) -> list[BookingResponse]:
    """Returns all bookings from the database."""
    try:
        bookings = db.query(Booking).all()
        return [BookingResponse.model_validate(booking) for booking in bookings]
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/search',
    tags=['bookings'],
    response_model=list[BookingResponse],
    summary="Search bookings",
    description="Search bookings by various parameters. All parameters are optional.",
)
def search(
    guest_name: Optional[str] = Query(None, min_length=1, max_length=100, description="Guest name"),
    date_from: Optional[date] = Query(None, description="Booking date from"),
    date_to: Optional[date] = Query(None, description="Booking date to"),
    min_stay: Optional[int] = Query(None, ge=0, description="Minimal stay"),
    max_stay: Optional[int] = Query(None, ge=0, description="Maximal stay"),
    min_rate: Optional[float] = Query(None, ge=0, description="Minimal price per night"),
    max_rate: Optional[float] = Query(None, ge=0, description="Maximal price per night"),
    db: Session = Depends(get_db)
) -> list[BookingResponse]:
    """Search bookings."""

    if min_stay is not None and max_stay is not None and min_stay > max_stay:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_stay cannot be greater than max_stay"
        )

    if min_rate is not None and max_rate is not None and min_rate > max_rate:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_rate cannot be greater than max_rate"
        )

    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="date_from cannot be later than date_to"
        )

    try:
        query = db.query(Booking)

        if guest_name:
            query = query.filter(Booking.guest_name.ilike(f"%{guest_name}%"))
        if date_from:
            query = query.filter(Booking.booking_date >= date_from)
        if date_to:
            query = query.filter(Booking.booking_date <= date_to)
        if min_stay is not None:
            query = query.filter(Booking.length_of_stay >= min_stay)
        if max_stay is not None:
            query = query.filter(Booking.length_of_stay <= max_stay)
        if min_rate is not None:
            query = query.filter(Booking.daily_rate >= min_rate)
        if max_rate is not None:
            query = query.filter(Booking.daily_rate <= max_rate)

        bookings = query.all()
        return [BookingResponse.model_validate(booking) for booking in bookings]
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/stats',
    tags=['statistics'],
    summary="Get booking statistics",
    description="Provides statistical information about the dataset, such as total bookings, average length of stay, average daily rate, etc.",
)
def stats():
    """Returns statistical information about hotel bookings."""
    try:
        stats_df = df.copy()
        stats_df['length_of_stay'] = stats_df['stays_in_weekend_nights'] + stats_df['stays_in_week_nights']
        stats_df['booking_date'] = pd.to_datetime(
            stats_df['arrival_date_year'].astype(str) + '-' +
            stats_df['arrival_date_month'] + '-' +
            stats_df['arrival_date_day_of_month'].astype(str)
        )
        stats_df['total_revenue'] = stats_df['adr'] * stats_df['length_of_stay']

        total_bookings = len(stats_df)
        avg_stay = round(stats_df['length_of_stay'].mean(), 2)
        median_stay = round(stats_df['length_of_stay'].median(), 2)

        avg_rate = round(stats_df['adr'].mean(), 2)
        median_rate = round(stats_df['adr'].median(), 2)

        total_revenue = round(stats_df['total_revenue'].sum(), 2)

        unique_guests = stats_df['name'].nunique()
        unique_countries = stats_df['country'].nunique()

        return {
            "total_bookings": total_bookings,
            "unique_guests": unique_guests,
            "unique_countries": unique_countries,

            "stay_statistics": {
                "average": avg_stay,
                "median": median_stay,
                "min": int(stats_df['length_of_stay'].min()),
                "max": int(stats_df['length_of_stay'].max()),
            },

            "rate_statistics": {
                "average": avg_rate,
                "median": median_rate,
                "min": float(stats_df['adr'].min()),
                "max": float(stats_df['adr'].max())
            },

            "total_revenue": total_revenue,
        }
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/analysis',
    tags=['statistics'],
    summary="Advanced booking analysis",
    description="Performs advanced analysis on the dataset, generating insights and trends based on specific criteria."
)
def analysis():
    """Returns advanced analysis and insights from hotel bookings dataset."""
    try:
        analysis_df = df.copy()
        total = len(analysis_df)
        analysis_df['length_of_stay'] = analysis_df['stays_in_weekend_nights'] + analysis_df['stays_in_week_nights']
        analysis_df['booking_date'] = pd.to_datetime(
            analysis_df['arrival_date_year'].astype(str) + '-' +
            analysis_df['arrival_date_month'] + '-' +
            analysis_df['arrival_date_day_of_month'].astype(str)
        )
        analysis_df['total_revenue'] = analysis_df['adr'] * analysis_df['length_of_stay']
        analysis_df['month'] = analysis_df['booking_date'].dt.month
        analysis_df['year'] = analysis_df['booking_date'].dt.year
        analysis_df['day_of_week'] = analysis_df['booking_date'].dt.day_name()
        analysis_df['day_number'] = analysis_df['booking_date'].dt.dayofweek

        yearly = analysis_df.groupby('year').agg(
            total_bookings=('length_of_stay', 'count'),
            avg_stay=('length_of_stay', 'mean'),
            avg_rate=('adr', 'mean'),
            total_revenue=('total_revenue', 'sum')
        ).round(2).reset_index()

        yearly_trends = []
        for _, row in yearly.iterrows():
            yearly_trends.append({
                "year": int(row['year']),
                "bookings_count": int(row['total_bookings']),
                "avg_stay": row['avg_stay'],
                "avg_rate": row['avg_rate'],
                "total_revenue": round(row['total_revenue'], 2)
            })

        monthly = analysis_df.groupby(['year', 'month']).agg(
            bookings=('length_of_stay', 'count'),
            avg_stay=('length_of_stay', 'mean'),
            avg_rate=('adr', 'mean'),
            total_revenue=('total_revenue', 'sum')
        ).round(2).reset_index()

        monthly_trends = []
        for _, row in monthly.iterrows():
            monthly_trends.append({
                "year": int(row['year']),
                "month": int(row['month']),
                "bookings_count": int(row['bookings']),
                "avg_stay": row['avg_stay'],
                "avg_rate": row['avg_rate'],
                "total_revenue": round(row['total_revenue'], 2)
            })

        daily = analysis_df.groupby(['day_number', 'day_of_week']).size().reset_index(name='count')
        daily = daily.sort_values('day_number')

        daily_trends = []
        for _, row in daily.iterrows():
            daily_trends.append({
                "day_of_week": row['day_of_week'],
                "bookings_count": int(row['count']),
                "percentage": round(int(row['count']) / total * 100, 2)
            })

        guests_demographics = analysis_df['country'].value_counts().head(10)
        demographics_stats = [
            {
                "country": country,
                "bookings_count": int(count),
                "percentage": round(count / total * 100, 2)
            }
            for country, count in guests_demographics.items()
        ]

        meal_stats = analysis_df['meal'].value_counts()
        popular_meal_packages = [
            {
                "meal": meal,
                "bookings_count": int(count),
                "percentage": round(count / total * 100, 2)
            }
            for meal, count in meal_stats.items()
        ]

        top_dates = analysis_df['booking_date'].value_counts().head(10)
        popular_arrival_dates = [
            {"date": str(date.date()), "bookings_count": int(count)}
            for date, count in top_dates.items()
        ]

        top_names = analysis_df['name'].value_counts().head(10)
        popular_guest_names = [
            {"name": name, "bookings_count": int(count)}
            for name, count in top_names.items()
        ]

        return {
            "yearly_trends": yearly_trends,
            "monthly_trends": monthly_trends,
            "daily_trends": daily_trends,
            "demographics_stats": demographics_stats,
            "meal_packages_trends": popular_meal_packages,
            "most_popular_arrival_dates": popular_arrival_dates,
            "most_popular_guest_names": popular_guest_names
        }
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/nationality',
    tags=['statistics'],
    summary="Get bookings by nationality",
    description="Returns all bookings for the specified country code."
)
def bookings_by_nationality(
        nationality: str = Query(
            min_length=3,
            max_length=3,
            description="Country code"
        )
):
    """Returns bookings filtered by nationality."""
    try:
        nationality = nationality.upper()
        nationality_df = df[df['country'] == nationality]
        nationality_df = nationality_df.fillna('')
        return nationality_df.to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/popular_meal_package',
    tags=['statistics'],
    summary="Get popular meal package",
    description="Returns the most popular meal package based on booking count.",
)
def popular_meal_package():
    """Returns the most popular meal package."""
    try:
        popular_meal = df['meal'].value_counts().idxmax()
        return {'popular_meal': popular_meal}
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/avg_length_of_stay',
    tags=['statistics'],
    summary="Get average length of stay",
    description="Returns average length of stay grouped by year and hotel type.",
)
def avg_length_of_stay():
    """Returns average length of stay by year and hotel type."""
    try:
        total_stay_df = df.copy()
        total_stay_df["total_stay"] = total_stay_df['stays_in_weekend_nights'] + total_stay_df['stays_in_week_nights']
        total_stay_df = total_stay_df.groupby(['arrival_date_year', 'hotel'])['total_stay'].mean()
        total_stay_df = total_stay_df.reset_index()
        total_stay_df.columns = ['year', 'hotel_type', 'avg_length_of_stay']
        return total_stay_df.to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )

@bookings_router.get(
    '/total_revenue',
    tags=['statistics'],
    summary="Get total revenue by month",
    description="Returns total revenue grouped by month and hotel type.",
)
def total_revenue():
    """Returns total revenue by month and hotel type."""
    try:
        df['total_stay'] = df['stays_in_weekend_nights'] + df['stays_in_week_nights']
        df['revenue'] = df['adr'] * df['total_stay']

        grouped = (df.groupby(['arrival_date_month', 'hotel'])
                   .agg(total_revenue=('revenue', 'sum'))
                   .round(2)
                   .reset_index())
        grouped.columns = ['month', 'hotel_type', 'total_revenue']
        grouped = grouped.sort_values('month')
        return grouped.to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )

@bookings_router.get(
    '/top_countries',
    tags=['statistics'],
    summary="Get top 5 countries",
    description="Returns top 5 countries by number of bookings.",
)
def top_countries():
    """Returns top 5 countries by number of bookings."""
    try:
        top_5 = (df.groupby('country')
                 .size()
                 .reset_index(name='bookings_count')
                 .nlargest(5, 'bookings_count'))

        return top_5.to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )

@bookings_router.get(
    '/repeated_guests_percentage',
    tags=['statistics'],
    summary="Get repeated guests percentage",
    description="Returns the percentage of repeated guests from total bookings.",
)
def repeated_guests_percentage():
    """Returns percentage of repeated guests."""
    try:
        total_bookings = len(df)
        repeated_guests = df['is_repeated_guest'].sum()
        percentage = round(repeated_guests / total_bookings * 100, 2)
        return {"percentage_of_repeated_guests": percentage}
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/total_guests_by_year',
    tags=['statistics'],
    summary="Get total guests by year",
    description="Returns total number of guests grouped by year.",
)
def total_guests_by_year():
    """Returns total number of guests by year."""
    try:
        total_quests_df = df.copy()
        total_quests_df['total_guests'] = df['adults'] + df['children'] + df['babies']

        result = (total_quests_df.groupby('arrival_date_year')['total_guests']
                  .sum()
                  .reset_index())

        result.columns = ['year', 'total_guests']
        return result.to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/avg_daily_rate_resort',
    tags=['statistics'],
    summary="Get average daily rate for Resort Hotel",
    description="Returns average daily rate for Resort Hotel by month. Requires authentication.",
)
def avg_daily_rate_resort(username: str = Depends(verify_credentials)):
    """Returns average daily rate for Resort Hotel by month."""
    try:
        resort_df = df[df['hotel'] == 'Resort Hotel']
        result = (resort_df.groupby('arrival_date_month')['adr']
                  .mean()
                  .round(2)
                  .reset_index())

        result.columns = ['month', 'avg_daily_rate']
        month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        result['month'] = pd.Categorical(result['month'], categories=month_order, ordered=True)
        result = result.sort_values('month')
        return result.to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/most_common_arrival_day_city',
    tags=['statistics'],
    summary="Get most common arrival day for City Hotel",
    description="Retrieves the most common arrival date day of the week for city hotel bookings. Requires authentication.",
)
def most_common_arrival_day_city(username: str = Depends(verify_credentials)):
    """Returns the most common arrival day for City Hotel."""
    try:
        city_df = df[df['hotel'] == 'City Hotel']

        city_df['arrival_date'] = pd.to_datetime(
            city_df['arrival_date_year'].astype(str) + '-' +
            city_df['arrival_date_month'] + '-' +
            city_df['arrival_date_day_of_month'].astype(str)
        )
        city_df['day_of_week'] = city_df['arrival_date'].dt.day_name()

        days_count = city_df['day_of_week'].value_counts()
        most_common_day = days_count.index[0]

        return {"most_common_day": most_common_day}
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/count_by_hotel_meal',
    tags=['statistics'],
    summary="Count of bookings by hotel type and meal package.",
    description="Retrieves the count of bookings grouped by hotel type and meal package. Requires authentication.",
)
def count_by_hotel_meal(username: str = Depends(verify_credentials)):
    """Returns the count of bookings grouped by hotel type and meal package."""
    try:
        result = df.groupby(['hotel', 'meal']).size().reset_index(name='bookings_count')
        result = result.sort_values(['hotel', 'bookings_count'], ascending=[True, False])
        return result.to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/total_revenue_resort_by_country',
    tags=['statistics'],
    summary="Сalculates total revenue for resort hotel by countries.",
    description="Retrieves the total revenue by country for resort hotel bookings. Requires authentication.",
)
def total_revenue_resort_by_country(username: str = Depends(verify_credentials)):
    """Returns the total revenue for resort hotel by each country"""
    try:
        resort_df = df[df['hotel'] == 'Resort Hotel']
        resort_df['total_stay'] = resort_df['stays_in_weekend_nights'] + resort_df['stays_in_week_nights']
        resort_df['revenue'] = resort_df['adr'] * resort_df['total_stay']
        result = resort_df.groupby('country')['revenue'].sum().round(2).reset_index()
        result.columns = ['country', 'total_revenue']
        result = result.sort_values('total_revenue', ascending=False)
        return result.to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )

@bookings_router.get(
    '/count_by_hotel_repeated_guest',
    tags=['statistics'],
    summary="Count bookings by hotel type and guest status.",
    description="Retrieves the count of bookings grouped by hotel type and repeated guest status. Requires authentication.",
)
def count_by_hotel_repeated_guest(username: str = Depends(verify_credentials)):
    """Returns the count of new guests and repeated guests by each hotel type"""
    try:
        result = df.groupby(['hotel', 'is_repeated_guest']).size().reset_index(name='bookings_count')
        result['guest_type'] = result['is_repeated_guest'].map({0: 'New Guest', 1: 'Repeated Guest'})
        result = result.sort_values(['hotel', 'is_repeated_guest'])

        return result[['hotel', 'guest_type', 'bookings_count']].to_dict(orient='records')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )


@bookings_router.get(
    '/{id}',
    tags=['bookings'],
    response_model=BookingResponse,
    summary="Get a booking by its ID",
    description="Retrieves details of a specific booking by its unique ID.",
)
def get_booking(
        id: int = Path(..., ge=0, description="Booking ID"),
        db: Session = Depends(get_db)
) -> Optional[BookingResponse]:
    """Returns a booking by its ID"""
    try:
        booking = db.query(Booking).filter(Booking.id == id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Booking {id} is not found!"
            )
        return BookingResponse.model_validate(booking)
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Server error: {str(ex)}"
        )