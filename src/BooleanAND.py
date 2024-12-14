import sys
import json
from pathlib import Path
from common.SimpleTokenizer import Tokenize
import common.ErrorMessages

def build_output_file(search_results):
    Q0 = 'Q0'
    RUNTAG = 'BooleanAND'

    output = []
    for topic in search_results:
        for i in range(len(topic[2])):
            output.append((topic[0], -(len(topic[2]) - (i + 1)), f'{topic[0]} {Q0} {topic[2][i]} {i+1} {len(topic[2]) - (i + 1)} {RUNTAG}'))

    output.sort()
    
    file_temp_holder = []
    for i in range(len(output)):
        file_temp_holder.append(output[i][-1])
    
    file_output = '\n'.join(file_temp_holder)

    return file_output
    

def build_queries(queries_path):
    topic_ids = []
    terms = []

    with open(queries_path) as f:
        for l in f:
            line = l.strip()

            if line.isdigit():
                topic_ids.append(line)
            else:
                terms.append(line)
    
    queries = list(zip(topic_ids, terms))
    return queries

def build_sorted_query_terms(query):
    topic_id, query_terms = query[0], query[1]
    query_terms = Tokenize(query_terms)

    query_terms_ordered = []

    for term in query_terms:
        # if the term is not in our lexicon, then there's no way it's in our inverted index
        # return a -1 for term id
        postings_length = 0
        term_id = -1
        try:
            term_id = str(lexicon[term])
            posting = inverted_index[term_id]
            postings_length = len(posting)
            query_terms_ordered.append((postings_length, term_id))
        except KeyError:
            query_terms_ordered.append((postings_length, term_id))

    query_terms_ordered.sort()
    return topic_id, query_terms_ordered

def get_docno_using_txt(index_path, doc_id):
    cnt = 0
    docno_path = Path(str(index_path) + '/docno.txt')

    if not docno_path.is_file():
        raise FileNotFoundError(common.ErrorMessages.docno_file_not_found())
    
    with open(docno_path, 'r') as file:
        for l in file:
            line = l.strip()
            if cnt == doc_id:
                return line
            cnt += 1

def boolean_and_search(query_terms):
    result_set = []
    
    try:
        postings = inverted_index[query_terms[0][1]]
    except KeyError:
        return result_set

    for i in range(0, len(postings), 2):
        result_set.append(postings[i])
    
    for t in range(1, len(query_terms)):
        try:
            postings = inverted_index[query_terms[t][1]]
            new_results = []
            j,k = 0,0
            while j < len(result_set) and k < len(postings):
                if result_set[j] == postings[k]:
                    new_results.append(result_set[j])
                    j += 1
                    k += 2
                elif result_set[j] < postings[k]:
                    j += 1
                else:
                    k += 2
            result_set = new_results
        except KeyError:
            return []

    return result_set

def main():
    if len(sys.argv) != 4:
        raise TypeError(common.ErrorMessages.boolean_and_argument_error())
    
    index_path = sys.argv[1]
    queries_path = sys.argv[2]
    output_path = sys.argv[3]

    lexicon_path = Path(index_path + '/metadata/lexicon.json')
    inverted_index_path = Path(index_path + '/metadata/inverted_index.json')
    index_path = Path(index_path)

    if not index_path.is_dir():
        raise FileNotFoundError(common.ErrorMessages.index_directory_not_found())
    elif not lexicon_path.is_file():
        raise FileNotFoundError(common.ErrorMessages.metadata_file_not_found_at_path('Lexicon'))
    elif not inverted_index_path.is_file():
        raise FileNotFoundError(common.ErrorMessages.metadata_file_not_found_at_path('Inverted index'))
        
    global lexicon
    global inverted_index

    print("Loading lexicon...")
    with open(lexicon_path, 'r') as file:
        lexicon = json.load(file)

    print("Loading inverted index...")
    with open(inverted_index_path, 'r') as file:
        inverted_index = json.load(file)

    queries_path = Path(queries_path)
    if not queries_path.is_file():
        raise FileNotFoundError(common.ErrorMessages.generic_file_not_found_at_path('Queries file'))
    
    print("Building search queries...")
    queries = build_queries(queries_path)

    search_results = []
    print("Running BooleanAND search...")
    for query in queries:
        topic_id, query_terms = build_sorted_query_terms(query)
        res = boolean_and_search(query_terms)
        docnos = []
        for doc in res:
            docnos.append(get_docno_using_txt(index_path, doc))

        search_results.append((topic_id, res, docnos))

    output_file = build_output_file(search_results)

    with Path(output_path).open("w", encoding ="utf-8") as f:
        f.write(output_file)
    
    print("BooleanAND complete, results written to: ", output_path)

if __name__ == '__main__':
    main()