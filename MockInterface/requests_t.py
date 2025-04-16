import requests
import csv
import json
from copy import deepcopy

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



def get_recommendations(header, size):
    """
    Function get_recommendations that receives headers and runs a get requests to the vocabulary api

    Params:
        headers (arr): headers of the csv file
    Return:
        results (dict): results of the request for the given header

    """
    params = {
        "q": header,
        "category": "class", 
        "page_size": size # Manually selected by users
    }

    response = requests.get(recommender_url, params=params)

    results = response.json()
    
    return results



def display_results(result, name):
    """
    HELPER fucntion display_results that takes query results and displays them in a readable format

    !Only used for debugging!
    
    Params:
        results (dict) : query results converted to json
    """
    matches = result['results']
    print(f"TOTAL OF {len(matches)} MATCHES FOR {name}")

    for count, match in enumerate(matches):
   
        print(f"-------Match {count + 1}--------")
        print(matches[count]['prefixedName'])
        print(matches[count]['vocabulary.prefix'])
        print(matches[count]['uri'])
        print(matches[count]['type'])
        print(matches[count]['score'])
    print("--------------------------------")



def organize_results(result):
    """
    Function organize_results that converts the query result into below specified format.

    Params: 
        - result: retrieved matches for the header
    Return:
        - match_arr (arr(arr)): array with the matches data

        
    TARGET format:

    all_results {
        header1: [match(i),match(i+1),...,match(i+n)]
        header2: [match(i),match(i+1),...,match(i+n)]
    }

    Function takes care of the following part: 
        match(i) = [prefixedName, vocabulary.prefix, uri, type, score]
    """

    # Initialize the array for matches
    match_arr = []
    matches = result['results']

    # For every match create a sub arary with retrieved coresponding data
    for id, match in enumerate(matches):

        sub_match = []
        sub_match.append(matches[id]['prefixedName'])
        sub_match.append(matches[id]['vocabulary.prefix'][0])
        sub_match.append(matches[id]['uri'])
        sub_match.append(matches[id]['type'])
        sub_match.append(matches[id]['score'])

        match_arr.append(sub_match)
    
    return match_arr



def get_vocabs(all_results):
    """
    Function get_vocabs that finds all vocabularies in the recommendation matches.

    Params:
        - all_results (dict): dictionary with matches for all headers
    Return:
        - vocabs (arr): array with unique vocabularies
    """

    # Initialize list of vocabularies
    vocabs = []

    # Add every unique vocabulary from the request result to the list
    for header in all_results:
        for match in all_results[header]:
            if match[1] in vocabs:
                continue
            else:
                vocabs.append(match[1])

    return vocabs



def get_average_score(vocabs, all_results):
    """
    Function get_average_score that computes average score for every distinct vocabulary.

    Params:
        - vocabs (arr): list of all vocabularies.
        - all_results (dict): dictinary with matches for all header.
    Return:
        - vocab_scores (arr(tuple)): array with typles consisting of 
    """     
    # Initialize list of scores that will be filled with tuples of the following format:
    # (vocabulary_name, average_score)
    vocab_scores = []

    # Calculate the average score for every vocabulary and add to the list
    for vocab in vocabs:
        score = 0
        num = 0
        for header in all_results:
            for match in all_results[header]:
                if match[1] == vocab:
                    score += match[4]
                    num += 1
        avg_score = score / num
        vocab_scores.append((vocab, avg_score))

    # Sort the vocabulary list by their corresponding scores in descending order
    vocab_scores = sorted(vocab_scores, key=lambda x: x[1], reverse=True)
    return vocab_scores



def combiSQORE(all_results, vocab_scores):
    """
    Function combiSQORE that leaves only the smallest set of vocabularies that ensures that every header has
    at least one recommendation.

    Params: 
        - all_results (dict(arr)): dictionary with query results for all headers
        - vocab_scores (arr(tuple)): array with vocabularies and their scores sorted in descending order
    Return:
        - combi_vocabs (arr): smallest set of vocabularies that ensuring every header has at least one recommendation

        
    Logic:
        1. Loop through the vocabularies
        2. For every header remove all the results from the current vocabulary
        3. Check if the match list is empty
        4. If no then exclude the vocabulary from the final list 
        5. Repeat for every vocabulary
    """
    # Reverse the list to first exclude the worst performing vocabularies.
    vocab_scores = vocab_scores[::-1]
    combi_vocab = []

    for vocab in vocab_scores:
        necessary = False
        for header in all_results:
            data = deepcopy(all_results[header])
            filtered = [match for match in data if match[1] != vocab[0]]
            if not filtered:
                necessary = True
                break
        if necessary == True:
            combi_vocab.append(vocab)
    
    return combi_vocab




