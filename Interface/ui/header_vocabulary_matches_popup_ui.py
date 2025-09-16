# This file contains builder functions to the main UI components of the HeaderVocabularyMatchesPopup class.
# The aformentioned class implments the popup window that displays all the matches for each of the csv headers when clicking on the corresponding card in Vocabulary Recommender part of the interfaces

#------ IMPORTS SECTION -------


# Kivy UI Imports
from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

# Kivymd Imports
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.button import MDRaisedButton

# Custom Imports
from ..core.metadata import insert_instance

#-----------------------------


def builder_vocabulary_matches_layout(header: str, organized_data: list, best_match_data: list, list_titles: list, on_row_checked):
    """
    Function builder_vocabulary_matches_table that builds the table with vocabulary matches for every header.
    
     Args:
        header (str): current header
        organized_data (list): list of matches for the header
        list_titles (list): list of titles for the output table columns
        request_results (list): list of tuples of the headers and indexes of the best match
        rec_mode (str): mode of display (Single or Homogenous)
    """
    ui_root = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(1, 1))

    # Cover the case when no matches found
    if not organized_data or len(organized_data) == 0:
            empty_label = Label(
                text='NO Matches found',
                color=(1,1,1,1),
                font_size='40sp',
                size_hint_y=0.05,
            )
            ui_root.add_widget(empty_label)
            return  ui_root                 # Return early to prevent empty table creation later

    # Label for best match
    best_match_label = Label(
            text=f'Best match for {header}:', 
            color=(1, 1, 1, 1), 
            font_size='20sp',
            size_hint_y=0.05
        )

    # Create the best match table according to the data passed as arguments
    best_match_table = MDDataTable(
            column_data=list_titles,
            row_data=best_match_data,
            size_hint= (0.6, 0.1),
            pos_hint={"center_x": 0.5, "center_y": 0.6},
            use_pagination = False,
            check = True,
        )

    # Spacing Widget
    spacing_widget = Widget(
        size_hint_y=None,
        height=20
    )

    # Label for all matches
    all_match_label = Label(
        text=f'List of all matches:', 
        color=(1, 1, 1, 1), 
        font_size='20sp', 
        size_hint_y=0.05
    )

    # Create the table for all matches
    all_match_table = MDDataTable(
        column_data=list_titles,
        row_data=organized_data,
        size_hint=(0.6, 0.3),
        pos_hint={"center_x": 0.5, "center_y": 0.3},
        use_pagination=True,
        check=True,
        rows_num=20
    )

    # Bind the insert functionality to every row of both tables 
    all_match_table.bind(on_check_press=on_row_checked)
    best_match_table.bind(on_check_press=on_row_checked)

    # Add all the elements to the final widget
    ui_root.add_widget(best_match_label)
    ui_root.add_widget(best_match_table)
    ui_root.add_widget(spacing_widget)
    ui_root.add_widget(all_match_label)
    ui_root.add_widget(all_match_table)

    return ui_root


def builder_recommendation_action_menu(instance_table: MDDataTable, instance_row: list, header: str, selected_file):
    """
    Builder function that creates the ui for action menu where user can insert the metadata of the required header.

    Args:
        instance_table (MDDataTable): table data
        instance_row (list): row data

    """
    ui_root = BoxLayout(orientation='vertical', size_hint= (1,1))
    print(f"Data Received - {instance_row}")

    def insert_instance_wrapper(x):
        Clock.schedule_once(lambda dt: insert_instance(instance_row, header, selected_file))

    # Create a button to insert the chosen match
    button_insert = MDRaisedButton(
        text="Insert", 
        on_press=insert_instance_wrapper, # Use clocking to avoid error when conflicting with loading screen
        size_hint=(None, None),
        pos_hint={"center_x":0.5, "y": 0.6}                                        
    )
    
    # Add the button to the widget
    ui_root.add_widget(button_insert)

    # Ininitialize the popup window
    insert_popup = Popup(
        title = "Select Action",
        size_hint=(None, None),
        size=(500, 300),
        auto_dismiss=True,
        content = ui_root
    )

    return insert_popup
    