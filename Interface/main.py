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
from tkinter import Tk, filedialog
from pathlib import Path
from kivy.core.window import Window
from .requests_t import get_recommendations, organize_results, get_vocabs, get_average_score, calculate_combi_score, retrieve_combiSQORE_recursion  # My implementation of single / homogenous requests
from .sparql_requests import get_sparql_recommendations, organize_sparql_results, get_sparql_vocabs, compute_similarity, assign_match_scores, get_average_sparql_score, calculate_sparql_combi_score, retrieve_sparql_results
from kivymd.uix.datatables import MDDataTable
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
import csv
import json
import logging
from cow_csvw.converter.csvw import build_schema, CSVWConverter
from utils import infer_column_type, open_csv, show_warning, get_csv_headers, show_success_message, create_vocab_row_data
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.snackbar import MDSnackbar
from kivy.clock import Clock
from shutil import copyfile
from kivy.uix.textinput import TextInput
from threading import Thread, Lock
from kivymd.uix.spinner import MDSpinner
import time
import multiprocessing
#-----------------------------

# Set up the logger
logger = logging.getLogger(__name__)

class StartingScreen(Screen):
    """
    Class StartingScreen that implements logic behind file selection.

    1. This class corresponds to the first screen user sees when opening the CoW Interface.
    2. After user selects the file and presses "Convert" button the system switches to ConverterScreen class

    Attributes:
        None
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_file = None


    def select_file(self):
        """
        Function select_file that opens filechooser.
        """
        logger.info("File chooser: Opening...")

        logger.info("File chooser: Opening...")
        root = Tk()
        root.withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        root.destroy()

        if file_path:
            self.selected_file = Path(file_path)
            self.ids.file_path_label.text = self.selected_file.name
            logger.info(f"File selected: {file_path}")
        else:
            logger.info("No file selected.")


    def select_store(self, selection: list) -> None:
        """
        Function selct_store that: 
            1. Stores the selected file path.
            2. Updates the file name label.
        Params:
            selection (list): list of length 1 with a selected file
        """
        # If user has Selected the file then update the Path and display the label of the file name of the screen
        if selection:
            self.selected_file = Path(selection[0])
            file_path_name = str(Path(selection[0]).name)
            self.ids.file_path_label.text = file_path_name
        logger.info("File Chooser: Closing...")


    def switch(self) -> None:
        """
        Function switch that 
            1. Switches the screen to loading_screen
            2. Passes the file path to the converter_screen
            3. Raises a warning window in case of a wrong file selection
        """
        # Retrieve the API endpoint
        custom_endpoint = self.ids.api_endpoint_data.text
        logger.info(f"API endpoint: {custom_endpoint}")

        # Invoking screen manager to switch to converter screen if proper file selected
        if self.selected_file:

            rows = open_csv(self.selected_file)
            if len(rows) > 0:

                # Check if the file is a CSV file
                if not str(self.selected_file).lower().endswith('.csv'):
                    logger.warning('Not a CSV file')
                    show_warning("Please select a CSV file")
                    return
                
                # Switch to loading screen
                self.manager.current = "loading"
                logger.info("Screen Manager: Switching to Loading Screen")
                
                # Schedule the data loading and screen switch
                def load_data(dt):
                    converter_screen = self.manager.get_screen("converter")
                    converter_screen.display_recommendation(self.selected_file, custom_endpoint)
                    self.manager.current = "converter"
                    logger.info("Screen Manager: Switching to Converter Screen")
                
                # Schedule the loading with a small delay to ensure loading screen is visible (0.5 seconds minimum for loading screen to be visible)
                Clock.schedule_once(load_data, 0.5)
            else:
                logger.warning("File is empty")
                show_warning("The file is empty. Please select a different file.")
        else:
            logger.warning('No file selected')
            show_warning("Please select a file")


class LoadingScreen(Screen):
    """
    Class LoadingScreen that displays a loading animation while data is being processed.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        
        # Add a spinning circle
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
        
        # Add main layout to screen
        self.add_widget(main_layout)


class DataPopup(FloatLayout):
    """
    Class DataPopup that defines a popup page that displays full csv data table.

    By default it invokes build_table function that loads whole dataset into a MDDataTable.
    """


    def __init__(self, column_heads, row_data, **kwargs):
        super().__init__(**kwargs)
        self.build_table(column_heads, row_data)


    def build_table(self, column_heads: list, row_data: list):
        """
        Function build_table that builds the table inspection widget for the whole dataset.

        Params:
            column_heads(arr): list of headers
            row_data(arr): list of data row by row
        """
        # Add a spacing widget
        self.ids.popup_data_container.add_widget(Widget(size_hint_y=None, height=20))

        # Define the table
        table = MDDataTable(
            column_data=column_heads,                     # column data 
            row_data=row_data,                            # row data
            size_hint=(0.9, 0.85),                        # size
            pos_hint={"center_x": 0.5, "center_y": 0.5},  # position
            use_pagination=True,                          # enable splitting data into pages
            rows_num=20                                   # maximum row numbers per page
        )

        # Clear the previous table on launch and add the new table to the widget
        self.ids.popup_data_container.clear_widgets()
        self.ids.popup_data_container.add_widget(table)


    def dismiss_popup(self):
        """
        Function dismiss_popup that closes the popup.
        """
        # Retrieve the parent of the popup
        parent = self.parent
        while parent:
            if isinstance(parent, Popup):
                parent.dismiss()        # close the popup
                break
            parent = parent.parent



