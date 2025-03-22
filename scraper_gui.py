from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGroupBox, QWidget,
    QLabel, QSpacerItem, QSizePolicy, QMessageBox
)
from PyQt6.QtCore import Qt, QSize

class ScraperGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.inputs = {
            'start_url': '',
            'sql_variable': '',
            'html_element': '',
            'class_id': ''
        }
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Chad Scraper")
        self.setMinimumSize(QSize(800, 600))
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        input_group = QGroupBox("Scraping Parameters")
        input_layout = QVBoxLayout()
        
        fields = [
            ("Starting URL:", QLineEdit(), 'start_url'),
            ("SQL Column Name:", QLineEdit(), 'sql_variable'),
            ("HTML Element:", QLineEdit(), 'html_element'),
            ("Class ID:", QLineEdit(), 'class_id')
        ]
        
        for label_text, field, key in fields:
            hbox = QHBoxLayout()
            hbox.addWidget(QLabel(label_text))

            ## Jebo sam mu mater u usta smrdljiva dok sam nasao ovu smrdljivu gresku sa textChanged mrs u kurac
            field.textChanged.connect(lambda text, k=key: self.update_input(k, text))
            hbox.addWidget(field)
            input_layout.addLayout(hbox)
            setattr(self, f'input_{key}', field)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        self.submit_btn = QPushButton("Start Scraping")
        self.submit_btn.setFixedSize(200, 40)
        self.submit_btn.clicked.connect(self.validate_inputs)
        main_layout.addWidget(self.submit_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        self.input_start_url.setPlaceholderText("https://books.toscrape.com")
        self.input_sql_variable.setPlaceholderText("price")
        self.input_html_element.setPlaceholderText("p")
        self.input_class_id.setPlaceholderText("price_color")

    def update_input(self, key, text):
        self.inputs[key] = text.strip()

    def validate_inputs(self):
        if all(self.inputs.values()):
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Please fill all fields!")

    def get_inputs(self):
        return self.inputs