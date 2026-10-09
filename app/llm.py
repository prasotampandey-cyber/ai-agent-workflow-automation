import os
from openai import OpenAI

class LLM:
    def __init__(self):
        key=os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        self.client=OpenAI(api_key=key)
        self.model=os.getenv("OPENAI_MODEL","gpt-4o-mini")

    def complete(self, prompt):
        resp=self.client.chat.completions.create(
            model=self.model,
            messages=[{"role":"system","content":"You are a workflow automation agent. Follow the requested output format exactly."},
                      {"role":"user","content":prompt}],
            temperature=0
        )
        return resp.choices[0].message.content
