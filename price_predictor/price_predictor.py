import logging

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
import pandas as pd
import numpy as np
from prophet import Prophet
from concurrent.futures import ThreadPoolExecutor
from serverutils.threading import get_optimal_worker_count
import threading
import uuid
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Time to keep cached images
CACHE_TIME = 1

# Thread-safe cache for storing prediction results
cache = {}
cache_lock = threading.Lock()

# Thread pool for handling concurrent requests
executor = ThreadPoolExecutor(max_workers=get_optimal_worker_count())
logging.info(f"ThreadPoolExecutor initialized with {executor._max_workers} workers")

# Data file and column mappings
data_file_mapping = {
    'super_market_sales': './data/supermarket-sales-data/annex3.csv'
}

data_column_names = {
    'super_market_sales': {'Date': 'ds', 'Wholesale Price (RMB/kg)': 'y'}
}


def load_data(data_name='super_market_sales'):
    file_path = data_file_mapping[data_name]
    data = pd.read_csv(file_path)
    data = data.rename(columns=data_column_names[data_name])
    data['ds'] = pd.to_datetime(data['ds'])
    return data


def run_predictor(product_id, time_period, optional_date):
    data = load_data('super_market_sales')
    item_data = data[data['Item Code'] == product_id]
    item_data.loc[:, 'ds'] = np.array(item_data['ds'])

    model = Prophet(yearly_seasonality=False, changepoint_prior_scale=0.001)
    model.add_seasonality(name='yearly', period=365.25, fourier_order=9)
    model.fit(item_data[['ds', 'y']])

    future = model.make_future_dataframe(periods=int(time_period))
    forecast = model.predict(future)

    predicted_price = None
    if optional_date:
        predicted_price = forecast[forecast['ds'] == pd.to_datetime(optional_date)]['yhat'].iloc[0]

    fig = model.plot(forecast)
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)

    return predicted_price, img


def cache_prediction(product_id, time_period, optional_date):
    predicted_price, img = run_predictor(product_id, time_period, optional_date)

    # Generate a unique ID for this prediction
    prediction_id = str(uuid.uuid4())

    # Save the image to a file
    img_path = f'temp_{prediction_id}.png'
    with open(img_path, 'wb') as f:
        f.write(img.getvalue())

    # Store the result in the cache
    with cache_lock:
        cache[prediction_id] = {
            'product_id': product_id,
            'predicted_price': predicted_price,
            'img_path': img_path,
            'timestamp': datetime.now()
        }

    return prediction_id


@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    product_id = data['product_id']
    time_period = data['time_period']
    optional_date = data.get('optional_date')

    # Run the prediction in a separate thread
    future = executor.submit(cache_prediction, product_id, time_period, optional_date)
    prediction_id = future.result()

    response = {
        'prediction_id': prediction_id,
        'product_id': product_id,
        'predicted_price': cache[prediction_id]['predicted_price']
    }

    return jsonify(response)


@app.route('/get_image/<prediction_id>', methods=['GET'])
def get_image(prediction_id):
    with cache_lock:
        if prediction_id not in cache:
            return "Image not found", 404
        img_path = cache[prediction_id]['img_path']

    return send_file(img_path, mimetype='image/png')


# Clean up old cache entries periodically
def clean_cache():
    with cache_lock:
        current_time = datetime.now()
        for prediction_id in list(cache.keys()):
            if current_time - cache[prediction_id]['timestamp'] > timedelta(minutes=CACHE_TIME):
                os.remove(cache[prediction_id]['img_path'])
                del cache[prediction_id]


# Run cache cleaning every 5 minutes
def cache_cleaning_job():
    clean_cache()
    threading.Timer(300, cache_cleaning_job).start()


if __name__ == '__main__':
    cache_cleaning_job()  # Start the cache cleaning job
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)