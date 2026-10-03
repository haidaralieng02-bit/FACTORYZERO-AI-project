from __future__ import annotations
from typing import Any
from crewai import Agent, Crew, Task, Process
from crewai.llms.base_llm import BaseLLM
from core.llm_client import LLMClient

class GroqCrewLLM(BaseLLM):
    """Minimal CrewAI BaseLLM adapter backed by the official Groq SDK."""
    def __init__(self, client: LLMClient):
        super().__init__(model="openai/gpt-oss-120b", temperature=0.1)
        self._client=client
    def call(self, messages, tools=None, callbacks=None, available_functions=None, from_task=None, from_agent=None, response_model=None, **kwargs):
        if isinstance(messages, list):
            system_parts=[]; user_parts=[]
            for m in messages:
                role=m.get("role") if isinstance(m,dict) else None
                content=m.get("content","") if isinstance(m,dict) else str(m)
                if role=="system": system_parts.append(str(content))
                else: user_parts.append(str(content))
            system="\n\n".join(system_parts) or "You are a careful engineering decision-support agent."
            user="\n\n".join(user_parts)
        else:
            system="You are a careful engineering decision-support agent."
            user=str(messages)
        raw=self._client.call(system,user)
        return raw
    def supports_function_calling(self): return False
    def supports_stop_words(self): return False

def run_crew_agent(client: LLMClient, role: str, goal: str, backstory: str, prompt: str, expected: str) -> str:
    llm=GroqCrewLLM(client)
    agent=Agent(role=role,goal=goal,backstory=backstory,llm=llm,allow_delegation=False,verbose=False,max_iter=1)
    task=Task(description=prompt,expected_output=expected,agent=agent)
    crew=Crew(agents=[agent],tasks=[task],process=Process.sequential,verbose=False)
    result=crew.kickoff()
    return str(result)
