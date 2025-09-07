import re
try:
    import nltk
    from nltk.corpus import stopwords, wordnet
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
    try:
        _ = wordnet.synsets("test"); WORDNET_AVAILABLE = True
    except Exception:
        WORDNET_AVAILABLE = False
except Exception:
    NLTK_AVAILABLE = False; WORDNET_AVAILABLE = False

SIMPLE_STOPWORDS = set("a about above after again against all am an and any are as at be because been before being below between both but by cannot could did do does doing down during each few for from further had has have having he her here hers herself him himself his how i if in into is it its itself let me more most my myself no nor not of on once only or other our ours ourselves out over own same she should so some such than that the their theirs them themselves then there these they this those through to too under until up very was we what when where which while who whom why with would you your yours yourself yourselves".split())

def simple_tokenize(text):
    text = text.lower()
    return re.findall(r"\b[a-z0-9]+\b", text)

def ensure_nltk_data():
    if not NLTK_AVAILABLE: return False
    try:
        nltk.download("stopwords"); nltk.download("punkt"); nltk.download("wordnet")
    except Exception:
        return False
    return True

def preprocess(text, lemmatizer=None, stop_words=None):
    if text is None: return ""
    if NLTK_AVAILABLE:
        try:
            tokens = [t.lower() for t in word_tokenize(text)]
        except Exception:
            tokens = simple_tokenize(text)
    else:
        tokens = simple_tokenize(text)
    out = []
    for t in tokens:
        if len(t) <= 1: continue
        if stop_words and t in stop_words: continue
        if lemmatizer:
            try:
                t = lemmatizer.lemmatize(t)
            except Exception:
                pass
        out.append(t)
    return " ".join(out)

def expand_with_wordnet(text):
    if not WORDNET_AVAILABLE: return text
    tokens = simple_tokenize(text); expanded = list(tokens)
    for t in tokens:
        synsets = wordnet.synsets(t)
        for s in synsets[:3]:
            for lemma in s.lemmas()[:3]:
                name = lemma.name().replace("_"," ")
                if name not in expanded: expanded.append(name)
    return " ".join(expanded)
