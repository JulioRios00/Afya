import json
import os
import datetime
import boto3
import pymongo
from bson import ObjectId
import pandas as pd
from jinja2 import Environment, FileSystemLoader

MONGODB_URI = os.environ.get('MONGODB_URI')
DB_NAME = os.environ.get('DB_NAME')
client = pymongo.MongoClient(MONGODB_URI)
db = client[DB_NAME]

s3 = boto3.client('s3')
S3_BUCKET = os.environ.get('S3_BUCKET')

template_env = Environment(loader=FileSystemLoader('templates'))

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def generate_sales_report(start_date=None, end_date=None):
    if not end_date:
        end_date = datetime.datetime.now()
    if not start_date:
        start_date = end_date - datetime.timedelta(days=30)
    
    match_query = {
        "date": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    pipeline = [
        {"$match": match_query},
        {
            "$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "total_revenue": {"$sum": "$total"},
                "avg_order_value": {"$avg": "$total"}
            }
        }
    ]

    sales_summary = list(db.orders.aggregate(pipeline))

    orders = list(db.orders.find(match_query).sort("date", -1))
 
    for order in orders:
        product_details = []
        for product_id in order.get('product_ids', []):
            product = db.products.find_one({"_id": product_id})
            if product:
                product_details.append({
                    "id": str(product["_id"]),
                    "name": product["name"],
                    "price": product["price"]
                })
        order['products'] = product_details
    
    product_pipeline = [
        {"$match": match_query},
        {"$unwind": "$product_ids"},
        {
            "$group": {
                "_id": "$product_ids",
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {"$limit": 10},
        {
            "$lookup": {
                "from": "products",
                "localField": "_id",
                "foreignField": "_id",
                "as": "product_info"
            }
        },
        {"$unwind": "$product_info"},
        {
            "$project": {
                "product_id": "$_id",
                "product_name": "$product_info.name",
                "count": 1
            }
        }
    ]
    
    top_products = list(db.orders.aggregate(product_pipeline))
    
    report_data = {
        "generated_at": datetime.datetime.now().isoformat(),
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "summary": sales_summary[0] if sales_summary else {
            "total_orders": 0,
            "total_revenue": 0,
            "avg_order_value": 0
        },
        "top_products": top_products,
        "orders": orders[:50] 
    }
    
    return report_data

def save_report_to_s3(report_data, format='json'):
    """Save the generated report to S3"""
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    if format == 'json':
        filename = f"sales_report_{date_str}.json"
        content = json.dumps(report_data, cls=JSONEncoder)
        content_type = 'application/json'
    elif format == 'csv':
        filename = f"sales_report_{date_str}.csv"
        orders_df = pd.DataFrame([{
            'order_id': str(order['_id']),
            'date': order['date'],
            'total': order['total'],
            'product_count': len(order.get('product_ids', []))
        } for order in report_data['orders']])
        content = orders_df.to_csv(index=False)
        content_type = 'text/csv'
    elif format == 'html':
        filename = f"sales_report_{date_str}.html"
        template = template_env.get_template('sales_report_template.html')
        content = template.render(**report_data)
        content_type = 'text/html'
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=filename,
        Body=content,
        ContentType=content_type
    )
    
    return {
        'bucket': S3_BUCKET,
        'key': filename
    }

def handler(event, context):
    """Lambda handler function"""
    try:
        body = {}
        if 'body' in event:
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        
        start_date_str = body.get('start_date')
        end_date_str = body.get('end_date')
        report_format = body.get('format', 'json')
        
        start_date = None
        end_date = None
        
        if start_date_str:
            start_date = datetime.datetime.fromisoformat(start_date_str)
        if end_date_str:
            end_date = datetime.datetime.fromisoformat(end_date_str)
        
        report_data = generate_sales_report(start_date, end_date)
        
        if isinstance(report_format, list):
            report_locations = {}
            for fmt in report_format:
                report_locations[fmt] = save_report_to_s3(report_data, fmt)
        else:
            report_locations = save_report_to_s3(report_data, report_format)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Sales report generated successfully',
                'report_locations': report_locations
            }, cls=JSONEncoder)
        }
    
    except Exception as e:
        print(f"Error generating sales report: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error generating sales report',
                'error': str(e)
            })
        }
