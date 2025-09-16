#------------ Imports Section ------------
# Python imports
import json
import logging

# Kivymd Imports
from kivymd.app import MDApp
#-----------------------------

logger = logging.getLogger(__name__)

def update_metadata(path, headers, all_results, request_results, mode, custom_endpoint):
    """
    Function update_metadata that overwrites the metadata file with the best matches.

    Args:
        headers (str): list of all headers
        all_results (list): list of all matches for every header
        request_results (list): best match index for each header
        mode (str): request mode
        custom_endpoint (str): url to the custom enpoint
    """

    # Open and read the file 
    with open(path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # Buld the lookup index
    index_lookup = {
        header: (idx if mode == 'Homogenous' else 0)
        for header, idx in request_results
    }

    # Insert the best match
    for column in data.get('tableSchema', {}).get('columns', []):
        header = column.get('name')
        if header in all_results and header in index_lookup:
            match = all_results[header][index_lookup[header]]
            column.update({
                'name': header,
                'prefixedName': match[0][0] if custom_endpoint == "" else match[0],
                '@id': match[2][0] if custom_endpoint == "" else match[2],
                'propertyUrl': match[2][0] if custom_endpoint == "" else match[2],
                'vocab': match[1],
                'type': match[3],
                'score': match[4],
            })

    # Write new data into the file
    with open(path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    return path


def insert_instance(row, header, selected_file):
    """
    Inserts the selected match into the metadata file for the current header.

    Args:
        table (MDDataTable): full table data
        row (list): data of the selected row
    """

    # REMEMBER WRITE A CLEANUP FUNCTION
    # Parse and clean the row values
    name = row[0].replace("[", "").replace("]", "")
    vocab = row[1].replace("[", "").replace("]", "")
    uri = row[2].replace("[", "").replace("]", "")
    rdf_type = row[3].replace("[", "").replace("]", "")
    score = float(row[4])

    # Choose the data path with only the name
    data_path = selected_file.parent / f"{selected_file.name[:-4]}-metadata.json"

    # Open the csv file for reading
    with open(data_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # Initialize the flag to track success of the update
    updated = False

    # Loop through all columns in the tableSchema
    for column in data.get('tableSchema', {}).get('columns', []):
        if column.get('name') == header:
            column.update({
                'prefixedName': name,     # prefixed name 
                '@id': uri,               # uri
                'vocab': vocab,           # vocabulary 
                'propertyUrl': uri,        # uri
                'type': rdf_type,         # rdf type
                'score': score            # score
            })

            updated = True # If replaced update the flag
            logger.info(f"[Inserted] {header} -> {name} ({vocab})")

    # Display warning
    if not updated:
        logger.warning(f"Insert Failed: Header '{header}' not found in metadata.")

    # Save the modified data to the file 
    with open(data_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)
        logger.info(f"Metadata File Written: {data_path}")

    # After Insert is Finished close the Popup
    #insert_popup.dismiss()

    # Refresh JSON preview
    app = MDApp.get_running_app()
    app.root.get_screen("converter").show_json()
    logger.info("Converter Screen: Refreshed JSON Preview Screen")


def retrieve_best_match(organized_data, request_results, header):
    """
    Function that retrieves the best results for both single and homogenous requests for a particular header.

    Args:
        organized_data (list) - list of matches for the header
        request_results (list) - list of tuples of the headers and indexes of the best match

    """
    try: 
        index = [item[1] for item in request_results if item[0] == header]

        # Extract the best recommendation for both Single and Homogenous requests
        best_match_data_homogenous = [organized_data[index[0]]]   # Retrieve the match indicated by the index
        best_match_data_single = [organized_data[0]]              # Since matches are already sorted retrieve the first one

    except:
        best_match_data_homogenous = []
        best_match_data_single = []
    
    return best_match_data_homogenous, best_match_data_single