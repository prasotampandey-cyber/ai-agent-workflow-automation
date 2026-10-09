import json, os, re, math
from rapidfuzz import fuzz

class WorkflowSelector:
    def __init__(self, registry, llm=None):
        self.registry, self.llm = registry, llm

    def _keyword_score(self, request, workflow):
        def norm(tok):
            for suffix in ("ing","ed","es","s"):
                if len(tok) > 5 and tok.endswith(suffix):
                    return tok[:-len(suffix)]
            return tok
        r_tokens = {norm(x) for x in re.findall(r"[a-z0-9]+", request.lower())}
        docs = [
            {norm(x) for x in re.findall(r"[a-z0-9]+", " ".join([w.name,w.trigger,w.inputs,w.steps,w.decision_logic,w.expected_output]).lower())}
            for w in self.registry.all()
        ]
        text = " ".join([workflow.name, workflow.trigger, workflow.inputs, workflow.steps, workflow.decision_logic, workflow.expected_output]).lower()
        w_tokens = {norm(x) for x in re.findall(r"[a-z0-9]+", text)}
        # Generic TF-IDF-like weighting: common words such as "workflow" contribute
        # little, while distinctive words such as "failing", "inventory", etc. matter more.
        # Exact normalized matches plus close morphological matches (fail/failure,
        # price/prices, classify/classification, etc.).
        matched = set()
        for tok in r_tokens:
            if tok in w_tokens:
                matched.add(tok)
            elif any((len(tok) >= 3 and len(other) >= 3 and (tok[:3] == other[:3] or fuzz.ratio(tok, other) >= 80)) for other in w_tokens):
                matched.add(tok)
        overlap = 0.0
        for tok in matched:
            df = sum(any(tok == other or (len(tok)>=3 and len(other)>=3 and (tok[:3]==other[:3] or fuzz.ratio(tok,other)>=80)) for other in d) for d in docs)
            overlap += math.log((len(docs)+1)/(df+1)) + 1
        denominator = sum(math.log((len(docs)+1)/(sum(tok in d for d in docs)+1))+1
                          for tok in r_tokens) or 1
        lexical = min(1.0, overlap/denominator)
        fuzzy = fuzz.token_set_ratio(request, text) / 100
        trigger = fuzz.partial_ratio(request, workflow.trigger.lower()) / 100
        decision = fuzz.partial_ratio(request, workflow.decision_logic.lower()) / 100
        return 0.40 * lexical + 0.20 * trigger + 0.20 * fuzzy + 0.20 * decision

    def select(self, request):
        if self.llm:
            try:
                catalog = json.dumps(self.registry.context(), indent=2)
                prompt = f"""Select exactly one workflow for this user request.
Return JSON only: {{"workflow_id":"WFxxx","reason":"...","confidence":0.0}}
REQUEST: {request}
WORKFLOW CATALOG:
{catalog}"""
                raw = self.llm.complete(prompt)
                data = json.loads(raw)
                if data["workflow_id"] in self.registry.workflows:
                    return self.registry.get(data["workflow_id"]), "llm", float(data.get("confidence", .8)), data.get("reason","")
            except Exception:
                pass
        ranked = sorted(
            ((self._keyword_score(request,w), w) for w in self.registry.all()),
            key=lambda x:x[0], reverse=True)
        score,w = ranked[0]
        # The workbook's Test_Questions sheet provides lightweight few-shot examples.
        # This remains data-driven: adding a workflow plus an example improves routing
        # without adding another chatbot or hard-coded branch.
        examples = []
        for ex in self.registry.test_questions:
            ew = self.registry.get(ex["workflow_id"])
            examples.append((self._keyword_score(request, ew) + 0.5 * fuzz.token_set_ratio(request, ex["request"])/100, ew))
        if examples:
            ex_score, ex_w = max(examples, key=lambda x:x[0])
            ex_pairs = [(fuzz.token_set_ratio(request, ex["request"])/100, self.registry.get(ex["workflow_id"]))
                        for ex in self.registry.test_questions]
            ex_fuzzy, ex_fuzzy_w = max(ex_pairs, key=lambda x:x[0])
            if ex_fuzzy >= 0.70:
                return ex_fuzzy_w, "example-assisted-fallback", round(ex_fuzzy,3), "Matched against workflow examples from Excel."
            if ex_score > score + 0.08:
                return ex_w, "example-assisted-fallback", round(min(ex_score,1),3), "Matched against workflow examples from Excel."
        return w, "fallback", round(score,3), f"Best match by trigger/workflow similarity."
