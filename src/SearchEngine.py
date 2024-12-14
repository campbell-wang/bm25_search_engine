from pathlib import Path
import json
from common.SimpleTokenizer import Tokenize
from datetime import datetime
import re
from math import log
import time
import heapq

# BM25 Parameters
K1 = 1.2
B = 0.75

def load_index_data(index_path):
    print("Loading lexicon...")
    with open(index_path / 'metadata/lexicon.json', 'r') as f:
        lexicon = json.load(f)

    print("Loading inverted index...")
    with open(index_path / 'metadata/inverted_index.json', 'r') as f:
        inverted_index = json.load(f)

    print("Loading doc lengths...")
    doc_lengths = []
    total_word_count = 0
    num_docs = 0
    
    with open(index_path / 'doc-lengths.txt', "r") as f:
        for line in f:
            words = int(line.strip())
            total_word_count += words
            doc_lengths.append(words)
            num_docs += 1
    
    avg_doc_length = total_word_count / num_docs

    return lexicon, inverted_index, doc_lengths, num_docs, avg_doc_length

def bm25_search(query_terms, lexicon, inverted_index, doc_lengths, num_docs, avg_doc_length):
    query_terms = set(query_terms)  # avoid duplicates
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
    
    return scored_docs[:10]

def get_document_content(doc_id, index_path):
    docno = None
    with open(index_path / 'docno.txt', 'r') as f:
        for i, line in enumerate(f):
            if i == doc_id:
                docno = line.strip()
                break
    
    if not docno:
        return None, None, None, None

    year, month, day = docno[6:8], docno[2:4], docno[4:6]
    doc_path = index_path / 'documents' / year / month / day / f'{docno}.txt'
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()

    headline_regex = '<HEADLINE>.*?<\/HEADLINE>'
    headline = re.findall(headline_regex, content, re.DOTALL)

    headline_text = 'NULL'
    if headline:
        h = headline[0].split(' ')
        temp = []
        for char in h:
            if char not in ['<P>', '</P>', '<HEADLINE>', '</HEADLINE>']:
                temp.append(char)
        headline_text = ' '.join(temp)

    text_regex = '<TEXT>.*?<\/TEXT>'
    text = re.findall(text_regex, content, re.DOTALL)

    text_content = 'NULL'
    if text:
        t = text[0].split(' ')
        temp = []
        for char in t:
            if char not in ['<P>', '</P>', '<TEXT>', '</TEXT>']:
                temp.append(char)
        text_content = ' '.join(temp)

    graphic_regex = '<GRAPHIC>.*?<\/GRAPHIC>'
    graphic = re.findall(graphic_regex, content, re.DOTALL)

    graphic_text = 'NULL'
    if graphic:
        g = graphic[0].split(' ')
        temp = []
        for char in g:
            if char not in ['<P>', '</P>', '<GRAPHIC>', '</GRAPHIC>']:
                temp.append(char)
        graphic_text = ' '.join(temp)

    full_text = []
    if text_content != 'NULL':
        full_text.append(text_content)
    if graphic_text != 'NULL':
        full_text.append(graphic_text)
        
    combined_text = ' '.join(full_text)
    
    date = datetime.strptime(f'19{year}{month}{day}', '%Y%m%d').strftime('%B %d, %Y')
    
    return headline_text, combined_text, date, docno