def retrieve_homogenous(best_vocab, all_results):
    """
    Funciton retrieve_homogenous that retrieves the matches based on the best vocabulary

    Params:
        - best_vocab (str): best vocabulary  (see the get_average_scores function)
    Return:
        - request_return (arr(tuple)): array containing tuples with the following format:
            (header, match_index)

    Main logic:
        1. For every header check all the matches
        2. For every match check if it is from a best_vocab
            3. If yes add it to the list and move to the next header
        4. If the header has no matches with the best_vocab, select the first match 
    """

    # Initialize the final list 
    request_return = []

    # For all headers check every match with the best vocabulary
    for header in all_results:
        choice = False
        for index, match in enumerate(all_results[header]):
            if match[1] == best_vocab:
                print(f'Header: {header} Found a match')
                choice = match
                request_return.append((header,index))
                # When match is found terminate immidiately
                break
            else:
                continue
        # If no match is found take the first match for the header 
        if choice == False:
            print("didn't find a match")
            request_return.append((header, 0))
            # To-Do if no matches are found then call combiSQORE again with the remaining data

    return request_return



def retrieve_combiSQORE(best_vocab, all_results):
    """
    Funciton retrieve_homogenous that retrieves the matches based on the best vocabulary based on combiSQORE

    Params:
        - best_vocab (str): best vocabulary  (see the combiSQORE function)
    Return:
        - request_return (arr(tuple)): array containing tuples with the following format:
            (header, match_index)

    Main logic:
        1. For every header check all the matches
        2. For every match check if it is from a best_vocab
            3. If yes add it to the list and move to the next header
        4. If the header has no matches with the best_vocab, select the first match 
    """

    request_return = []
    for header in all_results:
        choice = False
        for index, match in enumerate(all_results[header]):
            if match[1] == best_vocab:
                print(f'Header {header}: FOUND a match for {best_vocab}')
                choice = match
                request_return.append((header,index))
                # When match is found terminate immidiately
                break
            else:
                continue
        # If no match is found take the first match for the header 
        if choice == False:
            print(f"Header {header}: NOT FOUND a match for {best_vocab}")
            request_return.append((header, 0))

    return request_return

    


#--------------------------------------------------------------
# Main Function to run the request
def main():
    """
    Main function to run the test requests
    """
    csv_file = "examples/cow_person_example.csv"
    headers = get_csv_headers(csv_file)
    all_results = {}

    # Get Recommendations for every header
    for id,header in enumerate(headers):
        recommendations = get_recommendations(header, 20)
        header_scores = organize_results(recommendations)
        all_results[header] = header_scores
    
    # Create a list of retrieved vocabularies
    vocabs = get_vocabs(all_results)

    # Calculate a score for every vocabulary
    scores = get_average_score(vocabs, all_results)

    # Find only the necessary vocabularies
    combi_vocabs = combiSQORE(all_results,scores)
    
    # Select the best vocabulary
    best_vocab = scores[0][0]
    best_combi_vocab = combi_vocabs[0][0]
    
    # Retrieve the best results for a homogenous request
    #request_result = retrieve_homogenous(best_vocab, all_results)

    # IF wanna retrieve only with NECESSARY VOCABS
    request_result = retrieve_combiSQORE(best_combi_vocab, all_results)

    # Display the results in readable format
    print(f"\nBest Vocabulary: {best_combi_vocab}")
    print(f"Homogeneous Matches (header -> match):")
    for header, index in request_result:
        match = all_results[header][index]
        print(f"- {header}: {match[0]} ({match[1]}, score={match[4]})")


if __name__ == "__main__":
    main()
#--------------------------------------------------------------