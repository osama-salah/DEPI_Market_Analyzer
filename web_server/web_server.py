from flask import Flask, render_template, request, jsonify, url_for
import pandas as pd
import socket
import json

app = Flask(__name__)

ML_SERVER_HOST = '127.0.0.1'  # Placeholder for ML server host
PREDICTION_SERVER_HOST = '127.0.0.1'
ML_SERVER_PORT = 5000
PREDICTION_SERVER_PORT = 5002

product_id_name_mapping = pd.DataFrame()

# Load product data from CSV into memory
def load_products():
    global product_id_name_mapping
    product_id_name_mapping = pd.read_csv('static/data/annex4.csv')
    return [{'product_id': row['Item Code'], 'product_name': row['Item Name']} for _, row in product_id_name_mapping.iterrows()]

products_data = load_products()  # Preload the products into memory

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_products', methods=['GET'])
def get_products():
    return jsonify(products_data)

# Modify the price prediction request to include time_period and optional_date
def get_price_prediction(product_id, time_period, optional_date=None):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((PREDICTION_SERVER_HOST, PREDICTION_SERVER_PORT))
            # Prepare data as JSON with product_id, time_period, and optional_date
            request_data = {
                "product_id": product_id,
                "time_period": time_period,
                "optional_date": optional_date  # Could be None
            }
            client.sendall(json.dumps(request_data).encode())  # Send JSON data to prediction server

            response = b""
            while True:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response += chunk

            # response = client.recv(4096).decode()
            print('Response: ', response)
            print("Response type: ", type(response))

            result = json.loads(response)
            result['product_name'] = product_id_name_mapping[product_id_name_mapping['Item Code'] == result['product_id']]['Item Name'].iloc[0]

            return result  # JSON data containing product name, price, and image

    except ConnectionRefusedError:
        return "<p class='error'>Unable to connect to Prediction server. Is it running?</p>"
    except Exception as e:
        return f"<p class='error'>An error occurred: {str(e)}</p>"

@app.route('/price_prediction', methods=['GET', 'POST'])
def price():
    if request.method == 'POST':
        product_id = request.json.get('product_id')  # Get product_id from POST JSON data
        time_period = request.json.get('time_period')  # Get time_period from POST JSON data
        optional_date = request.json.get('optional_date')  # Get optional date from POST JSON data

        if product_id and time_period:
            result = get_price_prediction(product_id, time_period, optional_date)
            return render_template('price_prediction_result.html', result=result)
        else:
            return "Error: Product ID or time period is missing", 400
    else:
        return render_template('price_prediction_form.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
