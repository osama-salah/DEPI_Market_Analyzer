import base64
import io
import sys

import numpy as np
import pandas as pd
import json
import socket
from threading import Thread
from multiprocessing import Process, Queue as MPQueue
from prophet import Prophet  # Assuming Prophet is used for predictions

# Data file and column mappings
data_file_mapping = {
    'super_market_sales': './data/supermarket-sales-data/annex3.csv'
}

data_column_names = {
    'super_market_sales': {'Date': 'ds', 'Wholesale Price (RMB/kg)': 'y'}
}

# Function to rename columns to Prophet's expected format
def rename_dataset_columns(data, data_name):
    return data.rename(columns=data_column_names[data_name])

# Load and prepare data
def load_data(data_name='super_market_sales'):
    try:
        file_path = data_file_mapping[data_name]
        data = pd.read_csv(file_path)
    except KeyError:
        sys.stderr.write("Error: Dataset metadata is missing!\n")
        return None
    except FileNotFoundError:
        sys.stderr.write(f"Error: The file '{file_path}' was not found.\n")
        return None
    except pd.errors.EmptyDataError:
        sys.stderr.write(f"Error: The file '{file_path}' is empty.\n")
        return None

    # Rename columns and parse dates
    data = rename_dataset_columns(data, data_name)
    data['ds'] = pd.to_datetime(data['ds'])
    return data

# Start the TCP server
def start_server(host='0.0.0.0', port=5002):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"[*] Listening on {host}:{port}")

    while True:
        client, addr = server.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = Thread(target=handle_client, args=(client,))
        client_handler.start()

# Handle client requests
def handle_client(client_socket):
    try:
        request_data = client_socket.recv(1024).decode()
        request = json.loads(request_data)
        print(f"Received request: {request}")

        # Process request in a separate process
        result = process_request(request)
        # client_socket.send(json.dumps(result).encode())
        client_socket.sendall(json.dumps(result).encode())
    except Exception as e:
        print(f"Error handling request: {e}")
        client_socket.send(json.dumps({"error": str(e)}).encode())
    finally:
        client_socket.close()

# Run the price predictor using Prophet
def run_predictor(product_id, time_period, optional_date, results_queue):
    data = load_data('super_market_sales')
    if data is None:
        results_queue.put({"error": "Failed to load data."})
        return

    # Get the product data
    item_data = data[data['Item Code'] == product_id]
    item_data.loc[:, 'ds'] = np.array(item_data['ds'])

    model = Prophet(yearly_seasonality=False, changepoint_prior_scale=0.001)
    model.add_seasonality(name='yearly', period=365.25, fourier_order=9)

    # Fit the model
    model.fit(item_data[['ds', 'y']])

    # Create future dates
    future = model.make_future_dataframe(periods=int(time_period))

    # Make predictions
    forecast = model.predict(future)

    img_base64 = None

    if optional_date:
        predicted_price = forecast['yhat'].iloc[0]
    if time_period:
        # Create the plot
        fig = model.plot(forecast)

        # Save the plot to a BytesIO object
        img = io.BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)

        # Convert the image to base64 string
        img_base64 = base64.b64encode(img.read()).decode('utf-8')

        # Print base64 string length for debugging
        print(f"Image base64 length: {len(img_base64)}")
        print(f"Base64 image starts with: {img_base64[:100]}")  # Print first 100 characters for debugging

    # Add placeholder for predicted image
    results_queue.put({
        "product_id": product_id,
        "predicted_price": predicted_price,
        "prediction_image": img_base64
    })

# Process client request
def process_request(request):
    try:
        product_id = request.get('product_id')
        time_period = request.get('time_period')
        optional_date = request.get('optional_date')

        if not product_id or not time_period:
            return {"error": "Missing required parameters: product_id and time_period."}

        results_queue = MPQueue()
        process = Process(target=run_predictor, args=(product_id, time_period, optional_date, results_queue))
        process.start()
        process.join()

        # Retrieve the result from the prediction process
        result = results_queue.get()
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    start_server()
