#------Imports Section-------
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.config import Config
from plyer import filechooser
from pathlib import Path
from screeninfo import get_monitors
from kivy.core.window import Window
from MockInterface.requests_t import get_csv_headers, get_recommendations
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

class ConverterScreen(Screen):
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
            recommendations = get_recommendations(headers, size)
            table.add_widget(Label(text=f'{header}', bold=True, color=(0, 0, 0, 1)))
            #table.add_widget(Label(text=f'{recommendations}', bold=True, color=(0,0,0,1)))


class CowApp(App):
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