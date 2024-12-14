'''

Acknowledgements:

The code below for importing gzip, reading in the gzip file, and fetching the lines from @fferri on StackOverflow:
https://stackoverflow.com/questions/10566558/read-lines-from-compressed-text-files

The code for checking if path exists comes from @phihag (edited by @Mateen Ulhaq) on StackOverflow:
https://stackoverflow.com/questions/8933237/how-do-i-check-if-a-directory-exists-in-python

'''

import gzip
import sys
from pathlib import Path
import re
from collections import defaultdict, Counter
import json
from common.SimpleTokenizer import Tokenize

def dateParser(s):
    parsed = s.split(' ')
    docno = parsed[1]
    
    month = docno[2:4]
    day = docno[4:6]
    year = docno[6:8]

    return docno, year, month, day

def createDirectory(destPath):
    p = Path(destPath)
    docs = destPath + '/documents'
    meta = destPath + '/metadata'
    try:
        p.mkdir(parents=True, exist_ok=False)
        Path(docs).mkdir()
        Path(meta).mkdir()
    except FileExistsError:
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: Directory already exists!

                Choose a new directory path, or delete the existing directory.

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1
    
def saveDocument(date, fileName, file):
    # check if year month day subdirectories exist
    # if so, write file
    # else, create directory then write file

    year, month, day = date

    fileDir = destPath + '/documents/' + year + '/' + month + '/' + day
    filePath = fileDir + '/' + fileName + '.txt'

    if not Path(fileDir).is_dir():
        Path(fileDir).mkdir(parents=True)

    with Path(filePath).open("w", encoding ="utf-8") as f:
        f.write(file)

def processHeadline(headlineInfo, docNo, internal_id):
    headlineRegex = '<HEADLINE>.*?<\/HEADLINE>'
    headline = re.findall(headlineRegex, headlineInfo)

    default = 'NULL'
    temp = []
    output = ''

    if headline:
        h = headline[0].split(' ')
        for char in h:
            if char not in ['<P>', '</P>', '<HEADLINE>', '</HEADLINE>']:
                temp.append(char)
        output = ' '.join(temp)
    else:
        output = default

    buildMeta(output, docNo, internal_id)

    return [] if output == default else Tokenize(output)

def process_graphic(text):
    graphic_regex = '<GRAPHIC>.*?<\/GRAPHIC>'
    graphic = re.findall(graphic_regex, text)

    default = 'NULL'
    temp = []
    output = ''

    if graphic:
        g = graphic[0].split(' ')
        for char in g:
            if char not in ['<P>', '</P>', '<GRAPHIC>', '</GRAPHIC>']:
                temp.append(char)
        output = ' '.join(temp)
    else:
        output = default
        return []
    
    return Tokenize(output)

def process_text(txt):
    text_regex = '<TEXT>.*?<\/TEXT>'
    text = re.findall(text_regex, txt)

    default = 'NULL'
    temp = []
    output = ''

    if text:
        t = text[0].split(' ')
        for char in t:
            if char not in ['<P>', '</P>', '<TEXT>', '</TEXT>']:
                temp.append(char)
        output = ' '.join(temp)
    else:
        output = default
        return []
    
    return Tokenize(output)

def buildMeta(title, docNo, internal_id):
    month = docNo[2:4]
    day = docNo[4:6]
    year = docNo[6:8]

    monthMap = {
        '01': 'January',
        '02': 'February',
        '03': 'March',
        '04': 'April',
        '05': 'May',
        '06': 'June',
        '07': 'July',
        '08': 'August',
        '09': 'September',
        '10': 'October',
        '11': 'November',
        '12': 'December',
    }

    # according to project doc it is guaranteed that all dates are 19xx
    fullDate = f'{monthMap[month]} {day}, 19{year}'

    content = f'docno: {docNo}\ninternal id: {internal_id}\ndate: {fullDate}\nheadline: {title}\n'

    saveMeta(content, (year, month, day), docNo)

def saveMeta(content, date, docNo):
    year, month, day = date

    fileDir = destPath + '/metadata/' + year + '/' + month + '/' + day
    print(fileDir)
    filePath = fileDir + '/' + docNo + '_meta.txt'

    if not Path(fileDir).is_dir():
        Path(fileDir).mkdir(parents=True)

    with Path(filePath).open("w", encoding ="utf-8") as f:
        f.write(content)

def convert_tokens_via_lexicon(tokens_list):
    token_ids = []
    for token in tokens_list:
        if token not in lexicon:
            id = len(lexicon)
            lexicon[token] = id
        token_ids.append(lexicon[token])
    return token_ids

def count_words(token_ids):
    word_counts = Counter(token_ids)
    return word_counts

def add_to_postings(word_counts, doc_id):
    for term_id in word_counts:
        count = word_counts[term_id]
        postings = inverted_index[int(term_id)]
        postings.append(doc_id)
        postings.append(count)

def read(gzPath, destPath):
    gz = Path(gzPath)
    content = []

    docnoList = []
    doc_lengths = []
    internal_id = 0

    docNo, year, month, day = '', '', '', ''

    tokens = []

    global inverted_index
    inverted_index = defaultdict(list)
    global lexicon
    lexicon = defaultdict(int)

    with gzip.open(gz,'rt') as f:
        for line in f:

            l = line.strip()
            content.append(l)

            if '<DOCNO>' and '</DOCNO>' in l:
                docNo, year, month, day = dateParser(l)

            if l == '</DOC>':
                fileToSave = '\n'.join(content)

                full_text = ' '.join(content)

                tokens.extend(processHeadline(full_text, docNo, internal_id))
                tokens.extend(process_graphic(full_text))
                tokens.extend(process_text(full_text))

                token_ids = convert_tokens_via_lexicon(tokens)
                word_counts = count_words(token_ids)
                add_to_postings(word_counts, internal_id)

                doc_lengths.append(str(len(tokens)))
                
                saveDocument((year, month, day), docNo, fileToSave)
                content.clear()
                docnoList.append(docNo)

                tokens.clear()
                internal_id += 1

    docNoList_content = '\n'.join(docnoList)
    with Path(destPath + '/docno.txt').open("w", encoding ="utf-8") as f:
        f.write(docNoList_content)

    doc_lengths_content = '\n'.join(doc_lengths)
    with Path(destPath + '/doc-lengths.txt').open("w", encoding ="utf-8") as f:
        f.write(doc_lengths_content)

    with Path(destPath + '/metadata/lexicon.json').open("w") as f:
        json.dump(lexicon, f)

    with Path(destPath + '/metadata/inverted_index.json').open("w") as f:
        json.dump(inverted_index, f)

def main():
    if len(sys.argv) != 3:
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: Expected exactly two arguments!

                Usage: python src/IndexEngine.py <path to latimes gz file> <path to output directory>

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1
    
    gzPath = sys.argv[1]
    global destPath 
    destPath = str(Path(sys.argv[2]))

    gz = Path(gzPath)
    if not gz.is_file():
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: gz file does not exist at the path provided!

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1

    createPath = createDirectory(destPath)
    if createPath == -1:
        return -1
    
    read(gzPath, destPath)

if __name__ == '__main__':
    main()