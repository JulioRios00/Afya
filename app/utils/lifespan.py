from contextlib import asynccontextmanager
from fastapi import FastAPI
import time
from pymongo.errors import ConnectionFailure
from app.database import get_database, client
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from scripts.populate_script import populate_database

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            client.admin.command('ismaster')

            db = get_database()
            if db.categories.count_documents({}) == 0:
                print("Database is empty, populating with mocked data...")
                populate_database(
                    num_categories=5,
                    num_products=20,
                    num_orders=50,
                    clear_existing=False
                )
                print("Database initialized successfully!")
            else:
                print("Database already contains some data, moving ahead.")

            break
        except ConnectionFailure:
            print(f"MongoDB not ready yet (attempt {attempt+1}/{max_retries}), we will retry very soon")
            time.sleep(2)
            if attempt == max_retries - 1:
                print("Warning: Could not connect to MongoDB.")

    yield