from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from get_pages import GetPagesWindow
from web_crawler import WebCrawlerWindow

def main():
    app = QApplication([])
    mainWindow = QMainWindow()
    tabWidget = QTabWidget()

    webCrawlerWidget = WebCrawlerWindow()
    getPagesWidget = GetPagesWindow()

    tabWidget.addTab(webCrawlerWidget, "Web Crawler")
    tabWidget.addTab(getPagesWidget, "Get Pages")

    mainWindow.setCentralWidget(tabWidget)
    mainWindow.setWindowTitle('Web Crawler and Get Pages')
    mainWindow.setGeometry(100, 100, 800, 600)

    mainWindow.show()
    app.exec_()

if __name__ == '__main__':
    main()


