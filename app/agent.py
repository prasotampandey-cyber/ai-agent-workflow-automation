from .models import Execution
from .selector import WorkflowSelector
from .workflows import WorkflowExecutor

class Agent:
    def __init__(self, registry, tools, llm=None):
        self.registry=registry
        self.selector=WorkflowSelector(registry,llm)
        self.executor=WorkflowExecutor(tools,llm)

    def run(self, request):
        workflow, selected_by, confidence, reason=self.selector.select(request)
        steps,result=self.executor.execute(workflow,request)
        return {
            "selected_workflow":{"id":workflow.workflow_id,"name":workflow.name,
                                 "selection_method":selected_by,"confidence":confidence,"reason":reason},
            "steps_executed":steps,
            "final_output":result
        }
