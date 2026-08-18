import os
import uvicorn

from fastapi import FastAPI

from routes import bookings_router
from db import load_data_to_database, DATA_FILE_PATH


if not os.path.exists(DATA_FILE_PATH):
    print(f"Error! File not found - '{DATA_FILE_PATH}'!")
    exit(1)


app = FastAPI()

app.include_router(bookings_router)


if __name__ == '__main__':
    load_data_to_database()
    uvicorn.run(app, host='127.0.0.1', port=8000)