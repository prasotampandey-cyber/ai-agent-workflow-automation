import re

class WorkflowExecutor:
    """Generic dispatcher: workflow definitions come from Excel; handlers are reusable capabilities."""
    def __init__(self, tools, llm=None):
        self.tools, self.llm = tools, llm

    def _missing(self, request, workflow_id):
        # Business-critical input checks. Data can be supplied through request context in a production API.
        if workflow_id=="WF007" and not any(x in request.lower() for x in ["goal","campaign","launch","promotion","collection"]):
            return ["campaign goal"]
        return []

    def execute(self, workflow, request):
        steps=[]; result=None
        def step(name, fn):
            nonlocal result
            result=fn(); steps.append({"step":name,"status":"success"})
            return result

        try:
            missing=self._missing(request,workflow.workflow_id)
            if missing:
                return steps, {"status":"needs_input","missing":missing}

            wid=workflow.workflow_id
            if wid=="WF001":
                result=step("Load inventory and compare stock thresholds",lambda:self.tools.inventory_restock())
            elif wid=="WF002":
                result=step("Match SKUs and calculate vendor/internal price differences",lambda:self.tools.price_validation())
                result={"matches":result,"exceptions":[x for x in result if x["exception"]]}
            elif wid=="WF003":
                result=step("Read, normalize, validate and clean vendor file",lambda:self.tools.process_vendor_file())
            elif wid=="WF004":
                if self.llm:
                    result=step("Generate validated product content with LLM",lambda:self.llm.complete(
                        f"Generate product description, short description, SEO title and meta description. Do not invent attributes; mark missing information. Request: {request}"))
                else:
                    result=step("Validate product attributes and prepare content template",
                                 lambda:{"message":"LLM not configured","missing_attributes":"Provide product attributes/material/color/audience.",
                                         "request":request})
            elif wid=="WF005":
                ids=re.findall(r"ORD-\d+",request.upper())
                result=step("Search order and shipment data",lambda:self.tools.order_status(order_id=ids[0] if ids else None))
                if result is None: result={"status":"not_found","message":"No order found; provide another order ID or customer email."}
            elif wid=="WF006":
                result=step("Normalize identifiers and compare product attributes",self.tools.duplicate_detection)
            elif wid=="WF007":
                if self.llm:
                    result=step("Generate structured campaign brief with LLM",lambda:self.llm.complete(
                        f"Create a structured campaign brief including objective, audience, messaging, channels, timeline and checklist. Do not invent missing facts. Request: {request}"))
                else:
                    result=step("Validate campaign inputs and prepare brief template",
                                 lambda:{"status":"LLM_NOT_CONFIGURED","request":request})
            elif wid=="WF008":
                result=step("Classify keyword intent and map to target pages",self.tools.keyword_classification)
            elif wid=="WF009":
                result=step("Rank employees by required skills and available capacity",lambda:self.tools.assign_task(request))
            elif wid=="WF010":
                result=step("Aggregate execution logs and calculate performance metrics",self.tools.performance_report)
            else:
                raise ValueError(f"No generic capability mapping for {wid}")
            return steps,result
        except Exception as e:
            steps.append({"step":"Error handling","status":"failed","error":str(e)})
            return steps,{"status":"error","message":str(e)}
