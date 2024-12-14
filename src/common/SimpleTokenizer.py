"""
The tokenizer below is based on SimpleTokenizer by Trevor Strohman, provided by Dr. Mark Smucker
"""
def Tokenize(text):
    tokens = []
    text = text.lower()

    start = 0 
    i = 0

    for currChar in text:
        if not currChar.isdigit() and not currChar.isalpha() :
            if start != i :
                token = text[start:i]
                tokens.append( token )
                
            start = i + 1

        i = i + 1

    if start != i :
        tokens.append(text[start:i])

    return tokens

    
    
