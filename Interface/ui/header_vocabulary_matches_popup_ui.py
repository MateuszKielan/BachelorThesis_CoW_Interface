# This file contains builder functions to the main UI components of the HeaderVocabularyMatchesPopup class.
# The aformentioned class implments the popup window that displays all the matches for each of the csv headers when clicking on the corresponding card in Vocabulary Recommender part of the interfaces

#------ IMPORTS SECTION -------

# Kivy UI Imports
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout

# Kivymd Imports

from kivymd.uix.datatables import MDDataTable

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
                font_size='20sp',
                size_hint_y=0.05,
            )
            ui_root.add_widget(empty_label)
            return  ui_root                                  # Return early to prevent empty table creation later

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

    # LAbel for all matches
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