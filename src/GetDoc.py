import sys
from pathlib import Path

def check_directories(docpath):
    p = Path(docpath)
    docs = Path(str(p) + '/documents')
    meta = Path(str(p) + '/metadata')
    if not p.is_dir():
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: Directory does not exist!

                Choose a new directory path, or create the directory using IndexEngine.

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1
    elif not docs.is_dir():
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: Documents subdirectory does not exist!

                Choose a new directory path, or reconstruct using IndexEngine.

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1
    elif not meta.is_dir():
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: Metadata subdirectory does not exist!

                Choose a new directory path, or reconstruct using IndexEngine.

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1
    return 1

def check_docno_file(docpath):
    p = Path(docpath + '/docno.txt')
    if not p.is_file():
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: docno.txt does not exist!

                Choose a new directory path, or reconstruct using IndexEngine.

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1
    return 1

def construct_map(docpath):
    p = Path(docpath)
    global id_to_doc
    id_to_doc = []

    with p.open("r", encoding ="utf-8") as f:
        for doc in f:
            id_to_doc.append(doc)

def docno_helper(docpath, identifier):
    identifier = identifier.strip()
    year, month, day = identifier[6:8], identifier[2:4], identifier[4:6]
    path_to_doc = docpath + f'/documents/{year}/{month}/{day}/{identifier}.txt'
    path_to_meta = docpath + f'/metadata/{year}/{month}/{day}/{identifier}_meta.txt'

    content = ['\n']

    if not Path(path_to_doc).is_file():
        print('''
        # ------------------------------------------------------------------------------------------------

            Error: Docno specified does not exist!

        # ------------------------------------------------------------------------------------------------
        ''')
        return -1
    elif not Path(path_to_meta).is_file():
        print('''
        # ------------------------------------------------------------------------------------------------

            Error: Metadata for docno specified does not exist!

        # ------------------------------------------------------------------------------------------------
        ''')
        return -1
    else:
        with Path(path_to_meta).open("r", encoding ="utf-8") as f:
            for line in f:
                content.append(line)
        content.append('raw document:\n')
        with Path(path_to_doc).open("r", encoding ="utf-8") as f2:
            for l in f2:
                content.append(l)

        print(''.join(content))

def fetch_doc(method, docpath, identifier):
    if method == 'docno':
        docno_helper(docpath, identifier)
    elif method == 'id':
        try:
            docno = id_to_doc[int(identifier)]
            docno_helper(docpath, docno)
        except IndexError:
            print('''
                # ------------------------------------------------------------------------------------------------

                    Error: Internal ID does not exist!

                # ------------------------------------------------------------------------------------------------
            ''')
            return -1
        except ValueError:
            print('''
                # ------------------------------------------------------------------------------------------------

                    Error: Invalid internal ID!

                # ------------------------------------------------------------------------------------------------
            ''')
            return -1


def main():
    if len(sys.argv) != 4:
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: Expected exactly three arguments!

                Usage: python src/GetDoc.py <directory> <docno/id> <identifier>

                Sample: GetDoc /home/smucker/latimes-index docno LA010290-0030
                        GetDoc /home/smucker/latimes-index id 6832

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1
    
    docpath = sys.argv[1]
    method = sys.argv[2]
    identifier = sys.argv[3]

    if method not in ['docno', 'id']:
        print(
            '''
            # ------------------------------------------------------------------------------------------------

                Error: Expecting either docno or id as the search method!

                Usage: python src/GetDoc.py <directory> <docno/id> <identifier>

                Sample: GetDoc /home/smucker/latimes-index docno LA010290-0030
                        GetDoc /home/smucker/latimes-index id 6832

            # ------------------------------------------------------------------------------------------------
            '''
        )
        return -1

    if check_directories(docpath) == -1:
        return -1
    
    if check_docno_file(docpath) == -1:
        return -1
    else:
        construct_map(docpath + '/docno.txt')

    fetch_doc(method, docpath, identifier)

    
if __name__ == '__main__':
    main()