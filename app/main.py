from .memory import append_memory, build_record
from fastapi import FastAPI, HTTPException
from .models import OpportunityInput, DecisionOutput
from .agent import mock_decision

app = FastAPI(title="Decision-Making AI Agent", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/evaluate", response_model=DecisionOutput)
def evaluate(opportunity: OpportunityInput):
    try:
        decision_output = mock_decision(opportunity)
        append_memory(build_record(opportunity, decision_output))
        return decision_output
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

	 
    


