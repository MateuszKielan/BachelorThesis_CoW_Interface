# This file contais the ui elements used for building the vocabulary score popup which corresponds to the first card displayed in the vocabulary recommender.

#------ IMPORTS SECTION -------
# Core Kivy Imports
from kivy.metrics import dp

# Kivy UI Imports
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

# Kivymd Imports
from kivymd.uix.datatables import MDDataTable
#-----------------------------

def builder_vocabulary_score_popup(vocabulary_scores, vocab_data):
    ui_root = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint=(1, 1))

    if not vocabulary_scores:
        empty_label = Label(
                text='No vocabulary data available',
                color=(1,1,1,1),
                font_size='20sp',
                size_hint_y=0.05
            )
        ui_root.add_widget(empty_label)
        return ui_root

    try:
        list_col_names = [
            ("vocabularies", dp(60)), 
            ("Average Match Score", dp(60)), 
            ("Number of Produced Matches", dp(60)),
            ("Combi Score", dp(60))
        ]

        vocabulary_data_table = MDDataTable(
            column_data=list_col_names,
            row_data=vocab_data,
            size_hint=(0.6, 0.3),
            pos_hint={"center_x": 0.5, "center_y": 0.3},
            use_pagination=True,
            check=False,  # Disable row selection to prevent crashes
            rows_num=20
        )

        ui_root.add_widget(vocabulary_data_table)

        return ui_root

    except Exception as e:
        error_label = Label(
                text='Error Loading Vocabualry Data',
                color=(1,1,1,1),
                font_size='20sp',
                size_hint_y=0.05
            )

        ui_root.add_widget(error_label)

        return ui_root