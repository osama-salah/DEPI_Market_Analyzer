from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd

app = Flask(__name__)

PREDICTION_SERVER_URL = 'http://localhost:5002'
SENTIMENT_SERVER_URL = 'http://localhost:5000'

product_id_name_mapping = pd.DataFrame()


def load_products():
    global product_id_name_mapping
    product_id_name_mapping = pd.read_csv('static/data/annex4.csv')
    return [{'product_id': row['Item Code'], 'product_name': row['Item Name']} for _, row in
            product_id_name_mapping.iterrows()]


products_data = load_products()


def get_prediction(endpoint, product_id, time_period, optional_date=None):
    try:
        url = f'http://{PREDICTION_SERVER_URL}/{endpoint}'
        payload = {
            'product_id': product_id,
            'time_period': time_period,
            'optional_date': optional_date
        }
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        # Add the image URL to the data
        data['image_url'] = f'http://{PREDICTION_SERVER_URL}/get_image/{data["prediction_id"]}'

        return data
    except requests.ConnectionError:
        return {"error": "Unable to connect to ML server. Is it running?"}
    except requests.Timeout:
        return {"error": "Request to ML server timed out. The analysis might be taking too long."}
    except requests.RequestException as e:
        return {"error": f"An error occurred while communicating with the ML server: {str(e)}"}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sentiment_analysis')
def sentiment_analysis():
    return render_template('sentiment_analysis.html')

@app.route('/get_products', methods=['GET'])
def get_products():
    return jsonify(products_data)

# ----- Sentiment Analysis Part -----
def get_insights(product_url):
    try:
        response = requests.post(f'{SENTIMENT_SERVER_URL}/analyze',
                                 json={'url': product_url},
                                 timeout=300)  # 5-minute timeout
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        pros = "".join([f"<li>{p}</li>" for p in data['pros']])
        pros_html_str = f"<ul>{pros}</ul>"
        cons = "".join([f"<li>{c}</li>" for c in data['cons']])
        cons_html_str = f"<ul>{cons}</ul>"

        # Format the data as HTML
        formatted_html = f"""
        <h2>Insights for {data['product']}</h2>
        <p>{data['summary']}</p>
        <p>
        <strong>Insights:</strong>
        <p><strong>Price:</strong> {data['price']}</p>
        <p><strong>Average rating:</strong> {data['avg_rating']}</p>
        <p><strong>Positive reviews:</strong> {data['positive_reviews']}</p>
        <p><strong>Negative reviews:</strong> {data['negative_reviews']}</p>
        <p><strong>Pros:</strong>{pros_html_str}</p>
        <p><strong>Cons:</strong>{cons_html_str}</p>
        </p>
        """
        return formatted_html
    except requests.ConnectionError:
        return "<p class='error'>Unable to connect to ML server. Is it running?</p>"
    except requests.Timeout:
        return "<p class='error'>Request to ML server timed out. The analysis might be taking too long.</p>"
    except requests.RequestException as e:
        return f"<p class='error'>An error occurred while communicating with the ML server: {str(e)}</p>"
    except Exception as e:
        return f"<p class='error'>An unexpected error occurred: {str(e)}</p>"

@app.route('/get_insights', methods=['POST'])
def insights():
    product_url = request.json['product_url']  # Changed from product_name to product_url
    result = get_insights(product_url)
    return result  # Returning HTML directly

# -----Prediction part -----
def get_prediction(endpoint, data, template):
    product_id = data.get('product_id', None)
    time_period = data.get('time_period', None)
    optional_date = data.get('optional_date', None)

    if product_id and (time_period or optional_date):
        try:
            # Make a request to the prediction server
            response = requests.post(f'{PREDICTION_SERVER_URL}/{endpoint}', json={
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

            result['optional_date'] = optional_date

            prediction_name = 'predicted_price' if endpoint == 'predict_price' else 'predicted_demand'

            if result[prediction_name]:
                result[prediction_name] = round(result[prediction_name], 2)
            return render_template(template, result=result)
        except requests.RequestException as e:
            return f"Error: {str(e)}", 500
    else:
        return "Error: Product ID or time period is missing", 400

@app.route('/price_prediction', methods=['GET', 'POST'])
def price_prediction():
    if request.method == 'POST':
        data = request.json
        return get_prediction('predict_price', data, 'price_prediction_result.html')
    else:
        return render_template('price_prediction_form.html')

@app.route('/demand_prediction', methods=['GET', 'POST'])
def demand_prediction():
    if request.method == 'POST':
        data = request.json
        return get_prediction('predict_demand', data, 'demand_prediction_result.html')
    else:
        return render_template('demand_prediction_form.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)