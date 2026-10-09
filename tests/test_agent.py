from pathlib import Path
from app.registry import WorkflowRegistry
from app.tools import ToolBox
from app.agent import Agent

ROOT=Path(__file__).resolve().parents[1]
def agent(): return Agent(WorkflowRegistry(ROOT/"data/AI_Agent_Workflow_Assessment.xlsx"),ToolBox())

def test_selection_and_restock():
    r=agent().run("Which products need restocking?")
    assert r["selected_workflow"]["id"]=="WF001"
    assert len(r["final_output"])>0

def test_price_validation():
    r=agent().run("Find products where vendor price differs by more than 10%.")
    assert r["selected_workflow"]["id"]=="WF002"
    assert any(x["exception"] for x in r["final_output"]["exceptions"])

def test_order_not_found():
    r=agent().run("Where is order ORD-9999?")
    assert r["selected_workflow"]["id"]=="WF005"
    assert r["final_output"]["status"]=="not_found"

def test_performance_report():
    r=agent().run("Which workflows are failing most often?")
    assert r["selected_workflow"]["id"]=="WF010"
    assert "failure_rate_pct" in r["final_output"]
