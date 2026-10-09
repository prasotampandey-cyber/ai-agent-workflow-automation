import os, json
from pathlib import Path
from dotenv import load_dotenv
from .registry import WorkflowRegistry
from .tools import ToolBox
from .agent import Agent

ROOT=Path(__file__).resolve().parent.parent
load_dotenv(ROOT/".env")

def build_agent():
    llm=None
    if os.getenv("OPENAI_API_KEY"):
        from .llm import LLM
        try: llm=LLM()
        except Exception: pass
    registry=WorkflowRegistry(ROOT/"data"/"AI_Agent_Workflow_Assessment.xlsx")
    return Agent(registry,ToolBox(),llm)

if __name__=="__main__":
    import sys
    request=" ".join(sys.argv[1:]) or "Which products need restocking?"
    print(json.dumps(build_agent().run(request),indent=2,default=str))
