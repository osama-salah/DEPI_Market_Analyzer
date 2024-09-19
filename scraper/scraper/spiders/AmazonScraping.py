from time import sleep

import scrapy
from scrapy.http import Response
from scrapy.exceptions import CloseSpider
from scraper_p.scraper.scraper.items import AmazonscrapItem
import re
import random
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

from scrapy_selenium import SeleniumRequest


class CustomRetryMiddleware(RetryMiddleware):
    def process_response(self, request, response, spider):
        if response.status in [503, 403, 500]:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        return response


class AmazonSpider(scrapy.Spider):
    name = 'amazon_spider'

    custom_settings = {
        'DOWNLOAD_DELAY': 2,  # 2 seconds of delay
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'scraper_p.scraper_p.scraper_p.spiders.AmazonScraping.CustomRetryMiddleware': 550,
        },
        'RETRY_TIMES': 10,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
    }

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    ]

    def __init__(self, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        self.start_urls = kwargs.get('start_urls', '')
        print('urls:',self.start_urls)
        if not self.start_urls or self.start_urls == ['']:
            raise CloseSpider('No URLs provided. Please provide at least one URL to scrape.')

    def start_requests(self):
        for url in self.start_urls:
            if url.strip():
                # yield scrapy.Request(
                #     url=url.strip(),
                #     callback=self.parse,
                #     headers={'User-Agent': random.choice(self.user_agents)}
                # )
                yield SeleniumRequest(
                    url=url.strip(),
                    callback=self.parse,
                    wait_time=3,
                    headers={'User-Agent': random.choice(self.user_agents)}
                )
                sleep(random.uniform(5, 15))  # Random delay between 5-15 seconds

    def parse(self, response: Response):
        if response.status in [503, 403, 500]:
            self.logger.error(f"Received {response.status} for URL: {response.url}")
            return

        # Extracting the product name and price
        product = response.css('#productTitle::text').get()
        price = response.css('.a-price .a-price-whole::text').get()

        # Extract each review block
        review_blocks = response.css('.review')

        if not review_blocks:
            self.logger.warning(f"No reviews found on page: {response.url}")

        # Loop through each review block and yield an individual item for each
        for review in review_blocks:
            items = AmazonscrapItem()

            review_body = review.css('.review-text-content span::text').get()
            review_rating = review.css('.review-rating span::text').get()

            # Extracting the "helpful" count
            helpful_text = review.css('.cr-vote-text::text').get()
            if helpful_text:
                helpful_votes = helpful_text.strip().split()[0]
                if helpful_votes.lower() == 'one':
                    helpful_votes = '1'
            else:
                helpful_votes = '0'  # Default if no helpful count is available

            # Fill in the item with data
            items['product'] = product.strip() if product else None
            items['price'] = price.strip() if price else None
            items['review_body'] = review_body.strip() if review_body else None

            # Extract only the numeric part of the rating
            if review_rating:
                rating_number = self.extract_rating_number(review_rating)
                items['ratings'] = float(rating_number)
            else:
                items['ratings'] = None

            items['helpful_votes'] = helpful_votes

            # Yield the item for each review
            yield items

        # Follow pagination if available
        next_page = response.css('li.a-last a::attr(href)').get()
        if next_page:
            yield scrapy.Request(
                url=response.urljoin(next_page),
                callback=self.parse,
                headers={'User-Agent': random.choice(self.user_agents)}
            )

    def extract_rating_number(self, rating_string: str) -> str:
        match = re.search(r'(\d+(\.\d+)?)', rating_string)
        if match:
            return match.group(1)
        return None