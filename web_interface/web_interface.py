from flask import Flask, render_template, request, jsonify
import socket
import json

app = Flask(__name__)

ML_SERVER_HOST = '127.0.0.1'
ML_SERVER_PORT = 5000


def get_insights(product_name):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((ML_SERVER_HOST, ML_SERVER_PORT))
            client.sendall(product_name.encode())
            response = client.recv(4096).decode()
        data = json.loads(response)

        # Format the data as HTML
        formatted_html = f"""
        <h2>Insights for {data['product']}</h2>
        <p>{data['summary']}</p>
        <p>
        <strong>Insights:</strong>
        <p><strong>Average rating: {data['avg_rating']}</strong></p>
        <p>Positive reviews: {data['positive_reviews']}</p>
        <p>Negative reviews: {data['negative_reviews']}</p>
        {data['pros_cons']}
        </p>
        """
        return formatted_html
    except ConnectionRefusedError:
        return "<p class='error'>Unable to connect to ML server. Is it running?</p>"
    except Exception as e:
        return f"<p class='error'>An error occurred: {str(e)}</p>"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_insights', methods=['POST'])
def insights():
    product_name = request.json['product_name']
    result = get_insights(product_name)
    return result  # Now returning HTML directly


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)