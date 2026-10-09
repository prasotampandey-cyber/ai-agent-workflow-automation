from pathlib import Path
import pandas as pd
from .models import Workflow

class WorkflowRegistry:
    """Loads workflow definitions from Excel; no workflow is hard-coded here."""
    def __init__(self, excel_path: str):
        self.excel_path = Path(excel_path)
        self.workflows = self._load()
        self.test_questions = self._load_tests()

    def _load(self):
        df = pd.read_excel(self.excel_path, sheet_name="Workflows").fillna("")
        return {
            row["Workflow_ID"]: Workflow(
                workflow_id=row["Workflow_ID"],
                name=row["Workflow_Name"],
                trigger=row["Trigger"],
                inputs=row["Inputs"],
                steps=row["Steps"],
                decision_logic=row["Decision_Logic"],
                tools_required=row["Tools_Required"],
                expected_output=row["Expected_Output"],
            )
            for _, row in df.iterrows()
        }

    def _load_tests(self):
        df = pd.read_excel(self.excel_path, sheet_name="Test_Questions").fillna("")
        return [{"workflow_id":r["Workflow_ID"],"request":r["Test_Request"]} for _,r in df.iterrows()]

    def all(self):
        return list(self.workflows.values())

    def get(self, workflow_id):
        return self.workflows[workflow_id]

    def context(self):
        return [
            {"id": w.workflow_id, "name": w.name, "trigger": w.trigger,
             "inputs": w.inputs, "steps": w.steps, "decision_logic": w.decision_logic,
             "tools": w.tools_required, "expected_output": w.expected_output}
            for w in self.all()
        ]
