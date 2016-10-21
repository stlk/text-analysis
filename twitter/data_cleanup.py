import nltk
import re
from nltk.tokenize import RegexpTokenizer
from string import digits
from stopwords_czech import stopwords_czech
from nltk.tokenize import RegexpTokenizer

twitter_stopwords=['amp','get','got','hey','hmm','hoo','hop','iep','let','ooo','par',
            'pdt','pln','pst','wha','yep','yer','aest','didn','nzdt','via',
            'one','com','new','like','great','make','top','awesome','best',
            'good','wow','yes','say','yay','would','thanks','thank','going',
            'new','use','should','could','best','really','see','want','nice',
            'while','know']

url_matcher = '''(([\w\.\-\+]+:)\/{2}(([\w\d\.]+):([\w\d\.]+))?@?(([a-zA-Z0-9\.\-_]+)(?::(\d{1,5}))?))?(\/(?:[a-zA-Z0-9\.\-\/\+\%]+)?)(?:\?([a-zA-Z0-9=%\-_\.\*&;]+))?(?:#([a-zA-Z0-9\-=,&%;\/\\"'\?]+)?)?'''

base_stopwords = nltk.corpus.stopwords.words('english') + twitter_stopwords + stopwords_czech

def cleanup(raw_text):
    raw_text = re.sub(url_matcher, '', raw_text)
    raw_text = re.sub(r'http.*…', '', raw_text)

    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(raw_text.lower())

    unigrams = [w for w in tokens if len(w)==1]
    bigrams = [w for w in tokens if len(w)==2]

    stoplist = set(base_stopwords + unigrams + bigrams)
    tokens = [token for token in tokens if token not in stoplist]

    tokens = [token for token in tokens if len(token.strip(digits)) == len(token)]

    tokens = ' '.join(tokens)

    return tokens
