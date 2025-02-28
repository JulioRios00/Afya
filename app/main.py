from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import products, categories, orders, dashboard
import sys
import os
from app.utils.lifespan import app_lifespan

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(
    title="Afya developer test",
    description="API for Afya developer test",
    version="1.0.0",
    lifespan=app_lifespan
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

@app.get("/")
async def root():
    return {"message": "Welcome to developer test for Afya."}