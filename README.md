## Instructions
1. Clone the repo using `git clone`.
2. `cd` into the repo folder.
3. In the project's base directory, you can run
    > python src/IndexEngine.py `<path to latimes archive .gz file>` `<directory to store index>`

    to create the index.
4. After you've created the index, you can run
    > python src/GetDoc.py `<directory to index>` `<query method: docno or id>` `<identifier>`

    to query the data.

5. After you've created the index, you can run
    > python src/BooleanAND.py `<directory to index>` `<path to queries file>` `<path to the output file>`

    to perform Boolean AND search on the index with the queries inside your queries file.

## Sample commands
    python src/IndexEngine.py latimes.gz /Users/campbellwang/index/

    python src/GetDoc.py /Users/campbellwang/index/ docno LA010389-0019

    python src/GetDoc.py /Users/campbellwang/index/ id 513

### BooleanAND Search
    python src/BooleanAND.py /Users/campbellwang/index/ queries.txt results.txt

## How to build and run the BM25 search engine
At the root of the project directory, run 
> python src/SearchEngine.py

to initialize the search engine. You should not need to install any additional dependencies. 
