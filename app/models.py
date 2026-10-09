from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class Workflow:
    workflow_id: str
    name: str
    trigger: str
    inputs: str
    steps: str
    decision_logic: str
    tools_required: str
    expected_output: str

@dataclass
class Execution:
    workflow_id: str
    workflow_name: str
    selected_by: str
    confidence: float
    steps: List[Dict[str, Any]] = field(default_factory=list)
    result: Any = None
    error: str | None = None
