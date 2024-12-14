from common import SimpleTokenizer
from pathlib import Path
import json
from math import log

K1 = 1.2
B = 0.75

def bm25(query_terms):
    query_terms = set(query_terms)  # avoid dupes
    scores = [0] * num_docs

    for term in query_terms:
        term_id = lexicon.get(term, None)
        posting = None

        if term_id:
            posting = inverted_index.get(str(term_id), None)
        if posting:
            ni = len(posting) // 2
            
            for i in range(0, len(posting), 2):
                doc_id = posting[i]
                fi = posting[i + 1]
                
                k = K1 * ((1-B) + B * doc_lengths[doc_id]/avg_doc_length)
                scores[doc_id] += ((fi / (k+fi)) * log((num_docs-ni+0.5)/(ni+0.5)))

    scored_docs = [(doc_id, score) for doc_id, score in enumerate(scores) if score > 0]
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    return scored_docs[:1000]

def build_output_file(search_results):
    Q0 = 'Q0'
    RUNTAG = 'BM25nostem'
    
    output = []
    for topic_id, doc_results in search_results:
        for rank, (doc_id, score) in enumerate(doc_results, 1):
            docno = get_docno_using_txt(index_path, doc_id)
            output.append(f"{topic_id} {Q0} {docno.strip()} {rank} {score} {RUNTAG}")
    
    return '\n'.join(output)

def get_docno_using_txt(index_path, doc_id):
    cnt = 0
    docno_path = Path(str(index_path) + '/docno.txt')
    
    with open(docno_path, 'r') as file:
        for line in file:
            if cnt == doc_id:
                return line
            cnt += 1

def main():
    global index_path
    index_path = Path('/Users/campbellwang/stemmed_index/') # hardcoded path
    lexicon_path = index_path / 'metadata/lexicon.json'
    inverted_index_path = index_path / 'metadata/inverted_index.json'
    doc_lengths_path = index_path / 'doc-lengths.txt'
    queries_path = Path('queries.txt')
    
    global lexicon
    global inverted_index
    global doc_lengths
    global num_docs
    global avg_doc_length

    print("Loading lexicon...")
    with open(lexicon_path, 'r') as file:
        lexicon = json.load(file)

    print("Loading inverted index...")
    with open(inverted_index_path, 'r') as file:
        inverted_index = json.load(file)

    total_word_count = 0
    doc_lengths = []
    num_docs = 0

    print("Loading doc lengths...")
    with open(doc_lengths_path, "r") as f:
        for line in f:
            words = int(line.strip())
            total_word_count += words
            doc_lengths.append(words)
            num_docs += 1
    
    avg_doc_length = total_word_count / num_docs

    search_results = []
    print("Processing queries...")
    with open(queries_path, 'r') as f:
        for idx, line in enumerate(f):
            if idx % 2 == 0:
                curr_topic = line.strip()
            else:
                query_terms = [word for word in SimpleTokenizer.Tokenize(line.strip())]
                results = bm25(query_terms)
                search_results.append((curr_topic, results))

    output_content = build_output_file(search_results)
    
    print(output_content)
    with open('bm25.txt', 'w') as f:
        f.write(output_content)

if __name__ == '__main__':
    main()