def create_snippet(text, query_terms):

    originals = []
    curr_sentence = ""
    
    for char in text:
        curr_sentence += char
        if char in '.!?':
            originals.append(curr_sentence.strip())
            curr_sentence = ""
            
    if curr_sentence.strip():
        originals.append(curr_sentence.strip())

    sentences = [s.strip() for s in originals if s.strip()]
    distinct_query_terms = set(query_terms)
    max_heap = []

    """
    DA RULES
    +2 points if its the first sentence, +1 if its the second, 0 otherwise
    +n points for every matching word in the doc against the query, including repetitions
    +n for number of distinct query terms that match some word in the doc
    """

    for i, sentence in enumerate(sentences):
        l, c, d, k = 0, 0, 0, 0
        tokenized_sentence = Tokenize(re.sub(r'[.!?]$', '', sentence))

        if len(tokenized_sentence) < 5:
            continue
        
        if i == 0:
            l = 2
        elif i == 1:
            l = 1

        curr_run = 0
        max_run = 0
        for token in tokenized_sentence:
            if token in query_terms:
                curr_run += 1
                c += 1
            else:
                max_run = max(max_run, curr_run)
                curr_run = 0
        
        max_run = max(max_run, curr_run)
        k = max_run

        for distinct_term in distinct_query_terms:
            if distinct_term in tokenized_sentence:
                d += 1

        score = l+2*c+4*d+3*k
        max_heap.append((-score, sentence))

    heapq.heapify(max_heap)

    if len(max_heap) >= 2:
        summary = []
        for _ in range(2):
            _, sentence, = heapq.heappop(max_heap)
            
            if sentence.count('"') % 2 != 0:
                sentence = sentence.replace('"', '')
            
            if sentence.count("'") % 2 != 0:
                sentence = sentence.replace("'", '')
                
            summary.append(sentence)
        
        return ' '.join(summary)
    
    elif len(max_heap) == 1:
        return heapq.heappop(max_heap)[1]
    else:
        return " "

def sanitizer(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([.,;!?])', r'\1', text)
    return text.strip()

def view_document(doc_id, index_path):
    docno = None
    with open(index_path / 'docno.txt', 'r') as f:
        for i, line in enumerate(f):
            if i == doc_id:
                docno = line.strip()
                break
    
    if not docno:
        return False

    year, month, day = docno[6:8], docno[2:4], docno[4:6]
    doc_path = index_path / 'documents' / year / month / day / f'{docno}.txt'
    
    with open(doc_path, 'r') as f:
        content = f.read()
        print("\n" + content + "\n")
    return True

def main():
    index_path = Path('/Users/campbellwang/index/')
    
    print("Loading search engine...")
    lexicon, inverted_index, doc_lengths, num_docs, avg_doc_length = load_index_data(index_path)
    
    print("\nSearch engine ready!")
    print("Commands:")
    print("  - Enter your search query and press Enter")
    print("  - Enter a number (1-10) to view a specific document")
    print("  - Enter 'N' for a new search")
    print("  - Enter 'Q' or Ctrl+C to quit")
    
    current_results = []
    
    while True:
        try:
            if not current_results:
                print("Search Query:", end=" ")
                query = input().strip()
                
                if not query:
                    continue
                    
                query_terms = Tokenize(query)
                
                if not query_terms:
                    continue
                
                print("\nSearching...\n", end="", flush=True)
                start_time = time.time()
                
                results = bm25_search(query_terms, lexicon, inverted_index, doc_lengths, num_docs, avg_doc_length)
                
                if not results:
                    print(f"\nNo results found for your query: {query}")
                    continue
                
                print(f"Found {len(results)} results:")
                print("-"*80 + "\n")
                
                for rank, (doc_id, _) in enumerate(results, 1):
                    headline, text, date, docno = get_document_content(doc_id, index_path)

                    text = sanitizer(text)
                    headline = sanitizer(headline)

                    current_results.append(doc_id)
                    snippet = create_snippet(text, query_terms)
                    
                    if headline == 'NULL':
                        headline = snippet[:50] + "..."
                    
                    print(f"{rank}. {headline} ({date})")
                    print(f"{snippet} ({docno})\n")
                
                end_time = time.time()
                print("-"*80)
                print(f"Retrieval took {end_time - start_time:.2f} seconds.")
            
            print(f"\nWhat would you like to do? (1-{len(current_results)}: view document, N: new search, Q: quit)")
            print("Command:", end=" ")
            command = input().strip().upper()
            
            if command == 'Q':
                print("\nExiting...\n")
                break
            elif command == 'N':
                current_results = []
                print("\n" + "-"*80 + "\n")
                continue
            else:
                try:
                    rank = int(command)
                    if 1 <= rank <= len(current_results):
                        doc_id = current_results[rank-1]
                        if not view_document(doc_id, index_path):
                            print("\nError: Could not display document.")
                    else:
                        print("\nError: Please enter a valid rank number between 1 and", len(current_results))
                except ValueError:
                    print("\nError: Please enter a number, 'N', or 'Q'")
                
        except KeyboardInterrupt:
            print("\nExiting...\n")
            break

if __name__ == "__main__":
    main()