from flask import Flask, request, jsonify
import os
import pandas as pd
import google.generativeai as genai
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from scrapy import signals
from scrapy.signalmanager import dispatcher
from scraper.scraper.spiders.AmazonScraping import AmazonSpider
from sentiment_analyzer import analyze_sentiment, get_pros_cons, get_summary
from multiprocessing import Process, Queue as MPQueue

app = Flask(__name__)

def run_spider(urls, results_queue):
    results = []

    def item_scraped(item, response, spider):
        print(f"Item scraped: {item}")
        results.append(item)

    def spider_closed(spider):
        print(f"Spider closed. Total items scraped: {len(results)}")
        df = pd.DataFrame(results)
        if df.empty:
            print("Warning: DataFrame is empty!")
        else:
            print(f"DataFrame info:\n{df.info()}")
        results_queue.put(df)

    process = CrawlerProcess(get_project_settings())
    dispatcher.connect(item_scraped, signal=signals.item_scraped)
    dispatcher.connect(spider_closed, signal=signals.spider_closed)

    try:
        process.crawl(AmazonSpider, start_urls=urls)
        process.start()
    except Exception as e:
        print(f"Error during crawling: {str(e)}")
        results_queue.put(pd.DataFrame())

def spider_process(urls, results_queue):
    run_spider(urls, results_queue)

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

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    result = process_request(url)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)