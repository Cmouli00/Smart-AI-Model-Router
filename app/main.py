from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import litellm
import os
from .classifier import classify_complexity
from .database import SessionLocal, RequestLog
from .cache import check_cache, update_cache

app = FastAPI(title="Production AI Cost Router")

class Query(BaseModel):
    prompt: str

# Your specific cost mapping
COST_PER_1K = {
    "gpt-4o": 0.015,       
    "ollama/llama3": 0.005, 
    "ollama/phi3": 0.00    
}

@app.post("/ask")
async def ask_router(query: Query, background_tasks: BackgroundTasks):
    # 1. SEMANTIC CACHE CHECK
    # Check if a similar question was asked recently to save 100% of the cost
    cached_answer = check_cache(query.prompt)
    if cached_answer:
        background_tasks.add_task(log_to_db, query.prompt, "", "cache", 0.00, COST_PER_1K["gpt-4o"])
        return {
            "response": cached_answer, 
            "source": "semantic_cache", 
            "dollars_saved": f"${COST_PER_1K['gpt-4o']:.4f}" 
        }

    # 2. CLASSIFICATION (Using your Phi-3 Logic from classifier.py)
    try:
        tag = classify_complexity(query.prompt)
    except Exception:
        tag = "hard" # Safety fallback to ensure quality if classifier fails

    # 3. ROUTING & CIRCUIT BREAKER LOGIC
    # Define the failover path based on your tag
    if tag in ["medium"]:
        model_stack = ["ollama/llama3", "gpt-4o"]
    elif tag in ["simple"]:
        model_stack = ["ollama/phi3", "gpt-4o"]
    else:
        model_stack = ["gpt-4o"]
    
    final_response = None
    final_model = None

    # Try each model in the stack until one succeeds
    for model in model_stack:
        try:
            final_response = litellm.completion(
                model=model, 
                messages=[{"role": "user", "content": query.prompt}],
                timeout=10 
            )
            final_model = model
            break 
        except Exception:
            continue # Circuit Breaker: move to the next model (e.g., GPT-4o)

    if not final_response:
        raise HTTPException(status_code=503, detail="All LLM providers are currently unavailable")

    answer = final_response.choices[0].message.content

    # 4. CALCULATE SAVINGS & LOG ASYNCHRONOUSLY
    # Compare the cost of GPT-4o vs the model actually used
    actual_cost = COST_PER_1K.get(final_model, COST_PER_1K["gpt-4o"])
    potential_cost = COST_PER_1K["gpt-4o"]
    savings = potential_cost - actual_cost

    # Run these in the background so the user doesn't wait for DB writes
    background_tasks.add_task(update_cache, query.prompt, answer)
    background_tasks.add_task(log_to_db, query.prompt, tag, final_model, actual_cost, savings)

    return {
        "response": answer,
        "complexity": tag,
        "model_used": final_model,
        "dollars_saved": f"${savings:.4f}"
    }

def log_to_db(prompt, tag, model, cost, savings):
    """Saves the transaction details to PostgreSQL for the dashboard."""
    db = SessionLocal()
    try:
        new_log = RequestLog(
            prompt_preview=prompt[:100],
            complexity_tag=tag,
            model_used=model,
            cost_estimate=cost,
            savings_estimate=savings
        )
        db.add(new_log)
        db.commit()
    finally:
        db.close()