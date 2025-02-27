import typer
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId
from faker import Faker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_database

app = typer.Typer()
fake = Faker()

@app.command()
def populate_database(
    num_categories: int = 5,
    num_products: int = 20,
    num_orders: int = 50,
    clear_existing: bool = False
):
    """
    This script populates the database.
    """
    db = get_database()
    
    if clear_existing:
        typer.echo("Clearing existing data...")
        db.categories.delete_many({})
        db.products.delete_many({})
        db.orders.delete_many({})
    
    typer.echo(f"Creating {num_categories} categories...")
    category_ids = []
    
    categories = [
        "Electronics", "Clothing", "Books", "Home & Kitchen", 
        "Beauty", "Sports", "Toys", "Health", "Automotive", "Office"
    ]
    
    for i in range(min(num_categories, len(categories))):
        result = db.categories.insert_one({
            "name": categories[i]
        })
        category_ids.append(result.inserted_id)
    
    typer.echo(f"Creating {num_products} products...")
    product_ids = []
    
    for i in range(num_products):
        product_categories = random.sample(
            category_ids, 
            random.randint(1, min(3, len(category_ids)))
        )
        
        result = db.products.insert_one({
            "name": fake.product_name(),
            "description": fake.paragraph(),
            "price": round(random.uniform(10.0, 500.0), 2),
            "category_ids": product_categories,
            "image_url": f"https://picsum.photos/id/{random.randint(1, 1000)}/300/300"
        })
        product_ids.append(result.inserted_id)
    
    typer.echo(f"Creating {num_orders} orders...")
    
    for i in range(num_orders):
        order_products = random.sample(
            product_ids, 
            random.randint(1, min(5, len(product_ids)))
        )
        
        order_date = datetime.now() - timedelta(days=random.randint(0, 90))
        
        total = 0
        for prod_id in order_products:
            product = db.products.find_one({"_id": prod_id})
            if product:
                total += product["price"]
        
        total = round(total * random.uniform(0.9, 1.2), 2)
        
        db.orders.insert_one({
            "date": order_date,
            "product_ids": order_products,
            "total": total
        })
    
    typer.echo("Data seeding complete!")

if __name__ == "__main__":
    app()

