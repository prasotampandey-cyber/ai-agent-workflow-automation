# AI Agent Workflow Automation

An Excel-driven, reusable AI agent that selects one of 10 business workflows, executes reusable tools, applies workflow decisions, handles errors, and returns an execution trace.

## Architecture

```text
User Request
     |
     v
Workflow Agent
     |
     +--> Workflow Selector (LLM JSON selection + deterministic fallback)
     |
     v
Excel Workflow Registry
     |
     v
Generic Workflow Executor
     |
     +--> Reusable Tool Adapters
     |      + CSV/XLSX reader
     |      + calculator
     |      + mock order API/database
     |      + similarity
     |      + ranking
     |      + reporting
     |      + LLM generation
     |
     v
Conditions / Error Handling
     |
     v
Execution Trace + Final Result
```

### Why this is scalable

The Excel workbook is the source of truth for workflow metadata. The selector does not contain 10 independent chatbot prompts. The executor contains reusable capabilities/tool adapters and a single dispatch layer. To add workflow 11:

1. Add one row to `Workflows` in the Excel file.
2. Add/compose only the missing reusable capability if the new workflow needs a new tool.
3. Add one test/example.

This keeps selection, logging, error handling and presentation unchanged.

## Included workflows

WF001 Inventory Restock Check  
WF002 Product Price Validation  
WF003 Vendor File Processing  
WF004 Product Description Generator  
WF005 Customer Order Status  
WF006 Duplicate Product Detection  
WF007 Marketing Campaign Brief  
WF008 SEO Keyword Classification  
WF009 Employee Task Assignment  
WF010 Workflow Performance Report

The original assignment workbook is included at `data/AI_Agent_Workflow_Assessment.xlsx`.

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Optional LLM configuration:

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

Without an API key, workflow selection uses a deterministic similarity fallback and LLM-heavy workflows return a safe configuration message. All non-LLM workflows remain runnable with the included mock data.

## Run

CLI:

```bash
python -m app.main "Which products need restocking?"
python -m app.main "Find products where vendor price differs by more than 10%."
python -m app.main "Where is order ORD-1001?"
```

UI:

```bash
streamlit run streamlit_app.py
```

## Tests

```bash
pytest -q
```

## Tool/API simulation

Because real enterprise APIs were not supplied, the project uses adapters over `data/mock/`. In production, these adapters can be replaced by REST/database clients without changing the agent, selector, execution trace or workflow registry.

## Error and condition handling

- WF001 flags only products where `current_stock < minimum_stock`.
- WF002 flags differences greater than 10%.
- WF003 rejects rows missing SKU or product name.
- WF004 does not invent missing attributes; it marks them.
- WF005 returns a structured not-found response and asks for another identifier.
- WF006 distinguishes definite SKU duplicates from possible attribute matches.
- WF007 requests missing campaign-critical information.
- WF009 escalates when no candidate meets minimum suitability.
- WF010 flags failure rates above 10% and reports slow workflows.

## Example response shape

```json
{
  "selected_workflow": {
    "id": "WF001",
    "name": "Inventory Restock Check",
    "selection_method": "fallback",
    "confidence": 0.91
  },
  "steps_executed": [
    {"step": "Load inventory and compare stock thresholds", "status": "success"}
  ],
  "final_output": []
}
```

## Loom demo script

1. Show the Excel `Workflows` sheet and explain it is the workflow registry.
2. Show the architecture diagram in this README.
3. Run the Streamlit app with the WF001 request.
4. Point out selected workflow, confidence, executed steps and final result.
5. Run WF002 to demonstrate a decision condition (>10%).
6. Run WF005 with an invalid order ID to demonstrate error handling.
7. Run WF004 with an API key to demonstrate LLM-generated structured content and missing-attribute handling.
8. Explain that mock adapters simulate unavailable enterprise APIs.
9. Add an 11th row to Excel and explain that the same selector/executor/trace infrastructure remains reusable.

## Engineering decisions

- **Excel:** business users can edit workflow metadata without changing application code.
- **LLM:** used where language understanding/generation adds value; deterministic tools own calculations and business rules.
- **Adapters:** isolate external APIs/data sources from orchestration.
- **Structured result:** makes the system observable and easy to evaluate.
- **Fallback selector:** allows local execution/testing without an API key.
