import sys

import pandas as pd
import json

import socket
from threading import Thread
from multiprocessing import Process, Queue as MPQueue

data_file_mapping = {
    'super_market_sales': './data/supermarket-sales-data/annex3.csv'
}

data_column_names = {
    'super_market_sales': {'Date': 'ds', 'Wholesale Price (RMB/kg)': 'y'}
}

def rename_dataset_columns(data, data_name):
    # Rename columns for Prophet
    data = data.rename(columns=data_column_names[data_name])
    return data

def load_data(data_name='super_market_sales'):
    # Load the requested dataset
    try:
        file_path = data_file_mapping[data_name]
        data = pd.read_csv(file_path)
    except KeyError:
        sys.stderr.write("Error: Dataset meta data is missing!\n")
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{file_path}' is empty.")

    # Rename columns for Prophet
    data = rename_dataset_columns(data, data_name='super_market_sales')

    # Convert the 'ds' column to datetime
    data['ds'] = pd.to_datetime(data['ds'])

    return data


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

def handle_client(client_socket):
    request = client_socket.recv(1024).decode()
    print(f"Received request: {request}")

    result = process_request(request)

    client_socket.send(json.dumps(result).encode())
    client_socket.close()

def process_request(request):
    urls = [request]
    results_queue = MPQueue()

    p = Process(target=spider_process, args=(urls, results_queue))
    p.start()
    data = results_queue.get()
    p.join()

    print(data.info())
    print(data.head(5))

    if data.empty:
        print("Warning: Scraped data is empty!")
        return {
            "product": request,
            "error": "No data was scraped. Please check the URL and try again."
        }

    if data.empty:
        print("Warning: Scraped data is empty!")
        return {
            "product": request,
            "error": "No data was scraped. Please check the URL and try again."
        }

    sentiment_result = analyze_sentiment(data)
    genai.configure(api_key=os.environ['GENAI_API_KEY'])
    pros, cons, summary = get_pros_cons(sentiment_result)
    positive_reviews = sum(sentiment_result['predicted_rating'] == 1)
    negative_reviews = sum(sentiment_result['predicted_rating'] == 0)

    product = data['product'][0]
    price = data['price'][0]
    avg_rating = data['avg_rating'][0]

    return {
        "product": product,
        "price": price,
        "pros": pros,
        "cons": cons,
        "summary": summary,
        "avg_rating": avg_rating,
        "positive_reviews": positive_reviews,
        "negative_reviews": negative_reviews,
    }

if __name__ == "__main__":
    start_server()