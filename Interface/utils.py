#-------------------- Import Section --------------------
import pandas as pd
import numpy as np
import typing
import csv
from collections.abc import Iterable
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar
from pathlib import Path
from typing import List
#------------------------------------------

def get_csv_headers(file_path: str) -> list:
    """
    Function get_csv_header that opens a file and extracts headers from the csv for parsing into the vocabulary

    Args:
        file_path (str) : path of the file
    Returns:
        headers (arr) : headers of the csv
    """

    with open(file_path, "r", encoding="utf-8") as csv_file:
        dialect = csv.Sniffer().sniff(csv_file.read(1024))
        csv_file.seek(0)
        reader = csv.reader(csv_file, dialect)
        headers = next(reader)
    return headers


def show_warning(message: str):
        """
        Function show_warning that implements a warning with a custom message.

        Args:
            message (str): message to be displayed
        """
        # Create a Warning display with a custom message
        MDSnackbar(
            MDLabel(
                text=message
            ),
            md_bg_color='#FF0000'
        ).open()


def show_success_message(message: str):
    MDSnackbar(
            MDLabel(
                text=message
            ),
            md_bg_color='#4CAF50'
        ).open()


def open_csv(file_path: Path) -> list:
    """
    Function open_reader that handles opening the file and delimeter detection.
    Uses csv Sniffer to detect the delimeter of the file.

    Args:
        file_path (Path): path of the target csv file
    Returns:
        rows (list): list of row data from the csv file 

    """
    with open(str(file_path), newline='', encoding='utf-8') as csvfile:
            sample = csvfile.read(1024)           # Sample small chunk of the file 

            if not sample.strip():                # If empty return []
                return []
            
            dialect = csv.Sniffer().sniff(sample) # Delimeter detection
                
            csvfile.seek(0)                       # Go back to the first index
            reader = csv.reader(csvfile, dialect) 
            rows = list(reader)

            if not rows:
                return
            
            return rows


def extract_statistics(cols: list, rows: list) -> tuple[int, int, int]:
    """
    Function extract_statistics that takes a dataframe and extracts the follwing:

    Params:
        cols (list): column names of the dataset.
        rows (list): row data of the dataset.

    """
    #
    df = pd.DataFrame(rows, columns=cols)

    null_values = df.isnull().sum()
    num_cols = len(cols)
    num_rows = len(rows)

    return null_values, num_cols, num_rows


def infer_column_type(header: str, file_path: str) -> str:
    """
    Function infer_column_type that checks the type of data for the column for the corresponding header

    Params:
        header (str): header name 
        file_path (str): path to the file 

    Return:
        type (str): type of the column data. Returns "Mixed" if multiple types are detected.
    """

    # Open the file 
    with open(file_path, newline='', encoding='utf-8') as f:
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        reader = csv.DictReader(f, dialect=dialect)
        values = []

        # loop through the rows 
        for row in reader:
            if row[header].strip() != '':
                values.append(row[header])

        # Check for missing values
        if len(values) == 0:
            return "Undefined"

        # Initialize type flags
        has_int = False
        has_bool = False
        has_string = False
        has_iterable = False
        types_found = []

        # Check each value's type
        for v in values:
            if v.isdigit():
                has_int = True
                if "int" not in types_found:
                    types_found.append("int")
            elif v.lower() in ("0", "1", "true", "false"):
                has_bool = True
                if "bool" not in types_found:
                    types_found.append("bool")
            elif isinstance(v, Iterable) and type(v) != str:
                has_iterable = True
                if "iter" not in types_found:
                    types_found.append("iter")
            else:
                has_string = True
                if "str" not in types_found:
                    types_found.append("str")
                

        # If found more than one type, return "Mixed"
        if len(types_found) > 1:
            return "Mixed"

        # Return the single type found
        if has_int:
            return "Integer"
        elif has_bool:
            return "Boolean"
        elif has_iterable:
            return "Iterable"
        else:
            return "String"
