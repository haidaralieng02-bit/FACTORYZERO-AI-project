from rag.retriever import LocalRetriever

def test_retrieval():
    r=LocalRetriever([{"document":"a.txt","page":2,"chunk_id":1,"text":"bearing vibration lubrication"},{"document":"b.txt","page":1,"chunk_id":1,"text":"phase current electrical load"}])
    hits=r.search("bearing vibration",1); assert hits and hits[0]["document"]=="a.txt" and hits[0]["page"]==2
