from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import products, categories, orders, dashboard
import sys
import os
import time
from pymongo.errors import ConnectionFailure
from app.database import get_database, client


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.populate_script import populate_database

app = FastAPI(
    title="Afya developer test",
    description="API for Afya developer test",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(categories.router)
app.include_router(orders.router)
app.include_router(dashboard.router)

@app.lifespan("startup")
async def startup_db_client(app: FastAPI):
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

@app.get("/")
async def root():
    return {"message": "Welcome to developer test for Afya."}