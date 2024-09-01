from flask import Flask, request, jsonify
import uuid
import os
import pandas as pd
from celery import Celery
import requests
from PIL import Image
import io
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse

# Initialize Flask and Celery
app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Database configuration
engine = create_engine('sqlite:///image_data.db')
metadata = MetaData()

# Define table
image_table = Table(
    'images', metadata,
    Column('id', Integer, primary_key=True),
    Column('request_id', String),
    Column('serial_number', Integer),
    Column('product_name', String),
    Column('input_image_url', String),
    Column('output_image_url', String)
)
metadata.create_all(engine)

# Define the directory for processed images
PROCESSED_IMAGES_DIR = 'processed_images'

# Create the directory if it does not exist
if not os.path.exists(PROCESSED_IMAGES_DIR):
    os.makedirs(PROCESSED_IMAGES_DIR)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        request_id = str(uuid.uuid4())
        file_path = f'temp_{request_id}.csv'
        file.save(file_path)
        process_file.delay(file_path, request_id)
        return jsonify({"request_id": request_id}), 202

@app.route('/status/<request_id>', methods=['GET'])
def check_status(request_id):
    Session = sessionmaker(bind=engine)
    session = Session()

    result = session.query(image_table).filter_by(request_id=request_id).all()

    if result:
        data = {}
        for row in result:
            if row.product_name not in data:
                data[row.product_name] = {
                    'input_image_urls': [],
                    'output_image_urls': []
                }
            data[row.product_name]['input_image_urls'].append(row.input_image_url)
            data[row.product_name]['output_image_urls'].append(row.output_image_url)

        return jsonify({"status": "Processing complete", "data": data}), 200
    else:
        return jsonify({"status": "Request ID not found"}), 404

@celery.task
def process_file(file_path, request_id):
    df = pd.read_csv(file_path)
    results = []

    for index, row in df.iterrows():
        serial_number = row['Serial Number']
        product_name = row['Product Name']
        input_image_urls = row['Input Image Urls'].split(',')

        output_image_urls = []

        for image_url in input_image_urls:
            image_data = process_image_from_url(image_url)
            output_image_url = save_image(image_data, request_id, serial_number, image_url)
            output_image_urls.append(output_image_url)

        for input_url, output_url in zip(input_image_urls, output_image_urls):
            results.append({
                'request_id': request_id,
                'serial_number': serial_number,
                'product_name': product_name,
                'input_image_url': input_url,
                'output_image_url': output_url
            })

    store_results_in_db(results)
    os.remove(file_path)
    trigger_webhook(request_id)

def process_image_from_url(image_url):
    response = requests.get(image_url)
    image = Image.open(io.BytesIO(response.content))

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')  # Adjust if using JPEG
    return img_byte_arr.getvalue()

def save_image(image_data, request_id, serial_number, image_url):
    output_image_url = f'processed_images/{request_id}_{serial_number}_{os.path.basename(urlparse(image_url).path)}'
    with open(output_image_url, 'wb') as f:
        f.write(image_data)
    return output_image_url

def store_results_in_db(results):
    Session = sessionmaker(bind=engine)
    session = Session()

    for result in results:
        stmt = image_table.insert().values(
            request_id=result['request_id'],
            serial_number=result['serial_number'],
            product_name=result['product_name'],
            input_image_url=result['input_image_url'],
            output_image_url=result['output_image_url']
        )
        session.execute(stmt)
    session.commit()

def trigger_webhook(request_id):
    webhook_url = 'http://example.com/webhook'  # Update with actual URL
    payload = {'request_id': request_id, 'status': 'Processing complete'}
    requests.post(webhook_url, json=payload)

if __name__ == '__main__':
    app.run(debug=True)
