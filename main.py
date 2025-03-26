import asyncio
import sys
from scraper_gui import ScraperGUI
from scraper import AsyncScraper
from PyQt6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    gui = ScraperGUI()
    gui.show()
    app.exec()
    
    inputs = gui.get_inputs()
    
    scraper = AsyncScraper(
        start_url=inputs['start_url'],
        sql_column=inputs['sql_variable'],
        html_element=inputs['html_element'],
        class_id=inputs['class_id'] or ''
    )
    
    asyncio.run(scraper.run())

if __name__ == "__main__":
    main()