import os

import google.generativeai as genai
import socket
import json
from threading import Thread
from sentiment_analyzer import analyze_sentiment, get_pros_cons, get_summary, download_and_extract_data


def handle_client(client_socket):
    request = client_socket.recv(1024).decode()
    print(f"Received request: {request}")

    # TODO: Replace this with your actual ML and scraping logic
    url = "https://storage.googleapis.com/kaggle-data-sets/4667471/7939164/bundle/archive.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20240914%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20240914T070040Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=90df2d0acad0c10011e7fefbe5983ee156a3ac5dcadb29b7e0666fe8dac1d3d285869b49608305db64677e560ff1c9b421fbddc4522ee1e5b024034493ab20b4d33ab9a5f0343339876d6046f70066475983271ab28ef0c74da8328da98b93271236c11b90d77b6a29face215d0e3fb63757c369490955a3c1305686bde0f877b2f135d198dc35a0c31cda39677251a2626d45ab624bce1cc1b3ad798cbaf7c895cb947ec3e5bf93ee91e58b210ffc162ada9ef2002166f35b52323c73b78b2e778cbb6b9cb6632f47e57edcc6cd185348ecf733841e607a8aebce9f60f9817582697282dae1bbe4147291585185c784d685fbdce85a0a976455350b8eba6f91"
    data = download_and_extract_data(url,"Amazon-Product-Reviews - Amazon Product Review (1).csv")

    sentiment_result = analyze_sentiment(data)

    # Connect to Gemini API
    genai.configure(api_key=os.environ['GENAI_API_KEY'])
    pros_cons = get_pros_cons(sentiment_result)
    summary = get_summary('TEST SUMMARY')
    positive_reviews = sum(sentiment_result['sentiment'] == 1)
    negative_reviews = sum(sentiment_result['sentiment'] == 0)

    result = {
        "product": request,
        "pros_cons": pros_cons,
        "summary": summary,
        "avg_rating": 5.0,
        "positive_reviews": positive_reviews,
        "negative_reviews": negative_reviews,
    }

    client_socket.send(json.dumps(result).encode())
    client_socket.close()


def start_server(host='0.0.0.0', port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"[*] Listening on {host}:{port}")

    while True:
        client, addr = server.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = Thread(target=handle_client, args=(client,))
        client_handler.start()


if __name__ == "__main__":
    start_server()