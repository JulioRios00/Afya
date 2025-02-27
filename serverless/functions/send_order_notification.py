import json
import os
import datetime
import boto3
import pymongo
from bson import ObjectId
from jinja2 import Environment, FileSystemLoader

MONGODB_URI = os.environ.get('MONGODB_URI')
DB_NAME = os.environ.get('DB_NAME')
client = pymongo.MongoClient(MONGODB_URI)
db = client[DB_NAME]

ses = boto3.client('ses')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL')

template_env = Environment(loader=FileSystemLoader('templates'))

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

def get_order_details(order_id):
    try:
        order = db.orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            return None
        
        products = []
        for product_id in order.get('product_ids', []):
            product = db.products.find_one({"_id": product_id})
            if product:
                category_names = []
                for cat_id in product.get('category_ids', []):
                    category = db.categories.find_one({"_id": cat_id})
                    if category:
                        category_names.append(category['name'])
                
                products.append({
                    "id": str(product["_id"]),
                    "name": product["name"],
                    "description": product["description"],
                    "price": product["price"],
                    "categories": category_names,
                    "image_url": product.get("image_url")
                })
        
        order_with_details = {
            "id": str(order["_id"]),
            "date": order["date"],
            "total": order["total"],
            "products": products
        }
        
        return order_with_details
    
    except Exception as e:
        print(f"Error getting order details: {str(e)}")
        return None

def send_email_notification(order_details, recipient_email):
    try:
        template = template_env.get_template('order_notification_template.html')

        html_content = template.render(order=order_details)
        
        subject = f"New Order Confirmation #{order_details['id']}"
        
        response = ses.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [recipient_email]
            },
            Message={
                'Subject': {
                    'Data': subject
                },
                'Body': {
                    'Html': {
                        'Data': html_content
                    }
                }
            }
        )
        
        return {
            'success': True,
            'message_id': response['MessageId']
        }
    
    except Exception as e:
        print(f"Error sending email notification: {str(e)}")
        return {
            'success': False,
            'error': str(e)
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

        order_id = body.get('order_id')
        recipient_email = body.get('email')
        
        if not order_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'order_id is required'
                })
            }
        
        if not recipient_email:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'email is required'
                })
            }
        
        order_details = get_order_details(order_id)
        if not order_details:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'message': f'Order with ID {order_id} not found'
                })
            }
        
        notification_result = send_email_notification(order_details, recipient_email)
        
        if notification_result['success']:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Order notification sent successfully',
                    'order_id': order_id,
                    'message_id': notification_result['message_id']
                }, cls=JSONEncoder)
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Failed to send order notification',
                    'order_id': order_id,
                    'error': notification_result.get('error', 'Unknown error')
                })
            }
    
    except Exception as e:
        print(f"Error processing order notification: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error processing order notification',
                'error': str(e)
            })
        }
