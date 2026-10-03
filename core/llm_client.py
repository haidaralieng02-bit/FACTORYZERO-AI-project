from __future__ import annotations
import json, time
from typing import Any
from config import MODEL_NAME, MAX_RETRIES, LLM_TIMEOUT, get_groq_api_key

class LLMClient:
    def __init__(self, api_key: str | None = None):
        self.api_key=api_key or get_groq_api_key()
        self.client=None
        if self.api_key:
            try:
                from groq import Groq
                self.client=Groq(api_key=self.api_key)
            except ImportError as exc:
                raise RuntimeError("The Groq SDK is not installed. Install requirements.txt.") from exc
    @property
    def available(self): return self.client is not None
    def call(self, system_prompt: str, user_prompt: str, temperature: float=0.1) -> str:
        if not self.client: raise RuntimeError("GROQ_API_KEY is not configured.")
        last=None
        for attempt in range(MAX_RETRIES+1):
            try:
                response=self.client.chat.completions.create(model=MODEL_NAME,messages=[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],temperature=temperature,max_completion_tokens=1800,timeout=LLM_TIMEOUT)
                content=response.choices[0].message.content
                if not content: raise RuntimeError("Groq returned an empty response.")
                return content
            except Exception as exc:
                last=exc
                if attempt<MAX_RETRIES: time.sleep(2**attempt)
        raise RuntimeError(f"Groq request failed after retries: {type(last).__name__}: {last}")
    @staticmethod
    def parse_json(raw: str) -> Any:
        text=raw.strip()
        if text.startswith("```"):
            text=text.split("\n",1)[1] if "\n" in text else text
            text=text.rsplit("```",1)[0]
        try: return json.loads(text)
        except json.JSONDecodeError:
            start=min([i for i in (text.find("{"),text.find("[")) if i>=0], default=-1)
            if start<0: raise
            end=max(text.rfind("}"),text.rfind("]"))
            return json.loads(text[start:end+1])
