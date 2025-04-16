#------Imports Section-------
from kivymd.app import MDApp
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.lang import Builder
from kivy.config import Config
from plyer import filechooser
from pathlib import Path
from screeninfo import get_monitors
from kivy.core.window import Window
from requests_t import get_csv_headers, get_recommendations, organize_results, get_vocabs, get_average_score, combiSQORE, retrieve_combiSQORE  # My implementation of single / homogenous requests
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
import csv
import subprocess
from cow_csvw.converter.csvw import build_schema
#-----------------------------

# Set the adaptive fullScreen mode
Window.maximize()

class StartingScreen(Screen):
    """
    Class StartingScreen that implements logic begind Starting Screen
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


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



class DataPopup(FloatLayout):
    """
    Class DataPopup that defines a popup page that displays full csv data table
    """


    def __init__(self, column_heads, row_data, **kwargs):
        super().__init__(**kwargs)
        self.build_table(column_heads, row_data)


    def build_table(self, column_heads, row_data):
        """
        Function build_table that builds the table for the whole dataset.

        Params:
            column_heads(arr): list of headers
            row_data(arr): list of data row by row
        """

        # Define the table
        table = MDDataTable(
            column_data=column_heads,
            row_data=row_data,
            size_hint=(0.98, 0.85),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            use_pagination=True,
            rows_num=20
        )

        # Clear the previous table on launch and add the new table to the widget
        self.ids.popup_data_container.clear_widgets()
        self.ids.popup_data_container.add_widget(table)


    def dismiss_popup(self):
        """
        Function dismiss_popup that closes the popup.
        """
        parent = self.parent
        while parent:
            if isinstance(parent, Popup):
                parent.dismiss()
                break
            parent = parent.parent



class RecommendationPopup(FloatLayout):
    """
    Class RecommendationPopup that implements the logic behind Recommendation popups for every header 
    """


    def __init__(self, header, organized_data, list_titles, request_results, rec_mode, **kwargs):
        super().__init__(**kwargs)
        self.build_table(header, organized_data, list_titles, request_results,rec_mode)


    def build_table(self, header, organized_data, list_titles, request_results, rec_mode):
        """
        Function build_table that builds the table for every header.

        Params:
            header (str): current header
            organized_data (list): list of matches for the header
            list_titles (list): list of titles for the output table columns
            request_results (list): list of tuples of the headers and indexes of the best match
            rec_mode (str): mode of display (Single or Homogenous)

        """
        # Clear all  previous widgets
        self.ids.popup_recommendations.clear_widgets()

        index = [item[1] for item in request_results if item[0] == header]
        best_match_data = [organized_data[index[0]]]

        # Display the best_table according to mode 
        if rec_mode == 'Homogenous':
            best_table = MDDataTable(
                column_data = list_titles,
                row_data= best_match_data,
                size_hint=(1, 0.2),
                pos_hint={"center_x": 0.5, "center_y": 0.6},
                use_pagination=False,
            )
        elif rec_mode == 'Single':
            best_table = MDDataTable(
                column_data = list_titles,
                row_data= [organized_data[0]],
                size_hint=(1, 0.2),
                pos_hint={"center_x": 0.5, "center_y": 0.6},
                use_pagination=False,
            )

        # Define the table of Matches
        table = MDDataTable(
            column_data=list_titles,
            row_data=organized_data,
            size_hint=(1, 0.6),
            pos_hint={"center_x": 0.5, "center_y": 0.3},
            use_pagination=True,
            rows_num=20
        )

        # Add the new tables to the widget with Labels
        self.ids.popup_recommendations.add_widget(Label(text=f'Best match for {header}:', color=(1, 1, 1, 1), font_size='20sp', size_hint_y=0.05))
        self.ids.popup_recommendations.add_widget(best_table)
        self.ids.popup_recommendations.add_widget(Widget(size_hint_y=None, height=20)) # Create spacing Widget
        self.ids.popup_recommendations.add_widget(Label(text=f'List of all matches:', color=(1, 1, 1, 1), font_size='20sp', size_hint_y=0.05))
        self.ids.popup_recommendations.add_widget(table)


    def dismiss_popup(self):
        """
        Function dismiss_popup that closes the popup window
        """
        parent = self.parent

        # Search for the lowest parent
        while parent:
            if isinstance(parent, Popup):
                parent.dismiss()
                break
            parent = parent.parent



class ConverterScreen(Screen):
    """
    Class ConverterScreen that implements logic behind the conversion layout
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rec_mode = "Homogenous"  # Changing in the switch_mode function

    def convert_with_cow(self, csv_path):
        """
        Function convert_with_cow that takes the CSV file and creates a JSON metadata
        
        Params:
            csv_path (str): path to the input file
        
        Function utilizes build_schema from cow_csvw
        """
        input_path = Path(csv_path)
        output_metadata_path = input_path.parent / "metadata.json"

        try:
            build_schema(str(input_path), str(output_metadata_path))
        except Exception as e:
            pass

    def show_popup(self, column_heads, row_data):
        """
        Function show_popup that calls the DataPopup class to display the table 

        Params:
            column_heads(arr): list of headers
            row_data(arr): list of data row by row

        Those parameters are only needed to pass it further to the DataPopup screen
        """

        # Pass the data to the popup
        show = DataPopup(column_heads, row_data)

        # Initialize and open window
        popupWindow = Popup(title="CSV Data", content=show, size_hint=(1, 1))
        popupWindow.open()
    

    def open_recommendations(self,header, data, list_titles, request_results):
        """
        Function open recommendations that opens a recommendation popup.

        Params:
            header(str): name of the csv header
            data(arr): list of data for the  
            list_titles(arr): list of table headers
        """
        # Pass the data to the popup
        show = RecommendationPopup(header,data, list_titles, request_results, self.rec_mode)

        # Initialize and open window
        popupWindow = Popup(title=f'Matches for {header}', content=show,size_hint=(1,1))
        popupWindow.open()

    def switch_mode(self, choice, headers, all_results, table):
        """
        Function switch_mode
        """
        self.rec_mode = choice
        self.create_header_buttons(headers, all_results, table)

    def create_header_buttons(self, headers, all_results, table):
        table.clear_widgets()
        table.add_widget(Widget(size_hint_y=None, height=40))
        for header in headers:
            data = all_results[header]
            table.add_widget(Button(text=f'{header}', on_press=lambda x, h=header, d=data: self.open_recommendations(h, d, self.list_titles, self.request_results), bold=True, color=(1, 1, 1, 1), size_hint=(None, None),pos_hint={"x": 0.5}, size=(120, 80),))

    def display_recommendation(self, file_path):
        """
        Function display_recommnedation:
            1. Retreitves the recommendation from the input csv.
            2. Displays the headers on the middle page.
            3. Displays the recommendations on the middle page.
        """
        
        self.selected_file = file_path
        self.convert_with_cow(file_path)

        headers = get_csv_headers(file_path)
        size = 20

        table = self.ids.vocab_recommender

        all_results = {}

        # List of titles with spacings
        self.list_titles = [
            ('prefixedName', dp(60)), 
            ('vocabulary.prefix', dp(60)), 
            ('uri',dp(60)),
            ('type',dp(60)), 
            ('score',dp(60))
        ]

        for header in headers:
            recommendations = get_recommendations(header, size)
            organized_data = organize_results(recommendations)
            all_results[header] = organized_data
        
        vocabs = get_vocabs(all_results)
        scores = get_average_score(vocabs, all_results)
        combi_vocabs = combiSQORE(all_results, scores)

        best_combi_vocab = combi_vocabs[0][0]

        self.request_results = retrieve_combiSQORE(best_combi_vocab, all_results)
        
        self.create_header_buttons(headers, all_results, table)

        # Load CSV data for table
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)
            if not rows:
                return

        # Seperate headers and row data
        column_heads = [(header, dp(25)) for header in rows[0]]
        table_rows = rows[1:11] 
        row_data = rows [1:]

        # Remove old tables
        if hasattr(self, 'csv_table'):
            self.remove_widget(self.csv_table)

        # Create MDDataTable
        self.csv_table = MDDataTable(
            column_data=column_heads,
            row_data=table_rows,
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            use_pagination=True,
            rows_num = 10
        )

        self.ids.request_option_panel.add_widget(Button(text='Single', on_press=lambda x: self.switch_mode('Single', headers, all_results, table), color=(1, 1, 1, 1)))
        self.ids.request_option_panel.add_widget(Button(text='Homogenous',on_press=lambda x: self.switch_mode('Homogenous', headers, all_results, table), color=(1, 1, 1, 1)))
    
        self.ids.csv_preview_container.clear_widgets()
        self.ids.csv_preview_container.add_widget(self.csv_table)

        open_popup = Button(text='Load Full Dataset', on_press=lambda x: self.show_popup(column_heads,row_data), size_hint=(None,None), size=(200,50), pos_hint={"center_x": 0.5})
        self.ids.csv_preview_container.add_widget(open_popup)



class CowApp(MDApp):
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