#------Imports Section-------
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.lang import Builder
from plyer import filechooser
#-----------------------------

class StartingScreen(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def select_file(self):
        filechooser.open_file(on_selection=self.select_store)

    def select_store(self, selection):
        print(selection)

class CowApp(App):
    def build(self):
        return StartingScreen()
    
if __name__ == '__main__':
    CowApp().run()