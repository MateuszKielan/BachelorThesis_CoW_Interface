#------------ Imports Section ------------
# Python imports
import json


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
