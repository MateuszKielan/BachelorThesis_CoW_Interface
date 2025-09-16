# This file contains the UI builder functions for the ConverterScreen class in main.py.

# ------ Imports Section ------

# Kivy UI Imports
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

# Kivymd Imports
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton

# ------ Functions Section ------

def builder_request_help_popup(help_text: str) -> Popup:
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


def builder_recommended_terms_popup(title, content):

    # Initialize the popup window
    popupWindow = Popup(
        title=title, 
        content=content, 
        size_hint=(1,1)
    )

    return popupWindow


def builder_vocabulary_card(vocabulary_match_scores, on_press_callback=None):

    vocab_card = MDCard(
        orientation='vertical',
        size_hint=(0.85, None),
        pos_hint={"center_x": 0.5},
        height=160,
        padding=10,
        spacing=10,
        ripple_behavior=True,
        md_bg_color=(0.95, 0.95, 0.95, 1),
        shadow_softness=1,
        elevation=4,
        )

    vocab_card.add_widget(MDLabel(
        text=f"[b]Vocabulary Scores[/b]",
        markup=True,
        theme_text_color="Primary",
        font_style="Subtitle1",
        size_hint_y=None,
        height=30
        ))
    

    vocab_card.add_widget(MDLabel(
        text=f"Vocabularies: {len(vocabulary_match_scores)}",
        theme_text_color="Secondary",
        size_hint_y=None,
        height=24
        ))

    # Create the button with the callback
    button = MDRaisedButton(
        text="Show Scores",
        size_hint=(None, None),
        size=(150, 40),
        pos_hint={"center_x": 0.5}
    )
    
    # Set the callback if provided
    if on_press_callback:
        button.bind(on_press=on_press_callback)
    
    vocab_card.add_widget(button)

    return vocab_card

def builder_header_card(header, number_of_matches, dtype, on_press_callback):
    header_card = MDCard(
        orientation='vertical',
        size_hint=(0.85, None),
        pos_hint={"center_x": 0.5},
        height=160,
        padding=10,
        spacing=10,
        ripple_behavior=True,
        md_bg_color=(0.95, 0.95, 0.95, 1),
        shadow_softness=1,
        elevation=4,
    )

    header_card.add_widget(MDLabel(
        text=f"[b]Header:[/b] {header}",
        markup=True,
        theme_text_color="Primary",
        font_style="Subtitle1",
        size_hint_y=None,
        height=30
    ))

    header_card.add_widget(MDLabel(
        text=f"Type: {dtype}  |  Matches: {number_of_matches}",
        theme_text_color="Secondary",
        size_hint_y=None,
        height=24
    ))

    button = MDRaisedButton(
        text="Show Matches",
        size_hint=(None, None),
        size=(150, 40),
        pos_hint={"center_x": 0.5},
    )

    # Set the callback if provided
    if on_press_callback:
        button.bind(on_press=on_press_callback)
    
    header_card.add_widget(button)

    return header_card