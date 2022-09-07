import nltk
import numpy as np
import spacy
from nltk.corpus import stopwords
import argparse
import subprocess
from nltk.stem import WordNetLemmatizer
from simplemma import text_lemmatizer


def download_model(name):
    subprocess.run(["python", "-m", "spacy", "download", name], capture_output=True)


def sentence_to_stems_spacy(text_arr, model: str = "nl_core_news_lg") -> [str]:
    _stopwords = stopwords.words("dutch")
    text = [text.replace("\n", "").strip() for text in text_arr]
    try:
        nlp = spacy.load(model)
    except IOError as e:
        print(e)
        print("retrying")
        download_model(model)
        nlp = spacy.load(model)
    docs = nlp.pipe(text)
    cleaned_lemmas = [[t.lemma_ for t in doc if t.lemma_ not in _stopwords] for doc in docs][0]
    return cleaned_lemmas

def sentence_to_stems_nltk(text_arr) -> [str]:
    wordnet_lemmatizer = WordNetLemmatizer()
    res = list()
    punctuations = "?:!.,;"
    for sentence in text_arr:
        sentence_words = nltk.word_tokenize(sentence)
        for word in sentence_words:
            if word in punctuations:
                sentence_words.remove(word)
        lemma_words = list(map(lambda x:  wordnet_lemmatizer.lemmatize(x, pos="v"), sentence_words))
        res.append(lemma_words)
    return res

def sentence_to_stems_simplemma(text_arr) -> [str]:
    res = list()
    for text in text_arr:
        text_l = text_lemmatizer(text, lang="nl")
        res.append(text_l)
    return res

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sentence', '-s', type=np.ndarray,
                        default=["Vierkante geglazuurde en roodbruin geëngobeerde witbakkende aardewerken wandtegel "
                                 "met stippen in de hoeken"])
    args = parser.parse_args()

    print("sentence to lemmatize is: \r\n{}".format(args.sentence))
    clean_stems = sentence_to_stems_spacy(args.sentence)
    print("spacy is: \r\n{}".format(clean_stems))
    # result: spacy
    clean_stems = sentence_to_stems_nltk(args.sentence)
    print("nltk is: \r\n{}".format(clean_stems))
    # result: nltk
    clean_stems = sentence_to_stems_simplemma(args.sentence)
    print("simplemma is: \r\n{}".format(clean_stems))
    # result: simplemma

