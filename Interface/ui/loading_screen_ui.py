# This file contains main ui builder for the loading screen
# The main function can be found in main.py  (formulate better!)

#------IMPORTS SECTION-------

# Kivy UI imports
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

# KivyMD imports
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.label import MDLabel

#-----------------------------

def build_loading_screen_layout():
    """
    Function that creates the ui elements for the loading screen layout.

    Ui is constructed in the following way.
    - Screen is defined using FloatLayout.
        - Inside, vertical BoxLayout is used as a container for the elements
            - Inside the BoxLayout:
                - Spinner 
                - Label 
    """

    # Create a FloatLayout as the main container
    main_layout = FloatLayout()
    
    # Create a vertical box layout for the content
    content_layout = BoxLayout(
        orientation='vertical',
        spacing=30,
        padding=20,
        size_hint=(0.8, 0.5),
        pos_hint={'center_x': 0.5, 'center_y': 0.5}
    )
    
    # Add a spinning circle in the middle
    spinner = MDSpinner(
        size_hint=(None, None),
        size=(46, 46),
        pos_hint={'center_x': .5},
        active=True
    )
    
    # Add loading text
    loading_label = MDLabel(
        text="Loading... Processing your file and fetching recommendations",
        halign="center",
        theme_text_color="Primary",
        font_style="H5"
    )
    
    # Add widgets to content layout
    content_layout.add_widget(spinner)
    content_layout.add_widget(loading_label)
    
    # Add content layout to main layout
    main_layout.add_widget(content_layout)
    
    return main_layout
