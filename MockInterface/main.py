#------Imports Section-------
from kivymd.app import MDApp
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.config import Config
from plyer import filechooser
from pathlib import Path
from screeninfo import get_monitors
from kivy.core.window import Window
from requests_t import get_csv_headers, get_recommendations
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
import csv
#-----------------------------

# Set the adaptive fullScreen mode
Window.maximize()

class StartingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        selected_file = ''

    def select_file(self):
        """
        Function select_file that opens filechooser.
        """
        filechooser.open_file(on_selection=self.select_store)
        
    def select_store(self, selection):
        """
        Function selct_store that: 
            1. Stores the selected file path.
            2. Updates the file name label.
        Params:
            selection (arr): array of length 1 with a selected file
        """
        if selection:
            self.selected_file = str(Path(selection[0]))
            file_path_name = str(Path(selection[0]).name)
            self.ids.file_path_label.text = file_path_name

    def switch(self):
        """
        Function switch that 
            1. Switches the screen to converter_screen
            2. Passes the file path to the converter_screen
        """
        converter_screen = self.manager.get_screen("converter")
        converter_screen.display_recommendation(self.selected_file)
        self.manager.current = "converter"

class DataPopup(FloatLayout):
    """
    Class DataPopup that defines a popup page that displays full csv data table
    """
    
        
class ConverterScreen(Screen):
    def show_popup(self):
        show = DataPopup()

        popupWindow = Popup(title="CSV Data", content=show, size_hint=(1, 1))

        popupWindow.open()
    
    def display_recommendation(self, file_path):
        """
        Function display_recommnedation:
            1. Retreitves the recommendation from the input csv.
            2. Displays the headers on the middle page.
            3. Displays the recommendations on the middle page.
        """
        headers = get_csv_headers(file_path)
        size = 1

        table = self.ids.vocab_recommender
        for header in headers:
            recommendations = get_recommendations(header, size)
            table.add_widget(Label(text=f'{header}', bold=True, color=(0, 0, 0, 1)))
            #table.add_widget(Label(text=f'{recommendations}', bold=True, color=(0,0,0,1)))

        # Load CSV data for table
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            if not rows:
                return

        # Seperate headers and row data
        column_heads = [(header, dp(25)) for header in rows[0]]
        print(column_heads)
        table_rows = rows[1:11] 

        # Remove old tabless
        if hasattr(self, 'csv_table'):
            self.remove_widget(self.csv_table)

        # Create MDDataTable
        self.csv_table = MDDataTable(
            column_data=column_heads,
            row_data=table_rows,
            size_hint=(0.90, 0.80),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )

        # Add table to left section
        self.ids.csv_preview_container.clear_widgets()
        self.ids.csv_preview_container.add_widget(self.csv_table)

class CowApp(MDApp):
    def build(self):
        """
        Build app function that runs the Screen Manager.
        """
        sm = ScreenManager()
        sm.add_widget(StartingScreen(name="start"))
        sm.add_widget(ConverterScreen(name="converter"))
        return sm
    
if __name__ == '__main__':
    CowApp().run()