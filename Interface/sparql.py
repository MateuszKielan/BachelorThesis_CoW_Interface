from SPARQLWrapper import SPARQLWrapper, JSON

def query_sparql_endpoint(endpoint_url: str, header: str) -> list:
    """
    Query a SPARQL endpoint and return the results as a list of bindings.

    Args:
        endpoint_url (str): The URL of the SPARQL endpoint.
        sparql_query (str): The SPARQL query to execute.

    Returns:
        list: A list of result bindings (dictionaries).
    """

    sparql_query ="""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX dct: <http://purl.org/dc/terms/>
    SELECT ?uri ?namespace ?class ?label ?comment ?description WHERE {
        ?uri rdfs:label ?label .
        
        FILTER (?label = "Person"@en || ?label = "Person" || ?label = "{header}") 

        OPTIONAL { ?uri rdfs:comment ?comment . FILTER(LANG(?comment) = "en") }
        OPTIONAL { { ?uri dc:description ?description . } UNION { ?uri dct:description ?description . } FILTER(LANG(?description) = "en") }
        OPTIONAL { ?uri rdf:type ?class . }

        # Extract vocabulary (namespace)
        BIND(REPLACE(STR(?uri), "/[^/#]*$", "/") AS ?namespace)
    } LIMIT 10
    """

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


if __name__ == "__main__":
    endpoint = "https://dbpedia.org/sparql"

    results = query_sparql_endpoint(endpoint, 'Person')
    
    print(extract_results(results))

