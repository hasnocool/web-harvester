
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, QFormLayout
from urllib.parse import urlparse
from utils import URLCrawlerThread

class WebCrawlerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Web Crawler')
        self.setGeometry(100, 100, 600, 400)

        mainLayout = QVBoxLayout()
        formLayout = QFormLayout()

        self.domain_input = QLineEdit()
        self.domain_input.setText("https://docs.trychroma.com/")
        formLayout.addRow("Domain URL:", self.domain_input)

        self.depth_input = QLineEdit()
        self.depth_input.setText("1")
        formLayout.addRow("Depth:", self.depth_input)

        self.filters_input = QLineEdit()
        self.filters_input.setText("#,?")
        formLayout.addRow("URL Filters:", self.filters_input)

        self.start_button = QPushButton('Start Crawling')
        self.start_button.clicked.connect(self.start_crawling)
        formLayout.addRow(self.start_button)

        self.stop_button = QPushButton('Stop Crawling')
        self.stop_button.clicked.connect(self.stop_crawling)
        formLayout.addRow(self.stop_button)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        mainLayout.addWidget(self.console_output)
        mainLayout.addLayout(formLayout)

        self.setLayout(mainLayout)

    def start_crawling(self):
        domain_url = self.domain_input.text()
        depth = int(self.depth_input.text())
        filters = self.filters_input.text().split(',')
        output_csv = f"{urlparse(domain_url).netloc}_crawl_results_depth_{depth}.csv"
        self.crawler_thread = URLCrawlerThread(domain_url, output_csv, depth, filters)
        self.crawler_thread.progress_signal.connect(self.append_to_console)
        self.crawler_thread.crawled_url_signal.connect(self.append_to_console)
        self.crawler_thread.start()

    def stop_crawling(self):
        if hasattr(self, 'crawler_thread') and self.crawler_thread is not None:
            self.crawler_thread.terminate()
            self.console_output.append("Crawling has been stopped.")

    def append_to_console(self, message):
        self.console_output.append(message)
