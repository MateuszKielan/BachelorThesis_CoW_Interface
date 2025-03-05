from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_file("kivy_app.kv")

class StartingScreen(BoxLayout):
    pass

class CowApp(App):
    def build(self):
        return StartingScreen()
    
if __name__ == '__main__':
    CowApp().run()