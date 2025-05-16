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
from requests_t import get_csv_headers, get_recommendations, organize_results, get_vocabs, get_average_score, calculate_combi_score, retrieve_combiSQORE_recursion  # My implementation of single / homogenous requests
from kivymd.uix.datatables import MDDataTable
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
import csv
import json
import logging
from cow_csvw.converter.csvw import build_schema, CSVWConverter
from utils import infer_column_type
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivy.clock import Clock
from shutil import copyfile
from kivy.uix.textinput import TextInput
import threading
#-----------------------------

# Set up the logger
logger = logging.getLogger(__name__)

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
        logger.info("Opening the file chooser")

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
            self.selected_file = Path(selection[0])
            file_path_name = str(Path(selection[0]).name)
            self.ids.file_path_label.text = file_path_name


    def switch(self):
        """
        Function switch that 
            1. Switches the screen to converter_screen
            2. Passes the file path to the converter_screen
        """
        logger.info("Switching to Converter Screen")

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
        self.ids.popup_recommendations.add_widget(Widget(size_hint_y=None, height=20))

        # Define the table
        table = MDDataTable(
            column_data=column_heads,
            row_data=row_data,
            size_hint=(0.9, 0.85),
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


    def __init__(self, header, organized_data, list_titles, request_results, rec_mode, selected_file, **kwargs):
        super().__init__(**kwargs)
        self.header = header
        self.selected_file = selected_file
        self.build_table(header, organized_data, list_titles, request_results, rec_mode)

    def insert_instance(self, table, row):
        """
        Inserts the selected match into the metadata for the current header.
        """
        def clean(text):
            return text.translate(str.maketrans('', '', "[]'"))

        # Parse and clean the row values
        name = clean(row[0])
        vocab = clean(row[1])
        uri = clean(row[2])
        rdf_type = clean(row[3])
        score = float(row[4])

        data_path = self.selected_file.parent / f"{self.selected_file.name[:-4]}-metadata.json"

        with open(data_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        updated = False
        for column in data.get('tableSchema', {}).get('columns', []):
            if column.get('header') == self.header:
                column.update({
                    'name': name,
                    '@id': uri,
                    'vocab': vocab,
                    'type': rdf_type,
                    'score': score
                })
                updated = True
                logger.info(f"[Inserted] {self.header} -> {name} ({vocab})")

        if not updated:
            logger.warning(f"Insert Failed: Header '{self.header}' not found in metadata.")

        with open(data_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
            logger.info(f"Metadata File Written: {data_path}")

        self.insert_popup.dismiss()
        # Refresh preview
        app = MDApp.get_running_app()
        app.root.get_screen("converter").show_json()
        logger.info("Refreshed JSON Preview Screen")



    def show_recommendation_action_menu(self, instance_table, instance_row):
        """
        Function show_recommendation_action_menu that opens the popup window with insert option

        Params:
            instance_table: table data 
            instance_row: row data
        """
        # Logging the user action for debugging
        logger.info("Row clicked")
        logger.info(f"Table Data: {instance_table.row_data}")
        logger.info(f"Row Data {instance_row}")

        # Create the widget
        content = BoxLayout(orientation='vertical', size_hint= (1,1))

        # Create a button to insert the chosen match
        button_insert = MDRaisedButton(
            text="Insert", 
            on_press=lambda x, t=instance_table, r=instance_row: Clock.schedule_once(lambda dt: self.insert_instance(t, r)), # Use clocking to avoid error when conflicting with loading screen
            pos_hint={"center_y": 0.5, "center_x":0.5}                                        
        )
        
        # Add the button to the widget
        content.add_widget(button_insert)

        # Ininitialize the popup window
        self.insert_popup = Popup(
            title = "Select Action",
            size_hint=(None, None),
            size=(500, 300),
            auto_dismiss=True,
            content = content
        )

        # Open the popup window 
        self.insert_popup.open()

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

        self.header = header

        # Extract the best match index from request_results for the appropriate header
        index = [item[1] for item in request_results if item[0] == header]

        # Extract the best recommendation for both Single and Homogenous requests
        best_match_data_homogenous = [organized_data[index[0]]]
        best_match_data_single = [organized_data[0]]

        # Display the best_table according to mode 
        if rec_mode == 'Homogenous': # If mode is Homogenous
            best_table = MDDataTable(
                column_data = list_titles,
                row_data= best_match_data_homogenous,
                size_hint=(0.6, 0.1),
                pos_hint={"center_x": 0.5, "center_y": 0.6},
                check = True,
                use_pagination=False
            )
        elif rec_mode == 'Single': # If mode is Single
            best_table = MDDataTable(
                column_data = list_titles,
                row_data = best_match_data_single,
                size_hint=(0.6, 0.1),
                pos_hint={"center_x": 0.5, "center_y": 0.6},
                check = True,
                use_pagination=False
            )

        # Define the table of Matches
        table = MDDataTable(
            column_data=list_titles,
            row_data=organized_data,
            size_hint=(0.6, 0.3),
            pos_hint={"center_x": 0.5, "center_y": 0.3},
            use_pagination=True,
            check = True,
            rows_num=20
        )

        # Add the new tables to the widget with Labels
        self.ids.popup_recommendations.add_widget(Label(
            text=f'Best match for {header}:', 
            color=(1, 1, 1, 1), 
            font_size='20sp', 
            size_hint_y=0.05
        ))
        self.ids.popup_recommendations.add_widget(best_table)
        
        # Create spacing Widget
        self.ids.popup_recommendations.add_widget(Widget(
            size_hint_y=None, 
            height=20
        ))



        self.ids.popup_recommendations.add_widget(Label(
            text=f'List of all matches:', 
            color=(1, 1, 1, 1), 
            font_size='20sp', 
            size_hint_y=0.05
        ))
        self.ids.popup_recommendations.add_widget(table)
        table.bind(on_check_press=self.show_recommendation_action_menu)
        best_table.bind(on_check_press=self.show_recommendation_action_menu)

        # Implement Inserting Your own instance HERE

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


    def show_request_help_popup(self):
        """
        Function show_request_help_popup thta displayes help information about the type of requests made.
        """
        content = BoxLayout(orientation='vertical')
        help_text = (
        "[b]Single:[/b] Returns the best vocabulary suggestion for each column independently. "
        "This is useful when your data columns represent different types of information and you want the most accurate match for each.\n\n"
        "[b]Homogenous:[/b] Finds a single vocabulary that works well for all columns together. "
        "This is useful when your data is thematically consistent and you prefer using one shared vocabulary for easier semantic integration."
        )

        label = Label(
            text=help_text,
            markup=True,
            halign="left",
            valign="middle",
            text_size=(400, None),
            size_hint_y=None,
        )

        label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(label)

        content.add_widget(scroll)

        popup = Popup(
            title="Help: Request Types",
            content=content,
            size_hint=(None, None),
            size=(500, 300),
            auto_dismiss=True,
        )

        popup.open()

    def show_recommendation_help_popup(self):
        """
        Function show_recommendation_help_popup that displays help information about the recommendation section.
        """
        content = BoxLayout(orientation='vertical')
        help_text = "Each card represents a column from your uploaded CSV file. It shows the column name, its detected data type, and how many unique values it contains. Use the 'Show Matches' button to view vocabulary suggestions tailored for that specific column."
        
        label = Label(
            text=help_text,
            markup=True,
            halign="left",
            valign="middle",
            text_size=(400, None),
            size_hint_y=None,
        )

        label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))

        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(label)

        content.add_widget(scroll)

        popup = Popup(
            title="Help: Recommendations",
            content=content,
            size_hint=(None, None),
            size=(500, 300),
            auto_dismiss=True,
        )

        popup.open()


    def convert_with_cow(self, csv_path):
        """
        Function convert_with_cow that takes the CSV file and creates a JSON metadata
        
        Params:
            csv_path (str): path to the input file
        
        Utilizes build_schema function from cow_csvw
        """
        input_path = Path(csv_path)
        output_metadata_path = input_path.parent / f"{self.selected_file.name[:-4]}-metadata.json"

        if output_metadata_path.exists():
            logger.info("Metadata file already exists. Loading data.")
        else:
            try:
                build_schema(str(input_path), str(output_metadata_path))
                logger.info(f"Saving metadata at {str(output_metadata_path)}")
            except Exception as e:
                logger.info("Metadata generation failed")
    

    def replace_all(self, headers, all_results, request_results):
        """
        Updates the metadata file with best matches for each column.
        """
        logger.info("Initilizing replacement")
        path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")

        # Load
        with open(path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        logger.info(f"Mode detected: {self.rec_mode}")
        # Build a lookup dict for quick index access
        if self.rec_mode == 'Homogenous':
            index_lookup = {header: idx for header, idx in request_results}
        else:
            index_lookup = {header: 0 for header, idx in request_results}

        for column in data.get('tableSchema', {}).get('columns', []):
            header = column.get('header')
            if header in all_results and header in index_lookup:
                match = all_results[header][index_lookup[header]]

                column.update({
                    'name': match[0][0],     # prefixed name
                    '@id': match[2][0],      # URI
                    'vocab': match[1],       # vocabulary.prefix
                    'type': match[3],        # type
                    'score': match[4],       # score
                    'header': header         # original header for traceability
                })

                logger.info(f"Metadata Updated {header} -> {match[0][0]}")
            else:
                logger.warning(f"Match Not Found for header: {header}")

        # Save
        with open(path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
            logger.info(f"Metadata File Written {path}")

        logger.info("Updating the Screen")
        self.show_json()


    def substitute_recommendations(self, headers, all_results, request_results):
        """
        Updates the metadata file with best matches for each column.
        """
        path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")

        # Load
        with open(path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Build a lookup dict for quick index access
        index_lookup = {header: idx for header, idx in request_results}

        for column in data.get('tableSchema', {}).get('columns', []):
            header = column.get('name')
            if header in all_results and header in index_lookup:
                match = all_results[header][index_lookup[header]]

                column.update({
                    'name': match[0][0],     # prefixed name
                    '@id': match[2][0],      # URI
                    'vocab': match[1],       # vocabulary.prefix
                    'type': match[3],        # type
                    'score': match[4],       # score
                    'header': header         # original header for traceability
                })

                logger.info(f"[Metadata Updated] {header} -> {match[0][0]}")
            else:
                logger.warning(f"[Match Not Found] for header: {header}")

        # Save
        with open(path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
            logger.info(f"[Metadata File Written] {path}")


    def save_json(self):
        """
        Function save_json that saves changes made in the interface.
        """
        # Get the path of the metadata file 
        path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")


        data = self.ids.json_editor.text
        data = json.loads(data)

        with open(path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)

        logger.info("File saved Successfully")
        self.show_json()


    def convert_json(self):
        """
        Function convert_json that converts the metadata file into nquads file. 

        Utilizes the CSVConverter from CoW.

        !FIX THE FILE COPY!
        """
        # Selected file path
        input_csv_path = self.selected_file

        # Check if the file exists
        if not self.selected_file.exists():
            logger.error(f"CSV file does not exist at: {self.selected_file}")
        else:
            logger.info(f"CSV file does exist at: {self.selected_file}")

        metadata_file = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")

        # Check if the metadata file exists
        if not metadata_file.exists():
            logger.error(f"Metadata file not found: {metadata_file}")
        else:
            logger.info(f"Metadata file found: {metadata_file}")

        # INEFFICIENT -> CHANGE
        try:
            # Extract file paths
            input_csv_path = str(self.selected_file)
            correct_metadata_path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")
            cow_expected_path = self.selected_file.with_name(f"{self.selected_file.name}-metadata.json")

            # Ensure CoW finds the metadata file where it expects it
            if not cow_expected_path.exists():
                copyfile(correct_metadata_path, cow_expected_path)
                logger.info(f"Copied metadata to CoW-expected path: {cow_expected_path}")
            
            # Instantiate and run the converter
            converter = CSVWConverter(
                file_name=input_csv_path,
                output_format="nquads",
                base="https://example.com/id/"  
            )

            converter.convert()

            logger.info("Conversion to N-Quads completed successfully.")

        except Exception as e:
            logger.error(f"Error during conversion: {e}")

    def show_json(self):
        """
        Function show_json that displays the json file in the right section
        """

        # Get the path of the metadata file 
        path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")


        # Open and Load the file 
        with open(path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        
        # Prepare for display
        display_json = json.dumps(data, indent=2, ensure_ascii=False)

        # Add to the editor widget
        self.ids.json_editor.text = display_json
        logger.info("Displaying File")


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

        logger.info("Loading the full CSV dataset")
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
        show = RecommendationPopup(header,data, list_titles, request_results, self.rec_mode, self.selected_file)

        # Initialize and open window
        popupWindow = Popup(title=f'Matches for {header}', content=show,size_hint=(1,1))

        logger.info("Opening the Recommendation Popup")
        popupWindow.open()


    def highlight_switch(self):
        """
        Function highlight_switch that changes the color of the request buttons when clicking.
        """
        if self.rec_mode == "Single":
            logger.info("Highliting Choice: [Single Request]")
            self.single_button.md_bg_color = (0.2, 0.6, 0.86, 1) 
            self.homogenous_button.md_bg_color = (0.4, 0.4, 0.4, 1)  
        elif self.rec_mode == "Homogenous":
            logger.info("Highliting Choice: [Homogenous Request]")
            self.single_button.md_bg_color = (0.4, 0.4, 0.4, 1) 
            self.homogenous_button.md_bg_color = (0.2, 0.6, 0.86, 1)


    def switch_mode(self, choice, headers, all_results, table):
        """
        Function switch_mode that switches conversion mode according to the button pressed

        Params:
            choice (str): Single or Homogenous
            headers, all_results, table: see create_header_buttons function
        """
        # Set the variable to user choice
        self.rec_mode = choice

        # Reload the cards 
        logger.info("Reloading the header cards")
        self.create_header_buttons(headers, all_results, table)

        self.highlight_switch()
        logger.info(f"Mode switched to {self.rec_mode} requests")


    def create_header_buttons(self, headers, all_results, table):
        """
        Function create_header_buttons that adds a button for every widget in the file

        Params:
            headers (list): list of headers
            all_results (dict): dictionary of all headers with their matches
            table: display widget 
        """
        # Clear the previous buttons
        table.clear_widgets()

        # Add a spacing widget
        table.add_widget(Widget(size_hint_y=None, height=20))

        # For Every header add a corresponding button with the appropriate data
        for header in headers:
            data = all_results[header]

            dtype = infer_column_type(header, self.selected_file) 
            number_of_matches = len(all_results[header])

            card = MDCard(
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

            card.add_widget(MDLabel(
                text=f"[b]Header:[/b] {header}",
                markup=True,
                theme_text_color="Primary",
                font_style="Subtitle1",
                size_hint_y=None,
                height=30
            ))

            card.add_widget(MDLabel(
                text=f"Type: {dtype}  |  Matches: {number_of_matches}",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=24
            ))

            card.add_widget(MDRaisedButton(
                text="Show Matches",
                size_hint=(None, None),
                size=(150, 40),
                pos_hint={"center_x": 0.5},
                on_press=lambda x, h=header, d=data: self.open_recommendations(h, d, self.list_titles, self.request_results)
            ))

            table.add_widget(Widget(size_hint_y=None, height=40))
            table.add_widget(card)
            logger.info("Set of header cards created successfully")

    def query_linked_open_vocabularies(self, headers, size):
        for header in headers:
            recommendations = get_recommendations(header, size)
            organized_data = organize_results(recommendations)
            self.all_results[header] = organized_data

    def display_recommendation(self, file_path):
        """
        Function display_recommnedation:
            1. Retreitves the recommendation from the input csv.
            2. Displays the headers on the middle page.
            3. Displays the recommendations on the middle page.
        """
        # Initialize a class variable with file path -> reusable in other functions
        self.selected_file = file_path

        # Get the headers from CSV file
        logger.info("Retrieving CSV headers")
        headers = get_csv_headers(str(file_path))

        # Dictionary {header: list of matches}
        self.all_results = {}

        # Set the size of received matches
        size = 20

        # Convert the CSV to metadata JSON 
        converter = threading.Thread(target=self.convert_with_cow, args=(file_path,))
        #self.convert_with_cow(str(file_path))

        # For every header get recommendations and populate the all_results dictionary
        logger.info("Populating the match dictionary")
        query = threading.Thread(target=self.query_linked_open_vocabularies, args=(headers, size))
        #self.query_linked_open_vocabularies(headers, size)

        converter.start()
        query.start()

        converter.join()
        query.join()

        # Store the display widget
        table = self.ids.vocab_recommender

        # List of titles with spacings
        self.list_titles = [
            ('prefixedName', dp(60)), 
            ('vocabulary.prefix', dp(60)), 
            ('uri',dp(60)),
            ('type',dp(60)), 
            ('score',dp(60))
        ]


        # Get all the vocabularies from the request data
        logger.info("Retrieve vocabulary list")
        vocabs = get_vocabs(self.all_results)

        # Calculate average score for every vocabulary
        logger.info("Compute average score")
        scores = get_average_score(vocabs, self.all_results)

        # Find best vocabularies according to combiSQORE 
        logger.info("Calculate Combi Score")
        combi_score_vocabularies = calculate_combi_score(self.all_results, scores)
        sorted_combi_score_vocabularies = sorted(combi_score_vocabularies, key=lambda x: x[1], reverse=True)
        
        # Retrieve indexes of best matches for every header 
        self.request_results = retrieve_combiSQORE_recursion(self.all_results, sorted_combi_score_vocabularies, len(headers))
        
        logger.info("Request processing finished")

        # Create buttons for every header
        self.create_header_buttons(headers, self.all_results, table)

        # Load CSV data for table
        with open(str(file_path), newline='', encoding='utf-8') as csvfile:
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

        # Create data overwiew table
        self.csv_table = MDDataTable(
            column_data=column_heads,
            row_data=table_rows,
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            use_pagination=True,
            rows_num = 10
        )

        # Show JSON file in the right section
        json_path = 'examples/metadata.json'
        self.substitute_recommendations(headers, self.all_results, self.request_results)
        self.show_json()

        # Add two buttons to toggle between Single and Homogenous texts 
        self.single_button = MDRaisedButton(
            text='Single', 
            on_press=lambda x: self.switch_mode('Single', headers, self.all_results, table), 
            size_hint={0.5, None}
        )

        self.homogenous_button = MDRaisedButton(
            text='Homogenous',
            on_press=lambda x: self.switch_mode('Homogenous', headers, self.all_results, table),
            size_hint={0.5, None}
        )

        self.replace_all_button = MDRaisedButton(
            text='Replace All',
            size_hint={0.5, None},
            pos_hint={'center_x': 0.5},
            on_press= lambda x: self.replace_all(headers, self.all_results, self.request_results)
        )

        self.highlight_switch()
        self.ids.request_option_panel.add_widget(self.single_button)
        self.ids.request_option_panel.add_widget(self.homogenous_button)
        self.ids.request_option_panel_under.add_widget(self.replace_all_button)

        # Clear previews widgets
        self.ids.csv_preview_container.clear_widgets()
        self.ids.csv_preview_container.add_widget(self.csv_table)

        # Load Full dataset overview popup
        open_popup = MDRaisedButton(
            text='Load Full Dataset', 
            on_press=lambda x: self.show_popup(column_heads,row_data), 
            size_hint=(0.3, None),
            pos_hint={"center_x": 0.5}
        )
        
        self.ids.csv_preview_container.add_widget(open_popup)


class CowApp(MDApp):
    def build(self):
        """
        Build app function that runs the Screen Manager.
        """
        sm = ScreenManager()
        sm.add_widget(StartingScreen(name="start")) # File Selection Screen
        sm.add_widget(ConverterScreen(name="converter")) # Conversion Screen
        return sm
    
if __name__ == '__main__':
    CowApp().run()