
import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from PyQt5.QtCore import QThread, pyqtSignal

def is_same_domain(url1, url2):
    return urlparse(url1).netloc == urlparse(url2).netloc

def is_url_allowed(url, filters=['#', '?']):
    return not any(char in url for char in filters)

def spider_domain_links(domain_url, output_csv='domain_crawl_results.csv', depth=None, filters=None):
    visited = set()
    to_visit = [(domain_url, 0)]

    while to_visit:
        current_url, current_depth = to_visit.pop(0)
        if current_url in visited or (depth is not None and current_depth > depth) or not is_url_allowed(current_url, filters):
            continue

        visited.add(current_url)
        print(f"Crawling: {current_url}")
        yield current_url

        try:
            response = requests.get(current_url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', href=True):
            href = urljoin(domain_url, link['href'])
            if href not in visited and is_same_domain(href, domain_url) and is_url_allowed(href, filters):
                to_visit.append((href, current_depth + 1))

    with open(output_csv, 'w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['URL'])
        for url in visited:
            writer.writerow([url])

class URLCrawlerThread(QThread):
    progress_signal = pyqtSignal(str)
    crawled_url_signal = pyqtSignal(str)

    def __init__(self, domain_url, output_csv, depth, filters):
        super().__init__()
        self.domain_url = domain_url
        self.output_csv = output_csv
        self.depth = depth
        self.filters = filters

    def run(self):
        self.progress_signal.emit("Starting domain crawling...")
        try:
            for url in spider_domain_links(self.domain_url, self.output_csv, self.depth, self.filters):
                self.crawled_url_signal.emit(url)
            self.progress_signal.emit(f"Domain crawling completed. Results saved to {self.output_csv}.")
        except Exception as e:
            self.progress_signal.emit(f"Error during domain crawling: {str(e)}")
