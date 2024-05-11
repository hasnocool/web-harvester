from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QListWidget, QTabWidget, QApplication,
    QPushButton, QFileDialog, QTreeView, QMainWindow, QFrame, QLineEdit,
    QFormLayout, QMessageBox,
)
from PyQt5.QtCore import (
    QStandardPaths, QThread, pyqtSignal,
)
from PyQt5.QtGui import (
    QStandardItemModel, QStandardItem,
)
import os
import csv
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urlparse, urljoin

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
            self.progress_signal.emit(
                f"Domain crawling completed. Results saved to {self.output_csv}."
            )
        except Exception as e:
            self.progress_signal.emit(f"Error during domain crawling: {str(e)}")

def spider_domain_links(domain_url, output_csv="domain_crawl_results.csv", depth=None, filters=None):
    visited = set()
    to_visit = [(domain_url, 0)]

    while to_visit:
        current_url, current_depth = to_visit.pop(0)
        if (
            current_url in visited
            or (depth is not None and current_depth > depth)
            or not is_url_allowed(current_url, filters)
        ):
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

        soup = BeautifulSoup(response.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = urljoin(domain_url, link["href"])
            if (
                href not in visited
                and is_same_domain(href, domain_url)
                and is_url_allowed(href, filters)
            ):
                to_visit.append((href, current_depth + 1))

    with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["URL"])
        for url in visited:
            writer.writerow([url])

def is_same_domain(url1, url2):
    return urlparse(url1).netloc == urlparse(url2).netloc

def is_url_allowed(url, filters=["#", "?"]):
    return not any(char in url for char in filters)

class WebCrawlerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Crawler")
        self.setGeometry(100, 100, 600, 400)

        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        self.domain_input = QLineEdit()
        self.domain_input.setText("https://docs.trychroma.com/")
        form_layout.addRow("Domain URL:", self.domain_input)

        self.depth_input = QLineEdit()
        self.depth_input.setText("1")
        form_layout.addRow("Depth:", self.depth_input)

        self.filters_input = QLineEdit()
        self.filters_input.setText("#,?")
        form_layout.addRow("URL Filters:", self.filters_input)

        self.start_button = QPushButton("Start Crawling")
        self.start_button.clicked.connect(self.start_crawling)
        form_layout.addRow(self.start_button)

        self.stop_button = QPushButton("Stop Crawling")
        self.stop_button.clicked.connect(self.stop_crawling)
        form_layout.addRow(self.stop_button)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        main_layout.addWidget(self.console_output)
        main_layout.addLayout(form_layout)

        self.setLayout(main_layout)

    def start_crawling(self):
        domain_url = self.domain_input.text()
        depth = int(self.depth_input.text())
        filters = self.filters_input.text().split(",")
        output_csv = f"{urlparse(domain_url).netloc}_crawl_results_depth_{depth}.csv"
        self.crawler_thread = URLCrawlerThread(domain_url, output_csv, depth, filters)
        self.crawler_thread.progress_signal.connect(self.append_to_console)
        self.crawler_thread.crawled_url_signal.connect(self.append_to_console)
        self.crawler_thread.start()

    def stop_crawling(self):
        if hasattr(self, "crawler_thread") and self.crawler_thread is not None:
            self.crawler_thread.terminate()
            self.console_output.append("Crawling has been stopped.")

    def append_to_console(self, message):
        self.console_output.append(message)

class GetPagesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Get Pages")
        self.setGeometry(100, 100, 800, 600)

        self.parent_folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)

        self.currently_selected_file = None

        self.console_log = QTextEdit()
        self.console_log.setReadOnly(True)

        self.start_button = QPushButton("Start Parsing")
        self.start_button.clicked.connect(self.start_parsing)

        self.stop_button = QPushButton("Stop Parsing")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_parsing)

        layout = QVBoxLayout()
        layout.addWidget(self.console_log)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        self.setLayout(layout)

    def init_get_pages_tab(self):
        self.get_pages_layout = QVBoxLayout()

        self.csv_list_widget = QListWidget()
        self.csv_list_widget.itemClicked.connect(self.display_csv_content)

        self.populate_csv_list()

        self.csv_frame = QFrame()
        self.csv_frame.setLayout(self.get_pages_layout)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)

        self.start_button = QPushButton("Start Parsing")
        self.start_button.clicked.connect(self.start_parsing)

        self.stop_button = QPushButton("Stop Parsing")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_parsing)

        self.parent_folder_button = QPushButton("Select Parent Folder")
        self.parent_folder_button.clicked.connect(self.select_parent_folder)

        self.parent_folder_tree = QTreeView()
        self.parent_folder_model = QStandardItemModel()
        self.parent_folder_tree.setModel(self.parent_folder_model)

        self.update_parent_folder_tree()

        self.get_pages_layout.addWidget(self.csv_list_widget)
        self.get_pages_layout.addWidget(self.console_output)
        self.get_pages_layout.addWidget(self.start_button)
        self.get_pages_layout.addWidget(self.stop_button)
        self.get_pages_layout.addWidget(self.parent_folder_button)
        self.get_pages_layout.addWidget(self.parent_folder_tree)

        self.get_pages_tab.setLayout(self.csv_frame.layout())

    def populate_csv_list(self):
        self.csv_list_widget.clear()
        for folder in os.listdir(self.parent_folder):
            folder_path = os.path.join(self.parent_folder, folder)
            if os.path.isdir(folder_path) and folder.endswith("_output"):
                for file in os.listdir(folder_path):
                    if file.endswith(".csv"):
                        self.csv_list_widget.addItem(os.path.join(folder, file))

    def update_parent_folder_tree(self):
        self.parent_folder_model.clear()
        root_item = self.parent_folder_model.invisibleRootItem()
        self.populate_folder(root_item, self.parent_folder)

    def populate_folder(self, parent, folder):
        folder_item = QStandardItem(folder)
        parent.appendRow(folder_item)
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            if os.path.isdir(item_path):
                self.populate_folder(folder_item, item_path)

    def select_parent_folder(self):
        folder = str(
            QFileDialog.getExistingDirectory(
                self, "Select Parent Folder", self.parent_folder
            )
        )
        if folder:
            self.parent_folder = folder
            self.update_parent_folder_tree()
            self.populate_csv_list()

    def select_csv_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select CSV File", self.parent_folder, "All Files (*);;CSV Files (*.csv)", options=options)
        if fileName:
            self.currently_selected_file = fileName
            self.console_log.append(f"CSV file selected: {self.currently_selected_file}")
        else:
            self.console_log.append("No CSV file selected.")

    def display_csv_content(self, item):
        selected_file = os.path.join(self.parent_folder, item.text())
        with open(selected_file, "r", encoding="utf-8") as file:
            content = file.read()
            self.console_output.setText(content)

    def start_parsing(self):
        if self.currently_selected_file is None or not os.path.isfile(self.currently_selected_file):
            QMessageBox.warning(self, "File Not Selected", "Please select a CSV file to start parsing.")
            self.select_csv_file()
            if not self.currently_selected_file:
                return

        self.console_log.append("Starting parsing...")

        output_folder = f"{os.path.splitext(self.currently_selected_file)[0]}_output"
        os.makedirs(output_folder, exist_ok=True)

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        with open(self.currently_selected_file, "r", encoding="utf-8") as csvfile:
            csv_reader = csv.reader(csvfile)
            for i, row in enumerate(csv_reader):
                url = row[0]
                markdown_content = self.fetch_and_parse_url(url)
                markdown_filename = os.path.join(output_folder, f"page_{i+1}.md")
                with open(markdown_filename, "w", encoding="utf-8") as mdfile:
                    mdfile.write(markdown_content)
                self.console_log.append(f"Processed and saved {markdown_filename}")
                self.console_log.ensureCursorVisible()

    def stop_parsing(self):
        self.console_log.append("Parsing stopped by user.")
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)

    def fetch_and_parse_url(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")
            markdown_text = md(str(soup), heading_style="ATX")
            return markdown_text
        except requests.exceptions.RequestException as e:
            return f"Error fetching URL: {e}"

if __name__ == "__main__":
    app = QApplication([])
    window = GetPagesWindow()
    window.show()
    app.exec_()


#REFACTOR THIS AND SHOW ME THE ENTIRE SCRIPT WITH ALL CODE IMPLEMENTED
#CHANGE THE THE GET PAGES LOG TO DISPLAY THE SAME WAY THE WEB CRAWLER, 