import nltk
import string
from nltk.tokenize import word_tokenize
from nltk.stem.porter import PorterStemmer
nltk.download('punkt')



def clean_text(text: str, lower: bool=True, rmv_punc: bool = True, stem: bool = True, norm: bool = True):
    """
    This function accepts a string and performs preprocessing steps on it. 
    
    :param text (str): The string or text on which the preprocessing has to be performed.
    :param lower (bool): Default=True, indicates if the text has to be made into lower case.
    :param rmv_punc (bool): Default=True, indicates if the punctuation should be removed in the text.
    :param stem (bool): Default=True, indicates if the stemming should be performed on the words in the text.
    :param norm (bool): Default=True, indicates if the words in the has to be normalised.
    :return cleaned_text (list): The modified text is returned as list after performing the indicated operations.
    """
    
    # split into words
    tokens = word_tokenize(text)
    if lower:
        # convert to lower case
        tokens = [w.lower() for w in tokens]
    if rmv_punc:
        # remove punctuation from each word
        table = str.maketrans('', '', string.punctuation)
        tokens = [w.translate(table) for w in tokens if w.translate(table) != '']
    if stem:
        # stemming of words
        porter = PorterStemmer()
        tokens = [porter.stem(word) for word in tokens]
    cleaned_text = sorted(list(set(tokens)),key=str.lower)
    return cleaned_text


def search_tags(item, collection):
    clean_query = clean_text(item)
    clean_query_ocr = clean_text(item, lower=True, rmv_punc = False, stem = False, norm = False)
    search_items = clean_query + clean_query_ocr
    return None

def search_bb_and_tags(item, collection):
    return list(collection.find({"$or" : [{"obj_boxes." + item : {"$exists" : True}}, {"tags" : item }]}))

def search_bb(item, collection):
    return list(collection.find({"obj_boxes." + item : {"$exists" : True}}))


def search_country(country, collection):
    return list(collection.find({ "annotation.country" : country}))