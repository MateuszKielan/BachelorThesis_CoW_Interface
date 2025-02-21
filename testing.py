import requests
import csv
import json

# Lov api url
recommender_url = "https://lov.linkeddata.es/dataset/lov/api/v2/term/search"

def get_csv_headers(file_path):
    """
    Function get_csv_header that opens a file and extracts headers from the csv for parsing into the vocabulary

    Params:
        file_path (str) : path of the file
    Return:
        headers (arr) : headers of the csv
    """
    with open(file_path, "r", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        headers = next(reader)
    return headers

def get_recommendations(headers):
    """
    Function get_recommendations that receives headers and runs a get requests to the vocabulary api

    Params:
        headers (arr) : headers of the csv file
    Return:
        None

    """
    for header in headers:
        send = header

        params = {
            "q": send,
            "category": "class", # Here possibly allow the user to switch the type / supervise learning for matching the category
            "page_size": 5 # Manually selected by users
        }

        response = requests.get(recommender_url, params=params)

        results = response.json()
        display_results(results, send)

def display_results(results, send):
    """
    Fucntion display_results that takes query results and displays them in a readable format
    
    Params:
        results (dict) : query results converted to json
    """
    matches = results['results']
    print(f"TOTAL OF {len(matches)} MATCHES FOR {send}")

    for count, match in enumerate(matches):
   
        print(f"-------Match {count + 1}--------")
        print(matches[count]['prefixedName'])
        print(matches[count]['vocabulary.prefix'])
        print(matches[count]['uri'])
        print(matches[count]['type'])
        print(matches[count]['score'])
    print("--------------------------------")



#--------------------------------------------------------------
# Main Function to run the request
def main():
    csv_file = "examples/cow_person_example.csv"
    headers = get_csv_headers(csv_file)
    recommendations = get_recommendations(headers)

if __name__ == "__main__":
    main()
#--------------------------------------------------------------