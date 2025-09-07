from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
from preprocessing import preprocess, expand_with_wordnet

def fuzzy_score(a,b):
    return SequenceMatcher(None,a,b).ratio()

class Retriever:
    def __init__(self, raw_questions, raw_answers, use_wordnet=False, stop_words=None, lemmatizer=None):
        self.raw_questions = raw_questions
        self.raw_answers = raw_answers
        self.use_wordnet = use_wordnet
        self.stop_words = stop_words
        self.lemmatizer = lemmatizer
        self.corpus = [preprocess(q, lemmatizer=self.lemmatizer, stop_words=self.stop_words) for q in self.raw_questions]
        to_fit = [expand_with_wordnet(c) if self.use_wordnet else c for c in self.corpus]
        self.vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1,2))
        self.X = self.vectorizer.fit_transform(to_fit)

    def retrieve(self, query, top_k=5, threshold=0.25, dedupe_threshold=0.85):
        q_pre = preprocess(query, lemmatizer=self.lemmatizer, stop_words=self.stop_words)
        if self.use_wordnet:
            q_pre = expand_with_wordnet(q_pre)
        q_vec = self.vectorizer.transform([q_pre])
        sims = cosine_similarity(q_vec, self.X).flatten()
        idxs = sims.argsort()[::-1]
        results = []
        seen_answers = []
        for i in idxs:
            score = float(sims[i])
            if score < 0.01: break
            ans = str(self.raw_answers[i]).strip()
            dup = False
            for sa in seen_answers:
                if fuzzy_score(ans.lower(), sa.lower()) >= dedupe_threshold:
                    dup = True; break
            if dup: continue
            seen_answers.append(ans)
            results.append({"score": score, "question": self.raw_questions[i], "answer": ans})
            if len(results) >= top_k: break
        accepted = [r for r in results if r["score"] >= threshold]
        return accepted, results

    def fuzzy_fallback(self, query, top_k=3, dedupe_threshold=0.85):
        q = query.lower()
        scores = [(i, fuzzy_score(q, self.raw_questions[i].lower())) for i in range(len(self.raw_questions))]
        scores.sort(key=lambda x: -x[1])
        best = []
        seen_answers = []
        for i, s in scores:
            ans = str(self.raw_answers[i]).strip()
            dup = False
            for sa in seen_answers:
                if fuzzy_score(ans.lower(), sa.lower()) >= dedupe_threshold:
                    dup = True; break
            if dup: continue
            seen_answers.append(ans)
            best.append({"score": float(s), "question": self.raw_questions[i], "answer": ans})
            if len(best) >= top_k: break
        return best
