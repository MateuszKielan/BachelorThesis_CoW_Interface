from SPARQLWrapper import SPARQLWrapper, JSON
from utils import get_csv_headers
import difflib
import math


def query_sparql_endpoint(endpoint_url: str, header: str) -> list:
    """
    Query a SPARQL endpoint and return the results as a list of bindings.

    Args:
        endpoint_url (str): The URL of the SPARQL endpoint.
        sparql_query (str): The SPARQL query to execute.

    Returns:
        list: A list of result bindings (dictionaries).
    """

    sparql_query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX dct: <http://purl.org/dc/terms/>
    SELECT ?uri ?namespace ?class ?label ?comment ?description WHERE {{
        ?uri rdfs:label ?label .
        
        FILTER (?label = "{header}"@en || ?label = "{header}" || ?label = "{header}") 

        OPTIONAL {{ ?uri rdfs:comment ?comment . FILTER(LANG(?comment) = "en") }}
        OPTIONAL {{ {{ ?uri dc:description ?description . }} UNION {{ ?uri dct:description ?description . }} FILTER(LANG(?description) = "en") }}
        OPTIONAL {{ ?uri rdf:type ?class . }}

        # Extract vocabulary (namespace)
        BIND(REPLACE(STR(?uri), "/[^/#]*$", "/") AS ?namespace)
    }} LIMIT 20
    """.format(header=header)
    
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    
    try:
        response = sparql.query().convert()
        results = response["results"]["bindings"]
        return results
    except Exception as e:
        print(f"Error querying SPARQL endpoint: {e}")
        return []


def print_results(results: list) -> None:
    """
    Helper function to print the results of the SPARQL query for debugging purposes.

    Args:
        results (list): A list of result bindings (dictionaries).

    Returns:
        None
    """
    for res in results:
        print("--------------------------------")
        print("URI:", res['uri']['value'])
        print("Label:", res['label']['value'])
        if 'class' in res:
            print("Class:", res['class']['value'])
        if 'comment' in res:
            print("Comment:", res['comment']['value'])
        if 'description' in res:
            print("Description:", res['description']['value'])
        if 'namespace' in res:
            print("Namespace:", res['namespace']['value'])
        if 'type' in res:
            print("Type:", res['type']['value'])


def extract_results(results: list) -> list:
    """
    Function extract_results that extracts the results from the SPARQL query and returns a list of matches.

    Args:
        results (list): A list of result bindings (dictionaries).

    Returns:
        list: A list of matches.
    """
    match_arr = []

    for res in results:
        sub_match = []
        if 'label' in res:
            sub_match.append(res['label']['value'])        # prefixedName
        if 'namespace' in res:
            sub_match.append(res['namespace']['value'])    # vocabulary.prefix
        if 'uri' in res:
            sub_match.append(res['uri']['value'])          # uri
        if 'class' in res:
            sub_match.append(res['class']['value'])        # type
        if 'comment' in res:
            sub_match.append(res['comment']['value'])      # comment
        if 'description' in res:
            sub_match.append(res['description']['value'])  # description

        match_arr.append(sub_match)
    
    return match_arr


def get_vocabs(all_results: list) -> list:
    """
    Function get_vocabs that extracts the vocabularies from the SPARQL query results.

    Args:
        all_results (list): A list of result bindings (dictionaries).

    Returns:
        vocabs (list): A list of vocabularies.
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


def compute_similarity(header, text):
    """
    Compute similarity between header and target text (label, comment, etc.)
    using difflib's SequenceMatcher ratio (0 to 1).
    """
    return difflib.SequenceMatcher(None, header.lower(), text.lower()).ratio()


def assign_match_scores(all_results):
    """
    Assign a similarity score to each match based on header-to-label similarity.
    
    Args:
        all_results (dict): {header: list of matches}
    
    Returns:
        dict: {header: list of (match, similarity_score)}
    """
    scored_results = {}

    for header in all_results:
        
        for index, match in enumerate(all_results[header]):
            label = match[0]
            similarity_score = compute_similarity(header, label)
            match.append(similarity_score)
            all_results[header][index] = match

    return all_results


def get_average_score(vocabs: list, all_results: dict) -> list[tuple]:
    """
    Function get_average_score that computes average score for every distinct vocabulary.

    Args:
        - vocabs (arr): list of all vocabularies.
        - all_results (dict): dictinary with matches for all header.
    Returns:
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


def calculate_combi_score(all_results: dict, vocab_scores: list[tuple]) -> list[tuple]:
    """
    Function calculate_combi_score that calculates combi score of every vocabulary based on:
        1. SS - Similarity score 
        2. QC - Query coverage 

        Query-Combinative-Ontology Similarity Score = SS * QC

    Args:
        all_results (dict): {header: list of matches}
    """
    pass


if __name__ == "__main__":
    endpoint = "https://dbpedia.org/sparql"
    csv_file = "examples/cow_person_example.csv"
    all_results = {}

    # Get the headers of the CSV file
    headers = get_csv_headers(csv_file)

    # Get the recommendations for each header
    for id, header in enumerate(headers):
        print(f"Getting recommendations for {header}")
        recommendations = query_sparql_endpoint(endpoint, header)
        header_matches = extract_results(recommendations)
        all_results[header] = header_matches
        print(f"Number of matches for {header}: {len(header_matches)}")

    vocabs = get_vocabs(all_results)
    print(f"Number of vocabularies: {len(vocabs)}")
    print(f"Vocabularies: {vocabs}")
