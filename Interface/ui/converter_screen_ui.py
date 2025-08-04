# This file contains the UI builder functions for the ConverterScreen class in main.py.

# ------ Imports Section ------
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

# ------ Functions Section ------

def build_request_help_popup(help_text: str) -> Popup:
    """
    Function build_request_help_popup that builds the request help popup.

    Args:
        help_text (str): The text to display in the popup.

    Returns:
        Popup: The popup object.
    """

    # Create a box layout for the helper content
    content = BoxLayout(orientation='vertical')

    # Bind the text to the Label + Set up basic parameters
    label = Label(
        text=help_text,
        markup=True,
        halign="left",
        valign="middle",
        text_size=(400, None),
        size_hint_y=None,
    )
    # Bind the texture size to the label
    label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))

    # Add the ScrollView property to make the popup more responsive
    scroll = ScrollView(size_hint=(1, 1)) # Adjust it for the full page
    scroll.add_widget(label)

    content.add_widget(scroll)

    # Initialize Popup
    popup = Popup(
        title="Help: Request Types",
        content=content,
        size_hint=(None, None),
        size=(500, 300),
        auto_dismiss=True,
    )

    return popup


def builder_recommendation_help_popup(help_text):
    """
    Function builder_recommendation_help_popup that builds recommendation window help popup
    
    Args:
        help_text: 
    """
    content = BoxLayout(orientation='vertical')

    # Bind text to the Label
    label = Label(
        text=help_text,
        markup=True,
        halign="left",
        valign="middle",
        text_size=(400, None),
        size_hint_y=None,
    )

    # Bind the texture size to the label
    label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))

    # Add Scroll ability for enhanced responsiveness
    scroll = ScrollView(size_hint=(1, 1))
    scroll.add_widget(label)

    # Add property to the main window
    content.add_widget(scroll)

    # Instantiate Popup
    popup = Popup(
        title="Help: Recommendations",
        content=content,
        size_hint=(None, None),
        size=(500, 300),
        auto_dismiss=True,
    )

    return popup


def builder_vocabulary_popup(title, content):

    # Initialize the popup window
    popupWindow = Popup(
        title=title, 
        content=content, 
        size_hint=(1,1)
    )

    return popupWindow