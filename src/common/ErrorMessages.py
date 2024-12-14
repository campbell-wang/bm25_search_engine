def generic_file_not_found_at_path(file_name):
    return f'{file_name} does not exist at the path provided!'

def metadata_file_not_found_at_path(file_name):
    return f'{file_name} does not exist at the path provided!\nConsider rebuilding the index using IndexEngine to regenerate the {file_name}.'

def boolean_and_argument_error():
    msg = f'Expected exactly three arguments!\nUsage: python src/BooleanAND.py <directory location of index> <directory location of queries file> <name of output file>'

    return msg

def generic_directory_not_found(directory):
    return f"Directory does not exist: {directory}"

def index_directory_not_found():
    return f'Directory does not exist!\nChoose a new directory path, or create the directory using IndexEngine.'

def docno_file_not_found():
    return f'Docno file does not exist at this path!\nChoose a new file path, or recreate the docno file using IndexEngine.'