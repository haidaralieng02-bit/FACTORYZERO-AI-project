from __future__ import annotations
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LocalRetriever:
    def __init__(self, chunks=None):
        self.chunks=chunks or []; self.vectorizer=None; self.matrix=None
        self._fit()
    def _fit(self):
        if not self.chunks: return
        self.vectorizer=TfidfVectorizer(stop_words="english", ngram_range=(1,2), max_features=12000)
        self.matrix=self.vectorizer.fit_transform([c["text"] for c in self.chunks])
    def search(self, query: str, top_k: int=3):
        if not self.chunks or not query.strip(): return []
        q=self.vectorizer.transform([query]); scores=cosine_similarity(q,self.matrix).ravel(); idxs=scores.argsort()[::-1][:top_k]
        return [{**self.chunks[i],"score":round(float(scores[i]),4)} for i in idxs if scores[i]>0]
