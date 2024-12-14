from nltk.stem import PorterStemmer

# Initialize the Porter Stemmer
ps = PorterStemmer()

# Example words
words = ['running']

# Stem each word
stemmed_words = [ps.stem(word) for word in words]

print(stemmed_words)