class RecommendationPopup(FloatLayout):
    """
    Class RecommendationPopup that implements the logic behind Recommendation popups for every header 

    Attributes:
        header (str): current table header
        organized_data (list): match data for the header
        list_titles (list): list of match parameters e.g prefixedName, uri, score...
        rec_mode (str): mode of recommendation (Single or Homogenous)
        selected_file (str): path to the selected file
    """

    def __init__(self, header: str, organized_data: list, list_titles: list, request_results: list, rec_mode: str, selected_file: str, **kwargs):
        super().__init__(**kwargs)
        self.header = header
        self.selected_file = selected_file
        self.build_table(header, organized_data, list_titles, request_results, rec_mode)


    def insert_instance(self, table: MDDataTable, row: list):
        """
        Inserts the selected match into the metadata file for the current header.

        Args:
            table (MDDataTable): full table data
            row (list): data of the selected row
        """
        def clean(text: str):
            """
            Function clean that cleans the inserted results from unnecessary brackets

            Args:
                text (str): text that needs to be cleaned
            Returns:
                text (str): text cleaned from the unnecessary punctuation

            """
            return text.translate(str.maketrans('', '', "[]'"))

        # Parse and clean the row values
        name = clean(row[0])
        vocab = clean(row[1])
        uri = clean(row[2])
        rdf_type = clean(row[3])
        score = float(row[4])

        # Choose the data path with only the name
        data_path = self.selected_file.parent / f"{self.selected_file.name[:-4]}-metadata.json"

        # Open the csv file for reading
        with open(data_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Initialize the flag to track success of the update
        updated = False

        # Loop through all columns in the tableSchema
        for column in data.get('tableSchema', {}).get('columns', []):
            if column.get('name') == self.header:
                column.update({
                    'prefixedName': name,     # prefixed name 
                    '@id': uri,       # uri
                    'vocab': vocab,   # vocabulary 
                    'type': rdf_type, # rdf type
                    'score': score    # score
                })

                updated = True # If replaced update the flag
                logger.info(f"[Inserted] {self.header} -> {name} ({vocab})")

        # Display warning
        if not updated:
            logger.warning(f"Insert Failed: Header '{self.header}' not found in metadata.")

        # Save the modified data to the file 
        with open(data_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)
            logger.info(f"Metadata File Written: {data_path}")

        # After Insert is Finished close the Popup
        self.insert_popup.dismiss()

        # Refresh JSON preview
        app = MDApp.get_running_app()
        app.root.get_screen("converter").show_json()
        logger.info("Converter Screen: Refreshed JSON Preview Screen")


    def show_recommendation_action_menu(self, instance_table: MDDataTable, instance_row: list):
        """
        Function show_recommendation_action_menu that opens the popup window with insert option

        Args:
            instance_table (MDDataTable): table data 
            instance_row (list): row data
        """
        
        # Logging the user action for debugging
        logger.info("Recommendation Popup: Row clicked")
        logger.info(f"Recommendation Popup: Table Data - {instance_table.row_data}")
        logger.info(f"Recommendation Popup: Row Data - {instance_row}")

        # Create the widget
        content = BoxLayout(orientation='vertical', size_hint= (1,1))

        # Create a button to insert the chosen match
        button_insert = MDRaisedButton(
            text="Insert", 
            on_press=lambda x, t=instance_table, r=instance_row: Clock.schedule_once(lambda dt: self.insert_instance(t, r)), # Use clocking to avoid error when conflicting with loading screen
            size_hint=(None, None),
            pos_hint={"center_x":0.5, "y": 0.6}                                        
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


    def build_table(self, header: str, organized_data: list, list_titles: list, request_results: list, rec_mode: str):
        """
        Function build_table that builds the table for every header.

        Args:
            header (str): current header
            organized_data (list): list of matches for the header
            list_titles (list): list of titles for the output table columns
            request_results (list): list of tuples of the headers and indexes of the best match
            rec_mode (str): mode of display (Single or Homogenous)

        """
        # Clear all  previous widgets
        self.ids.popup_recommendations.clear_widgets()

        if not organized_data or len(organized_data) == 0:
            self.ids.popup_recommendations.add_widget(Label(
                text='NO Matches found',
                color=(1,1,1,1),
                font_size='20sp',
                size_hint_y=0.05
            ))
            return  # Prevent Table creation
        

        # Update the class-wide variable with the received header
        self.header = header

        # Extract the best match index from request_results for the appropriate header
        try: 
            index = [item[1] for item in request_results if item[0] == header]

            # Extract the best recommendation for both Single and Homogenous requests
            best_match_data_homogenous = [organized_data[index[0]]]   # Retrieve the match indicated by the index
            best_match_data_single = [organized_data[0]]              # Since matches are already sorted retrieve the first one

        except:
            best_match_data_homogenous = []
            best_match_data_single = []

        if len(best_match_data_single) > 0 and len(best_match_data_homogenous) > 0:
            # Display the best match table according to mode 
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

            # Define the table of all matches
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

            # Add best table to the widget
            self.ids.popup_recommendations.add_widget(best_table)
            
            # Create spacing Widget
            self.ids.popup_recommendations.add_widget(Widget(
                size_hint_y=None, 
                height=20
            ))

            # Add the title
            self.ids.popup_recommendations.add_widget(Label(
                text=f'List of all matches:', 
                color=(1, 1, 1, 1), 
                font_size='20sp', 
                size_hint_y=0.05
            ))

            # Add all matches table to the widget
            self.ids.popup_recommendations.add_widget(table)

            # Bind the insert functionality to every row of both tables 
            table.bind(on_check_press=self.show_recommendation_action_menu)
            best_table.bind(on_check_press=self.show_recommendation_action_menu)
        else:
            self.ids.popup_recommendations.add_widget(Label(
                text='NO Matches found',
                color=(1,1,1,1),
                font_size='20sp',
                size_hint_y=0.05
            ))

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

class VocabularyScorePopup(FloatLayout):
    def __init__(self, vocabulary_match_scores, vocabulary_coverage_score, vocabulary_scores, **kwargs):
        super().__init__(**kwargs)
        self.vocabulary_match_scores = vocabulary_match_scores
        self.vocabulary_coverage_score = vocabulary_coverage_score
        self.vocabulary_scores = vocabulary_scores
        self.build_table(vocabulary_match_scores, vocabulary_coverage_score, vocabulary_scores)

    def build_table(self, vocabulary_match_scores, vocabulary_coverage_score, vocabulary_scores):
        """
        Builds the vocabulary scores table with proper error handling.
        """
        self.ids.popup_vocab_recommendations.clear_widgets()
        
        # Add error handling for empty data
        if not vocabulary_match_scores or not vocabulary_scores:
            self.ids.popup_vocab_recommendations.add_widget(Label(
                text='No vocabulary data available',
                color=(1,1,1,1),
                font_size='20sp',
                size_hint_y=0.05
            ))
            return
        
        try:
            vocab_data = create_vocab_row_data(vocabulary_match_scores, vocabulary_coverage_score, vocabulary_scores)
            logger.info(f"Row_data: {vocab_data}")
            
            # Check if we have valid data
            if not vocab_data:
                self.ids.popup_vocab_recommendations.add_widget(Label(
                    text='No vocabulary data available',
                    color=(1,1,1,1),
                    font_size='20sp',
                    size_hint_y=0.05
                ))
                return
            
            list_col_names = [
                ("vocabularies", dp(60)), 
                ("Average Match Score", dp(60)), 
                ("Number of Produced Matches", dp(60)),
                ("Combi Score", dp(60))
            ]

            table = MDDataTable(
                column_data=list_col_names,
                row_data=vocab_data,
                size_hint=(0.6, 0.3),
                pos_hint={"center_x": 0.5, "center_y": 0.3},
                use_pagination=True,
                check=False,  # Disable row selection to prevent crashes
                rows_num=20
            )
            
            self.ids.popup_vocab_recommendations.add_widget(table)
            
        except Exception as e:
            logger.error(f"Error building vocabulary table: {e}")
            self.ids.popup_vocab_recommendations.add_widget(Label(
                text=f'Error loading vocabulary data: {str(e)}',
                color=(1,1,1,1),
                font_size='16sp',
                size_hint_y=0.05
            ))
            
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

    Attributes:
        rec_mode: indicates the request method, singular or homogenous
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rec_mode = "Homogenous"  # Changing in the switch_mode function
        self.headers = []  # Add this to store headers for search functionality
        self.sorted_combi_score_vocabularies = [] 


    def show_loading_screen(self):
        self.manager.current = "loading"


    def show_converter_screen(self):
        self.manager.current = "converter"


    def show_request_help_popup(self):
        """
        Function show_request_help_popup thta displayes help information about the type of requests made.
        """

        # Create a box layout for the helper content
        content = BoxLayout(orientation='vertical')

        # insert the text of the helper button
        help_text = (
        "[b]Single:[/b] Returns the best vocabulary suggestion for each column independently. "
        "This is useful when your data columns represent different types of information and you want the most accurate match for each.\n\n"
        "[b]Homogenous:[/b] Finds a single vocabulary that works well for all columns together. "
        "This is useful when your data is thematically consistent and you prefer using one shared vocabulary for easier semantic integration."
        )

        # Bind the text to the Label
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

        # Open the popup
        popup.open()

    def show_recommendation_help_popup(self):
        """
        Function show_recommendation_help_popup that displays help information about the recommendation section.
        """
        content = BoxLayout(orientation='vertical')

        # Help text 
        help_text = "Each card represents a column from your uploaded CSV file. It shows the column name, its detected data type, and how many unique values it contains. Use the 'Show Matches' button to view vocabulary suggestions tailored for that specific column."
        
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

        # Open popup
        popup.open()


    def convert_with_cow(self, csv_path: str):
        """
        Function convert_with_cow that takes the CSV file and creates a JSON metadata
        Utilizes build_schema function from cow_csvw

        Args:
            csv_path (str): path to the input file
        
        """

        # convert string to a Path object for further processing
        input_path = Path(csv_path)

        # Retrieve the whole path + the retrieved file name with the file type for CoW conversion
        #   The final path looks as following: csvFileName.csv-metadata.json
        output_metadata_path = input_path.parent / f"{self.selected_file.name[:-4]}-metadata.json"

        # Check if the file was already generated
        if output_metadata_path.exists():
            logger.info("CoW: Metadata file already exists. Loading data.")
        else:
            try:
                start_time_converter = time.time()
                build_schema(str(input_path), str(output_metadata_path)) # Build the mapping file using the CoW implementation
                end_time_converter = time.time()
                total_execution_time_converter = end_time_converter - start_time_converter
                logger.info(f"Total execution time of conversion: {total_execution_time_converter} seconds")
                logger.info(f"CoW: Saving metadata at {str(output_metadata_path)}")
            except Exception as e:
                logger.info("CoW: Metadata generation failed")
    

    def replace_all(self, headers: list, all_results: dict, request_results: list):
        """
        Updates the metadata file with best matches for each column.

        Args;
            headers (list): list of all the headers in the csv file
            all_results: (dict): dictionary with all matches for every header from the headers
            request_resuls (list): list of best matches for every header from headers
        """
        logger.info("System: Initilizing replacement")

        # Find the metadata path without the extension
        path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")

        # Load the file
        with open(path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        logger.info(f"System: Mode detected: {self.rec_mode}")

        # Build a lookup map for quick index access depending on the request mode 
        if self.rec_mode == 'Homogenous':
            index_lookup = {header: idx for header, idx in request_results} # If homogenous than retrieve index for every header
        else:
            index_lookup = {header: 0 for header, idx in request_results} # If single take the first match

        # Retrieve the column names from tableSchema
        for column in data.get('tableSchema', {}).get('columns', []):
            # Get the header name for mapping purposes
            header = column.get('name')

            # If header is present in both all_results and index_lookup
            if header in all_results and header in index_lookup:
                match = all_results[header][index_lookup[header]]
                
                if self.custom_endpoint == "":
                    # Update the data in the file 
                    column.update({
                        'name': header,
                        'prefixedName': match[0][0],  # prefixed name
                        '@id': match[2][0],           # URI
                        'propertyUrl': match[2][0],   # URI for CoW
                        'vocab': match[1],            # vocabulary.prefix
                        'type': match[3],             # type
                        'score': match[4],            # score
                    })
                else:
                    column.update({
                        'name': header,
                        'prefixedName': match[0],     # prefixed name
                        '@id': match[2],              # URI
                        'propertyUrl': match[2],      # URI for CoW
                        'vocab': match[1],            # vocabulary.prefix
                        'type': match[3],             # type
                        'score': match[4],            # score
                    })

                logger.info(f"System: Metadata Updated {header} -> {match[0][0]}")
            else:
                logger.warning(f"System: Match Not Found for header: {header}")

        # Save the changes
        try:
            with open(path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)
                logger.info(f"System: Metadata File Written {path}")
        except Exception as e:
            logger.warning(f"Error writing metadata file: {e}")
            show_warning("Could not write the metadata file. Please check file permission.")

        logger.info("Converter Screen: Updating the Screen")

        # Update the json preview
        self.show_json()


    def substitute_recommendations(self, headers: list, all_results: dict, request_results: list):
        """
        Updates the metadata file with best matches for each column.

        Params:
            headers (list): list of headers
            all_results (dict): dictionary of header: list of matches
            request_results (list): array of tuples containt the header and corresponding best match
        """

        # Retrieve the file path without the type name 
        path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")

        # Open the file 
        with open(path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Build a lookup dict for quick index access
        index_lookup = {header: idx for header, idx in request_results}

        for column in data.get('tableSchema', {}).get('columns', []):
            header = column.get('name')
            if header in all_results and header in index_lookup:
                match = all_results[header][index_lookup[header]]

                if self.custom_endpoint == "":
                    column.update({
                        'name': header,
                        'prefixedName': match[0][0],  # prefixed name
                        '@id': match[2][0],           # URI
                        'propertyUrl': match[2][0],   # URI for CoW
                        'vocab': match[1],            # vocabulary.prefix
                        'type': match[3],             # type
                        'score': match[4],            # score
                    })
                else:
                    column.update({
                        'name': header,
                        'prefixedName': match[0],     # prefixed name
                        '@id': match[2],              # URI
                        'propertyUrl': match[2],      # URI for CoW
                        'vocab': match[1],            # vocabulary.prefix
                        'type': match[3],             # type
                        'score': match[4],            # score
                    })

                logger.info(f"System: Metadata Updated - {header} -> {match[0][0]}")
            else:
                logger.warning(f"System: Match Not Found - for header: {header}")

        # Save
        try:
            with open(path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=4, ensure_ascii=False)
                logger.info(f"System: Metadata File Written - {path}")
        except Exception as e:
            logger.warning(f"Error writing metadata file: {e}")
            show_warning("Could not write the metadata file. PLease check file permissions.")


    def save_json(self):
        """
        Function save_json that saves changes made in the interface.
        """
        # Get the path of the metadata file 
        path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")

        # Retieve the current text in the JSON 
        data = self.ids.json_editor.text
        data = json.loads(data)

        # Save the Retrieved data into the fiel 
        with open(path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)

        logger.info("System: File saved Successfully")

        # Update the JSON preview
        self.show_json()

    def convert_json(self):
        """
        Function convert_json that converts the metadata file into nquads file. 

        Utilizes the CSVConverter from CoW.
        """
        #multiprocessing.freeze_support()
        # Selected file path
        input_csv_path = self.selected_file

        # Check if the file exists
        if not self.selected_file.exists():
            logger.error(f"System: CSV file does not exist at: {self.selected_file}")
        else:
            logger.info(f"System: CSV file does exist at: {self.selected_file}")

        metadata_file = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")

        # Check if the metadata file exists
        if not metadata_file.exists():
            logger.error(f"System: Metadata file not found: {metadata_file}")
        else:
            logger.info(f"System: Metadata file found: {metadata_file}")

        try:
            start_time_converter = time.time()
            # Extract file paths
            input_csv_path = str(self.selected_file)
            correct_metadata_path = self.selected_file.with_name(f"{self.selected_file.stem}-metadata.json")
            cow_expected_path = self.selected_file.with_name(f"{self.selected_file.name}-metadata.json")

            # Ensure CoW finds the metadata file where it expects it
            if not cow_expected_path.exists():
                copyfile(correct_metadata_path, cow_expected_path)
                logger.info(f"System: Copied metadata to CoW-expected path: {cow_expected_path}")
            
            # Instantiate and run the converter
            converter = CSVWConverter(
                file_name=input_csv_path,
                processes=1,
                output_format="nquads",
                base="https://example.com/id/"  
            )

            converter.convert()

            logger.info("CoW: Conversion to N-Quads completed successfully.")
            show_success_message("Conversion to N-Quads completed successfully.")
            end_time_converter = time.time()
            total_execution_time_converter = end_time_converter - start_time_converter
            logger.info(f"Total execution time of conversion: {total_execution_time_converter} seconds")
        except Exception as e:
            logger.error(f"CoW: Error during conversion: {e}")


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
        logger.info("Converter Screen: Displaying File")


    def show_popup(self, column_heads: list, row_data: list):
        """
        Function show_popup that calls the DataPopup class to display the table 

        Args:
            column_heads (list): list of headers
            row_data (list): list of data row by row

        Those parameters are only needed to pass it further to the DataPopup screen
        """
        # Show loading screen
        self.manager.current = "loading"

        # Schedule the data loading after a delay
        Clock.schedule_once(lambda dt: self.load_full_dataset(column_heads, row_data), 0.5)

    def load_full_dataset(self, column_heads, row_data):
        """
        Function to load the full dataset and display it in a popup.
        """
        # Pass the data to the popup
        show = DataPopup(column_heads, row_data)

        # Initialize and open window
        popupWindow = Popup(title="CSV Data", content=show, size_hint=(1, 1))

        logger.info("Converter Screen: Loading the full CSV dataset")
        popupWindow.open()

        # Switch back to the converter screen after loading
        self.manager.current = "converter"


    def open_recommendations(self,header: str, data: list, list_titles: list, request_results: list):
        """
        Function open recommendations that opens a recommendation popup.

        Args:
            header (str): name of the csv header
            data (list): list of data for the header  
            list_titles (list): list of table headers
        """
        if header not in self.all_results or not self.all_results[header]:
            show_warning("No data available for this header. Try running the recommendation again.")
            return

        if not data or len(data) == 0:
            show_warning("Couldn't load the data, try again")
            return

        self.show_loading_screen()

        def show_popup_after_loading(dt):
            # Pass the data to the popup
            show = RecommendationPopup(header,data, list_titles, request_results, self.rec_mode, self.selected_file)

            # Initialize and open window
            popupWindow = Popup(title=f'Matches for {header}', content=show,size_hint=(1,1))

            logger.info("Converter Screen: Opening the Recommendation Popup")
            popupWindow.open()
            self.show_converter_screen()

        Clock.schedule_once(show_popup_after_loading, 1)


    def open_vocabulary_recommendations(self, vocabulary_match_scores, vocabulary_coverage_score, vocabulary_scores):
        """
        Function open recommendations that opens a recommendation popup.

        Args:
            header (str): name of the csv header
            data (list): list of data for the header  
            list_titles (list): list of table headers
        """
        if len(vocabulary_match_scores) == 0:
            show_warning("No vocabulary data available")
            return

        if len(vocabulary_scores) == 0:
            show_warning("Couldn't load the data, try again")
            return
        
        if len(vocabulary_coverage_score) == 0:
            show_warning("Couldn't load the data, try again")
            return

        self.show_loading_screen()

        def show_popup_after_loading(dt):
            # Pass the data to the popup
            show = VocabularyScorePopup(vocabulary_match_scores, vocabulary_coverage_score, vocabulary_scores)

            # Initialize and open window
            popupWindow = Popup(title=f'Vocabulary Ranking data', content=show,size_hint=(1,1))

            logger.info("Converter Screen: Opening the Recommendation Popup")
            popupWindow.open()
            self.show_converter_screen()

        Clock.schedule_once(show_popup_after_loading, 1)

    def highlight_switch(self):
        """
        Function highlight_switch that changes the color of the request buttons when clicking.
        """
        if self.rec_mode == "Single":
            logger.info("Converter Screen: Highliting Choice- Single Request")
            self.single_button.md_bg_color = (0.2, 0.6, 0.86, 1) 
            self.homogenous_button.md_bg_color = (0.4, 0.4, 0.4, 1)  
        elif self.rec_mode == "Homogenous":
            logger.info("Converter Screen: Highliting Choice- Homogenous Request")
            self.single_button.md_bg_color = (0.4, 0.4, 0.4, 1) 
            self.homogenous_button.md_bg_color = (0.2, 0.6, 0.86, 1)


    def switch_mode(self, choice: str, headers: list, all_results: dict, table):
        """
        Function switch_mode that switches conversion mode according to the button pressed

        Params:
            choice (str): Single or Homogenous
            other: headers, all_results, table: see create_header_buttons function
        """
        # Set the variable to user choice
        self.rec_mode = choice

        # Reload the cards 
        logger.info("Converter Screen: Reloading the header cards")
        self.create_header_buttons(headers, all_results, table)

        self.highlight_switch()
        logger.info(f"Converter Screen: Mode switched to {self.rec_mode} requests")


    def create_header_buttons(self, headers, all_results, table):
        """
        Function create_header_buttons that adds a button for every widget in the file with pagination
        
        Params:
            headers (list): list of headers
            all_results (dict): dictionary of all headers with their matches
            table: display widget
        """
        # Clear the previous buttons
        table.clear_widgets()

        # Add a spacing widget
        table.add_widget(Widget(size_hint_y=None, height=20))

        # Calculate pagination info
        self.cards_per_page = 5
        self.current_page = getattr(self, 'current_page', 0)              # Get current page or default to 0
        self.total_pages = (len(headers) - 1) // self.cards_per_page + 1  # Calculate total pages
        
        # Get the slice of headers for current page
        start_idx = self.current_page * self.cards_per_page
        end_idx = start_idx + self.cards_per_page
        current_headers = headers[start_idx:end_idx]

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
                text=f"Vocabularies: {len(self.vocabulary_match_scores)}",
                theme_text_color="Secondary",
                size_hint_y=None,
                height=24
            ))


        vocab_card.add_widget(MDRaisedButton(
                text="Show Scores",
                size_hint=(None, None),
                size=(150, 40),
                pos_hint={"center_x": 0.5},
                on_press = lambda x, v=self.vocabulary_match_scores, vc= self.vocab_coverage_score, vm= self.vocabulary_scores: self.open_vocabulary_recommendations(v, vc, vm)
        ))
        
        table.add_widget(vocab_card)

        # For Every header in current page add a corresponding button with the appropriate data
        for header in current_headers:
            logger.info(f"creating a card for {header}")
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

        # Add pagination controls
        pagination_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            height=50,
            width=400,
            pos_hint={"center_x": 0.5},
            spacing=10
        )

        # Previous page button
        prev_button = MDRaisedButton(
            text="Previous",
            disabled=self.current_page == 0,
            on_press=lambda x: self.change_page(-1, headers, all_results, table),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5}
        )
        
        # Page indicator label
        page_label = MDLabel(
            text=f"Page {self.current_page + 1} of {self.total_pages}",
            halign='center',
            size_hint = (None, None),
            size=(150, 40),
            pos_hint={"center_x": 0.5}
        )

        # Next page button
        next_button = MDRaisedButton(
            text="Next",
            disabled=self.current_page >= self.total_pages - 1,
            on_press=lambda x: self.change_page(1, headers, all_results, table),
            size_hint=(None, None),
            pos_hint={"center_x": 0.5}
        )

        pagination_layout.add_widget(prev_button)
        pagination_layout.add_widget(page_label)
        pagination_layout.add_widget(next_button)

        table.add_widget(Widget(size_hint_y=None, height=20))
        table.add_widget(pagination_layout)
        
        logger.info(f"Converter Screen: Set of header cards created successfully (Page {self.current_page + 1} of {self.total_pages})")


    def change_page(self, direction, headers, all_results, table):
        """
        Function to change the current page of header cards
        
        Args:
            direction (int): 1 for next page, -1 for previous page
            headers (list): list of headers
            all_results (dict): dictionary of all headers with their matches
            table: display widget
        """
        self.current_page = max(0, min(self.current_page + direction, self.total_pages - 1))
        self.create_header_buttons(headers, all_results, table)


    def compute_scores(self, vocabs, all_results):
        """
        Function compute_scores that computes average scores in a separate thread. 

        Params:
            vocabs - list of vocabularies
            all_results - dictionary with the headers and corresponding matches

        """
        scores = get_average_score(vocabs, all_results)
        self.vocabulary_match_scores = scores
        logger.info(f"Quality of matches {self.vocabulary_match_scores}")
        combi_score_vocabularies, self.vocab_coverage_score = calculate_combi_score(all_results, scores)
        logger.info(f"Coverage Score: {self.vocab_coverage_score}")
        self.vocabulary_scores = combi_score_vocabularies
        logger.info(f"Combi_score {self.vocabulary_scores}")
        self.sorted_combi_score_vocabularies = sorted(combi_score_vocabularies, key=lambda x: x[1], reverse=True)



    def compute_sparql_scores(self, vocabs, all_results):
        """
        Function compute_sparql_scores that computes average scores in a separate thread. 
        """
        scored_results = assign_match_scores(all_results)
        logger.info(f"Scored_results: {scored_results}")
        scores = get_average_sparql_score(vocabs, scored_results)
        logger.info(f"Vocabulary scores: {scores}")
        combi_score_vocabularies = calculate_sparql_combi_score(all_results, scores)
        self.sorted_combi_score_vocabularies = sorted(combi_score_vocabularies, key=lambda x: x[1], reverse=True)

    def query_linked_open_vocabularies(self, headers, size):
        """
        Function query_linked_open_vocabularies that sends request to LOV API separately for every header

        Embedded function query_header executes query to API for every header separately

        Params:
            headers - list of headers
            size - maximum number of matches
        """
        # Initialize Lock
        self.lock = Lock()

        # Initialize list of Threads
        threads = []

        self.execution_times = {}

        def query_header(header, size):
            """
            Function query_header that executes a thread for every header
            """
            try:
                # Start time of query
                start_time = time.time()
                recommendations = get_recommendations(header, size)
                organized_data = organize_results(recommendations)
                end_time = time.time()
                execution_time = end_time - start_time              

                # Lock overwriting the hash map
                with self.lock:
                    self.all_results[header] = organized_data
                    
                    # Measure execution time of query
                    end_time = time.time()
                    execution_time = end_time - start_time
                    self.execution_times[header] = execution_time
                    logger.info(f"Execution time for {header}: {execution_time} seconds")

            except Exception as e:
                logger.info(f"Error querying header: {e}")
                show_warning("Ooops... Something went wrong")

        # Loop through all the headers and create a separate thread
        for header in headers:
            header_thread = Thread(target=query_header, args=(header, size)) # Create a thread
            threads.append(header_thread)                                    # Add thread to the list
            header_thread.start()                                            # Start thread

        # Wait for all the threads to finish
        for t in threads:
            t.join()


    def query_sparql_endpoint(self, headers, size):
        # Initialize Lock
        self.lock = Lock()

        # Initialize list of Threads
        threads = []

        self.execution_times = {}

        def query_header(header, size):
            """
            Function query_header that executes a thread for every header
            """
            try:
                # Start time of query
                start_time = time.time()
                recommendations = get_sparql_recommendations(self.custom_endpoint, header)
                organized_data = organize_sparql_results(recommendations)
                end_time = time.time()
                execution_time = end_time - start_time              

                # Lock overwriting the hash map
                with self.lock:
                    self.all_results[header] = organized_data
                    
                    # Measure execution time of query
                    end_time = time.time()
                    execution_time = end_time - start_time
                    self.execution_times[header] = execution_time
                    logger.info(f"Execution time for {header}: {execution_time} seconds")
            except Exception as e:
                logger.info(f"Error querying header: {e}")
                show_warning("Ooops... Something went wrong")


        # Loop through all the headers and create a separate thread
        for header in headers:
            header_thread = Thread(target=query_header, args=(header, size)) # Create a thread
            threads.append(header_thread)                                    # Add thread to the list
            header_thread.start()                                            # Start thread

        # Wait for all the threads to finish
        for t in threads:
            t.join()


    def search_header(self, search_text):
        """
        Function search_header that searches for a header and opens its recommendation popup
        
        Args:
            search_text (str): The header name to search for
        """
        # Convert both search text and headers to lowercase for case-insensitive search
        search_text = search_text.lower().strip()
        
        # Find matching headers
        matching_headers = [h for h in self.headers if h.lower().strip() == search_text]
        
        if matching_headers:
            # Get the exact header (preserving original case)
            header = matching_headers[0]
            # Open recommendations for the found header
            self.open_recommendations(header, self.all_results[header], self.list_titles, self.request_results)
        else:
            # Show warning if header not found
            show_warning("Header not found")


    def process_default_enpoint(self, file_path, headers, size):
        """
        Function process_default_enpoint that processes the default endpoint.
        """
        try:
            # Convert the CSV to metadata JSON
            converter = Thread(target=self.convert_with_cow, args=(file_path,))
            converter.start()
        except Exception as e:
            logger.error(f"Error starting conversion thread: {e}")
            show_warning("Something went wrong with converting your file to metadata. Please try again.")
            self.manager.current = "converter"
            return 

        try:
            logger.info("Requests: Populating the match dictionary")
            query = Thread(target=self.query_linked_open_vocabularies, args=(headers, size))
            query.start()
        except Exception as e:
            logger.error(f"Error starting query thread: {e}")
            self.manager.current = "start"
            return 

        # Wait for both threads to finish
        converter.join(timeout=20)
        query.join(timeout=20)

        # Check if threads completed successfully
        if converter.is_alive() or query.is_alive():
            logger.warning("One or more threads did not complete in time.")
            show_warning("Processing is taking longer than expected. Please try again.")
            self.manager.current = "start"
            return

        # Get all the vocabularies from the request data
        start_time_score = time.time()
        logger.info("Requests: Retrieve vocabulary list")
        vocabs = get_vocabs(self.all_results)

        # Calculate average score for every vocabulary -> compute combi score
        logger.info("Requests: Compute average score and compute Combi Score")
        t = Thread(target=self.compute_scores, args=(vocabs, self.all_results))
        t.start()
        t.join()

        # Retrieve indexes of best matches for every header 
        self.request_results = retrieve_combiSQORE_recursion(self.all_results, self.sorted_combi_score_vocabularies, len(headers))

        logger.info("Requests: Query processing finished")

        # Calculate total execution time of score computation
        end_time_score = time.time()
        total_execution_time_score = end_time_score - start_time_score
        logger.info(f"Total execution time of score computation: {total_execution_time_score} seconds")

        # List of titles with spacings
        self.list_titles = [
            ('prefixedName', dp(60)), 
            ('vocabulary.prefix', dp(60)), 
            ('uri', dp(60)),
            ('type', dp(60)), 
            ('score', dp(60))
        ]
        
    def process_custom_endpoint(self, file_path, headers, size):
        """
        Function process_custom_endpoint that processes the custom endpoint.
        """
        # Convert the CSV to metadata JSO
        converter = Thread(target=self.convert_with_cow, args=(file_path,))

        try:
            logger.info("Requests: Populating the match dictionary")
            query = Thread(target=self.query_sparql_endpoint, args=(headers, size))
        except Exception as e:
            logger.error(f"Error fetching recommendations: {e}")
            self.manager.current = "start"

        converter.start()
        query.start()

        converter.join()
        query.join()

        # Get all the vocabularies from the request data
        # Start time of score computation
        start_time_score = time.time()
        logger.info("Requests: Retrieve vocabulary list")
        vocabs = get_sparql_vocabs(self.all_results)

        # Calculate average score for every vocabulary -> compute combi sqore
        logger.info("Requests: Compute average score and compute Combi Score")
        t = Thread(target=self.compute_sparql_scores, args=(vocabs, self.all_results))
        t.start()
        t.join()


        self.request_results = retrieve_sparql_results(self.all_results, self.sorted_combi_score_vocabularies, len(headers))
        logger.info(f"Request results: {self.request_results}")


        logger.info("Requests: Query processing finished")

        # Calculate total execution time of score computation
        end_time_score = time.time()
        total_execution_time_score = end_time_score - start_time_score
        logger.info(f"Total execution time of score computation: {total_execution_time_score} seconds")

        # List of titles with spacings
        self.list_titles = [
            ('prefixedName', dp(60)), 
            ('vocabulary.prefix', dp(60)), 
            ('uri',dp(60)),
            ('type',dp(60)), 
            ('score',dp(60))
        ]
        # Test the results - return to the starting screen
        self.manager.current = "start"


    def display_recommendation(self, file_path, custom_endpoint=""):
        """
        Function display_recommnedation:
            1. Retreitves the recommendation from the input csv.
            2. Displays the headers on the middle page.
            3. Displays the recommendations on the middle page.
        """
        
        # Initialize a class variable with file path -> reusable in other functions
        self.selected_file = file_path

        self.custom_endpoint = custom_endpoint

        # Load CSV data for table
        try:
            rows = open_csv(file_path)
        except Exception as e:
            logger.warning(f"Error reading file: {e}")
            show_warning("Could not read the file. Please check the file format and encoding.")

        # Get the headers from CSV file
        logger.info("Requests: Retrieving CSV headers")
        headers = get_csv_headers(str(file_path))
        self.headers = headers  # Store headers for search functionality

        # Dictionary {header: list of matches}
        self.all_results = {}

        # Set the size of received matches
        size = 20

        # Processing the endpoint depending on the user input
        if custom_endpoint == "":
            self.process_default_enpoint(file_path, headers, size)
        else:
            self.process_custom_endpoint(file_path, headers, size)

        # Store the display widget
        table = self.ids.vocab_recommender

        # Seperate headers and row data
        self.column_heads = [(header, dp(25)) for header in rows[0]]
        table_rows = rows[1:11] 
        self.row_data = rows [1:]

        # Remove old tables
        if hasattr(self, 'csv_table'):
            self.ids.csv_preview_container.remove_widget(self.csv_table)

        # Create data overwiew table
        self.csv_table = MDDataTable(
            column_data=self.column_heads,
            row_data=table_rows,
            size_hint=(1, 1),
            pos_hint={"center_x": 0.5, "y": 0.6},
            use_pagination=True,
            rows_num = 10
        )

        #self.create_preview_table(file_path)
        # Create buttons for every header
        self.create_header_buttons(headers, self.all_results, table)

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

        # Load Full dataset overview popup
        open_popup = MDRaisedButton(
            text='Load Full Dataset', 
            on_press=lambda x: self.show_popup(self.column_heads,self.row_data), 
            size_hint=(0.5, None),
            pos_hint={"center_x": 0.5, 'y': 0.2}
        )

        self.ids.csv_preview_container.clear_widgets()
        self.ids.csv_preview_container.add_widget(self.csv_table)
        self.ids.csv_preview_container.add_widget(open_popup)


class CowApp(MDApp):
    def build(self):
        """
        Build app function that runs the Screen Manager.
        """
        # Set the adaptive fullScreen mode
        Window.maximize()
        sm = ScreenManager()
        sm.add_widget(StartingScreen(name="start"))      # File Selection Screen
        sm.add_widget(LoadingScreen(name="loading"))     # Loading Screen
        sm.add_widget(ConverterScreen(name="converter")) # Conversion Screen
        return sm

def main():
    CowApp().run()
    
if __name__ == '__main__':
    main()
