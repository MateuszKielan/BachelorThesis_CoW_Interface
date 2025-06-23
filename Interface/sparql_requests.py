from SPARQLWrapper import SPARQLWrapper, JSON
from .utils import get_csv_headers
import difflib
import math


def get_sparql_recommendations(endpoint_url: str, header: str) -> list:
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


def organize_sparql_results(results: list) -> list:
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


def get_sparql_vocabs(all_results: list) -> list:
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


def get_average_sparql_score(vocabs: list, all_results: dict) -> list[tuple]:
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


def normalize_scores(scores: tuple[str, int]) -> tuple[str, int]:
    """
    Function normalize_scores that takes list of scroes and normalizes them according to the min max formula

    Args:
        scores (tuple(int,str)): tuple of vocabularies with corresponding scores
    Returns:
        scores (tuple(int,str)): tuple of voacbularies with corresponding normalized scores
    """
    scores_dict = dict(scores)
    min_score = min(scores_dict.values())
    max_score = max(scores_dict.values())

    for vocab in scores_dict:
        score = scores_dict[vocab]
        normalized_score = (score - min_score) / (max_score - min_score)
        scores_dict[vocab] = normalized_score

    return list(scores_dict.items())


def calculate_sparql_combi_score(all_results: dict, vocab_scores: list[tuple]) -> list[tuple]:
    """
    Function calculate_combi_score that calculates combi score of every vocabulary based on:
        1. SS - Similarity score 
        2. QC - Query coverage 

        Query-Combinative-Ontology Similarity Score = SS * QC

    Args:
        all_results (dict(list())) - data of all headers and all matches.
        vocab_scores (list(tuple))  - list of vocabularies with their corresponding scores.
        necesary_vocabs (list(tuple)) - list of necessary vocabularies identified in necessary vocabs function.

    Returns:
        new_vocab_scores (list(tuple)) - list of vocabularies with the calculated combi score.
    """
    pass

    new_vocab_scores = []

    for vocab in vocab_scores:
        
        vocab_name = vocab[0]
        vocab_similarity_score = vocab[1]
        vocab_query_coverage = 0
        vocab_combi_score = 0

        for header in all_results:
            for match in all_results[header]:

                if match[1] == vocab_name:
                    vocab_query_coverage += 1

        vocab_combi_score = vocab_similarity_score * vocab_query_coverage

        new_vocab_scores.append((vocab_name, vocab_combi_score))

    new_vocab_scores = normalize_scores(new_vocab_scores)

    return new_vocab_scores


def retrieve_sparql_results(all_results: str, vocab_scores: str, num_headers: int, matched=None, unmatched=None) -> list[tuple]:
    if matched is None:
        matched = []
    if unmatched is None:
        unmatched = list(all_results.keys())

    if not vocab_scores:
        print("No more vocabularies to try.")
        return matched

    if len(matched) == num_headers:
        return matched
    
    current_vocab = vocab_scores[0][0]
    print(f"Trying vocabulary: {current_vocab}")

    still_unmatched = []
    
    for header in unmatched:
        found = False
        for idx, match in enumerate(all_results[header]):
            if match[1] == current_vocab:
                print(f"Matched header '{header}' with vocab '{current_vocab}'")
                matched.append((header, idx))
                found = True
                break
        if not found:
            print(f"No match for '{header}' in vocab '{current_vocab}'")
            still_unmatched.append(header)

    return retrieve_sparql_results(all_results, vocab_scores[1:], num_headers, matched, still_unmatched)


if __name__ == "__main__":
    endpoint = "https://dbpedia.org/sparql"
    csv_file = "examples/cow_person_example.csv"
    all_results = {}

    # Get the headers of the CSV file
    headers = get_csv_headers(csv_file)

    # Get the recommendations for each header
    for id, header in enumerate(headers):
        print(f"Getting recommendations for {header}")
        recommendations = get_sparql_recommendations(endpoint, header)
        header_matches = organize_sparql_results(recommendations)
        all_results[header] = header_matches
        print(f"Number of matches for {header}: {len(header_matches)}")

    vocabs = get_sparql_vocabs(all_results)
    print(f"Number of vocabularies: {len(vocabs)}")
    print(f"Vocabularies: {vocabs}")

    # Compute estimated TF-like scores
    scored_results = assign_match_scores(all_results)
    print(scored_results)

    avg_scores = get_average_sparql_score(vocabs, scored_results)
    print(avg_scores)

    combi_scores = calculate_sparql_combi_score(scored_results, avg_scores)
    print(combi_scores)

    request_results = retrieve_sparql_results(all_results, combi_scores, 4)
    print(request_results)
