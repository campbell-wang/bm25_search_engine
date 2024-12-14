from collections import defaultdict
from math import log2
import sys

def load_qrels(qrels_path):
    # { 
    #   topic -> {docno -> rel}
    # }
    qrels = defaultdict(dict)
    with open(qrels_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 4:
                topic, _, docno, rel = parts
                qrels[topic][docno] = int(rel)
    return qrels

def average_precision(qrels, topic, results):
    # get relevant docs from qrels   
    relevant_docs = {docno for docno, rel in qrels[topic].items() if rel > 0}

    if not relevant_docs:
        return 0.000
        
    precisions = []
    num_rel_docs = 0

    for rank, docno in enumerate(results, 1):
        if docno in relevant_docs:
            num_rel_docs += 1
            precisions.append(num_rel_docs / rank)
            
    return sum(precisions) / len(relevant_docs)

def precision_cut_k(qrels, topic, results, k):
    results_cut_k = results[:k]
    num_rel_docs = 0

    for docno in results_cut_k:
        if docno in qrels[topic] and qrels[topic][docno] > 0:
            num_rel_docs += 1

    return num_rel_docs / k

def dcg_cut_k(qrels, topic, results, k):
    dcg = 0.000
    results_cut_k = results[:k]

    # DCG@k = sum[i = 1 -> k] ( G(i) / log2(i+1) )
    for rank, docno in enumerate(results_cut_k, 1):
        # not judged = not relevant
        # G(i) = 1 if rel else 0
        gain = 0
        if docno in qrels[topic] and qrels[topic][docno] > 0:
            gain = 1
        
        dcg += gain / (log2(rank + 1))

    return dcg

def ideal_dcg_cut_k(qrels, topic, k):
    relevant_docs = [docno for docno, rel in qrels[topic].items() if rel > 0]
    
    # since we are using binary relevance (0 = not relevant, 1 = relevant) so order doesn't matter
    # ideal dcg = all relevant docs will be on top
    # take up to either k or number of rel docs from qrels

    idcg = 0.000
    for rank in range(min(len(relevant_docs), k)):
        idcg += 1 / log2(rank + 2)
    return idcg

def ndcg_cut_k(qrels, topic, results, k):
    idcg = ideal_dcg_cut_k(qrels, topic, k)
    if idcg == 0.000:
        return 0.000
    
    dcg = dcg_cut_k(qrels, topic, results, k)
    
    return dcg / idcg

def evaluate_topic(qrels, topic, results):
    return {
        'ap': average_precision(qrels, topic, results),
        'P_10': precision_cut_k(qrels, topic, results, 10),
        'ndcg_cut_10': ndcg_cut_k(qrels, topic, results, 10),
        'ndcg_cut_1000': ndcg_cut_k(qrels, topic, results, 1000)
    }

def sort_results(lines):
    parsed = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) != 6:
            print("Error: Results file is formatted incorrectly. Expecting columns: topic Q0 docno rank score tag")
            sys.exit()
        try:
            topic = int(parts[0])
            rank = int(parts[3])
            score = float(parts[4])
            docno = parts[2]
            if parts[1] != 'Q0' or not docno or len(docno) != 13:
                print("Error: Results file is formatted incorrectly. Detected error in Q0 and/or docno columns.")
                sys.exit()
            parsed.append((topic, score, docno, line))
        except ValueError:
            print("Error: Results file is formatted incorrectly. Detected error in topic/rank/score columns.")
            sys.exit()

    # sort by topic -> score -> docno
    parsed.sort(key=lambda x: (x[0], -x[1], x[2]))
    return [line[3] for line in parsed]
    
def load_results(results_path):
    topics = set(str(i) for i in range(401, 451) if i not in {416, 423, 437, 444, 447})
    results = {topic: [] for topic in topics}
    
    try:
        with open(results_path) as f:
            lines = f.readlines()
            sorted_lines = sort_results(lines)
            
            for line in sorted_lines:
                parts = line.strip().split()
                topic, docno = parts[0], parts[2]
                
                if topic in topics:
                    results[topic].append(docno)
                    
    except FileNotFoundError:
        print(f"Error: Could not open results file at {results_path}")
        sys.exit()

    return results

def main():

    if len(sys.argv) != 3:
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: Expected exactly three arguments!

                Usage: python src/TopicEvaluator.py <path to qrels file> <path to results file>

                Sample: python src/TopicEvaluator.py LA-only.trec8-401.450.minus416-423-437-444-447.txt student1.results

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1
    
    qrels_path = sys.argv[1]
    results_path = sys.argv[2]

    qrels = load_qrels(qrels_path)
    results = load_results(results_path)

    # this method of printing tables is from:
    # https://learnpython.com/blog/print-table-in-python/
    print("\nScores:")
    print("-" * 70)
    print(f"{'Topic':>6} {'AP':>10} {'P@10':>10} {'NDCG@10':>10} {'NDCG@1000':>10}")
    print("-" * 70)

    metrics_sums = defaultdict(float)
    topics = 45

    for topic in sorted(results.keys()):
        scores = evaluate_topic(qrels, topic, results[topic])
        print(f"{topic:>6} {scores['ap']:>10.3f} {scores['P_10']:>10.3f} {scores['ndcg_cut_10']:>10.3f} {scores['ndcg_cut_1000']:>10.3f}")
        for metric, value in scores.items():
            metrics_sums[metric] += value

    print("-" * 70)
    print(f"{'Mean':>6} {metrics_sums['ap']/topics:>10.3f} {metrics_sums['P_10']/topics:>10.3f} {metrics_sums['ndcg_cut_10']/topics:>10.3f} {metrics_sums['ndcg_cut_1000']/topics:>10.3f}")

if __name__ == "__main__":
    main()