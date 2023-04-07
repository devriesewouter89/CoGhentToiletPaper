from nltk import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import argparse
import string
from nltk.corpus import wordnet as wn

'''
script to test NLP models to get stem words from sentences and remove stop words.
This methodology can then be used to convert unstructured text to structured, assisting in finding objects with some similarity.
'''


# run once:
# import nltk
# nltk.download()
def start_WordListCorpusReader():
    """
    function to ensure the LazyCorpusLoader is initialized, needs to be called once.(especially use-ful in threaded
    environment)
    """
    print(wn.__class__)  # <class 'nltk.corpus.util.LazyCorpusLoader'>
    try:
        wn.ensure_loaded()  # first access to wn transforms it
    except LookupError as e:
        print(e)
        import nltk
        nltk.download()
        start_WordListCorpusReader()
    print(wn.__class__)  # <class 'nltk.corpus.reader.wordnet.WordNetCorpusReader'>


def sentence_to_stems(text) -> list[str]:
    ps = PorterStemmer()
    _stopwords = stopwords.words("dutch")
    # 1. remove punctuation
    text = text.translate(str.maketrans(dict.fromkeys(string.punctuation)))
    # 2. tokenize the text
    _words = word_tokenize(text, language="dutch")
    # 3. convert to stems
    _stems = list(map(ps.stem, _words))
    # 4. remove stopwords
    _clean_stems = list(filter(lambda w: w not in _stopwords, _stems))
    return _clean_stems


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sentence', '-s', type=str,
                        default="Vierkante geglazuurde en roodbruin geëngobeerde witbakkende aardewerken wandtegel "
                                "met stippen in de hoeken")
    args = parser.parse_args()

    clean_stems = sentence_to_stems(args.sentence)
    print(clean_stems)
