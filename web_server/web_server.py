from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd

app = Flask(__name__)

PREDICTION_SERVER_URL = 'http://localhost:5002'

product_id_name_mapping = pd.DataFrame()


def load_products():
    global product_id_name_mapping
    product_id_name_mapping = pd.read_csv('static/data/annex4.csv')
    return [{'product_id': row['Item Code'], 'product_name': row['Item Name']} for _, row in
            product_id_name_mapping.iterrows()]


products_data = load_products()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_products', methods=['GET'])
def get_products():
    return jsonify(products_data)


@app.route('/price_prediction', methods=['GET', 'POST'])
def price_prediction():
    if request.method == 'POST':
        data = request.json
        product_id = data.get('product_id')
        time_period = data.get('time_period')
        optional_date = data.get('optional_date')

        if product_id and time_period:
            try:
                # Make a request to the prediction server
                response = requests.post(f'{PREDICTION_SERVER_URL}/predict', json={
                    'product_id': product_id,
                    'time_period': time_period,
                    'optional_date': optional_date
                })
                response.raise_for_status()

                result = response.json()

                # Get the image URL using the prediction_id
                result['image_url'] = f'{PREDICTION_SERVER_URL}/get_image/{result["prediction_id"]}'

                result['product_name'] = \
                product_id_name_mapping[product_id_name_mapping['Item Code'] == product_id]['Item Name'].iloc[0]

                return render_template('price_prediction_result.html', result=result)
            except requests.RequestException as e:
                return f"Error: {str(e)}", 500
        else:
            return "Error: Product ID or time period is missing", 400
    else:
        return render_template('price_prediction_form.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)