# This file contains the builder functions for the data popup class responsible for displaying the full csv table

#------ IMPORTS SECTION -------

# KivyMD imports 
from kivymd.uix.datatables import MDDataTable

#-----------------------------


def build_data_table(column_headers: list, row_data: list):         # Change the name of row_data (wtf does that even mean?!!??!?!?!) -> be more specific
    """
    Function build_table that builds the table inspection widget for the whole dataset.

        Params:
            column_headers(arr): list of headers
            row_data(arr): list of data row by row
        Return:
            table(MDDataTable): table with the data from the csv file that is an instance of a MDDatatable class
    
    """

    table = MDDataTable(
            column_data=column_headers,                   # column data 
            row_data=row_data,                            # row data
            size_hint=(0.9, 0.85),                        # size
            pos_hint={"center_x": 0.5, "center_y": 0.5},  # position
            use_pagination=True,                          # enable splitting data into pages
            rows_num=20                                   # maximum row numbers per page
        )

    return table

