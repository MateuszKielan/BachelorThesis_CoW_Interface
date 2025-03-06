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
#-----------------------------

Window.maximize()

class StartingScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def select_file(self):
        filechooser.open_file(on_selection=self.select_store)
        
    def select_store(self, selection):
        if selection:
            file_path_name = str(Path(selection[0]).name)
            self.ids.file_path_label.text = file_path_name

    def switch(self, item=None):
        self.manager.current = "converter"

class ConverterScreen(Screen):
    pass


class CowApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(StartingScreen(name="start"))
        sm.add_widget(ConverterScreen(name="converter"))
        return sm
    
if __name__ == '__main__':
    CowApp().run()