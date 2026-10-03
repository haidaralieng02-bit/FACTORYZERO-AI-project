from __future__ import annotations
from pathlib import Path
import csv, io, re
from pypdf import PdfReader

def extract_file(path: str | Path) -> list[dict]:
    path=Path(path); suffix=path.suffix.lower(); name=path.name
    if suffix==".pdf":
        reader=PdfReader(str(path)); out=[]
        for page_no,page in enumerate(reader.pages,1):
            text=page.extract_text() or ""
            if text.strip(): out.append({"document":name,"page":page_no,"text":text.strip()})
        return out
    text=path.read_text(encoding="utf-8", errors="replace")
    if suffix==".txt": return [{"document":name,"page":None,"text":text.strip()}] if text.strip() else []
    if suffix==".csv":
        rows=list(csv.DictReader(io.StringIO(text))); joined="\n".join(" | ".join(f"{k}: {v}" for k,v in r.items()) for r in rows)
        return [{"document":name,"page":None,"text":joined}] if joined.strip() else []
    if suffix==".json":
        return [{"document":name,"page":None,"text":str(text)}] if text.strip() else []
    raise ValueError(f"Unsupported document type: {suffix}")

def chunk_text(text: str, chunk_size: int=900, overlap: int=120) -> list[str]:
    clean=re.sub(r"\s+"," ",text).strip()
    if not clean: return []
    chunks=[]; start=0
    while start<len(clean):
        end=min(len(clean),start+chunk_size); chunks.append(clean[start:end])
        if end==len(clean): break
        start=max(0,end-overlap)
    return chunks

def build_chunks(paths) -> list[dict]:
    chunks=[]
    for path in paths:
        for item in extract_file(path):
            for idx,chunk in enumerate(chunk_text(item["text"]),1):
                chunks.append({"document":item["document"],"page":item["page"],"chunk_id":idx,"text":chunk})
    return chunks
