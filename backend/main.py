import time
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.database import get_db, engine
from backend.graph import app_graph
from backend.cache import cache_get, cache_set

# Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.api_rate_limit])

app = FastAPI(
    title="University ERP Conversational Analytics Assistant API",
    description="Backend service converting natural language queries into secure ERP SQL commands.",
    version="1.0"
)

# Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS for React frontend (Vite defaults to 5173)
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Request/Response Schemas
class LoginRequest(BaseModel):
    email: str
    role: str  # 'Student', 'Faculty', 'Department Admin', 'Super Admin'

class ChatRequest(BaseModel):
    message: str
    role: str
    student_id: Optional[int] = None
    session_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    generated_sql: Optional[str] = None
    execution_time_ms: int = 0
    rows_returned: int = 0
    cache_hit: bool = False
    domain: str
    sql_valid: bool = True
    sql_error: Optional[str] = None
    query_result: Optional[List[Dict[str, Any]]] = None

@app.get("/health")
def health_check():
    """Simple service status indicator."""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Simulates logging in.
    Students/Faculty are looked up in the database to retrieve their IDs and confirm they exist.
    """
    role = req.role
    email = req.email.strip()

    if role == "Student":
        # Check student table
        query = text("SELECT student_id, first_name, last_name, enrollment_no FROM students WHERE email = :email")
        result = db.execute(query, {"email": email}).first()
        if not result:
            raise HTTPException(status_code=404, detail="Student email not found in ERP records.")
        return {
            "success": True,
            "role": "Student",
            "student_id": result.student_id,
            "name": f"{result.first_name} {result.last_name}",
            "enrollment_no": result.enrollment_no
        }
    elif role == "Faculty":
        query = text("SELECT faculty_id, first_name, last_name FROM faculty WHERE email = :email")
        result = db.execute(query, {"email": email}).first()
        if not result:
            raise HTTPException(status_code=404, detail="Faculty email not found in ERP records.")
        return {
            "success": True,
            "role": "Faculty",
            "name": f"{result.first_name} {result.last_name}",
            "faculty_id": result.faculty_id
        }
    elif role in ["Department Admin", "Super Admin"]:
        # Standard administrative demo accounts
        return {
            "success": True,
            "role": role,
            "name": f"Demo {role}"
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid ERP role specified.")

@app.post("/chat", response_model=ChatResponse)
@limiter.limit(settings.api_rate_limit)
def chat_endpoint(request: Request, req: ChatRequest):
    """
    Processes chat requests using the LangGraph state workflow.
    Ensures safe, role-restricted SQL queries are executed and answers are formulated.
    """
    # Load session history from cache
    session_key = f"history:{req.session_id}"
    history_raw = cache_get(session_key)
    chat_history = []
    if history_raw:
        try:
            import json
            chat_history = json.loads(history_raw)
        except Exception:
            pass

    # Initialize state
    initial_state = {
        "question": req.message,
        "user_role": req.role,
        "student_id": req.student_id,
        "chat_history": chat_history,
        "domain": None,
        "generated_sql": None,
        "sql_valid": True,
        "sql_error": None,
        "query_result": None,
        "final_response": None,
        "execution_time_ms": 0,
        "rows_returned": 0,
        "cache_hit": False
    }

    try:
        # Run graph
        final_state = app_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant workflow failed: {str(e)}")

    # Update session history if the query was valid
    if final_state.get("sql_valid") and not final_state.get("sql_error"):
        chat_history.append({
            "question": req.message,
            "generated_sql": final_state.get("generated_sql"),
            "response": final_state.get("final_response")
        })
        # Keep last 10 exchanges to prevent token bloat
        chat_history = chat_history[-10:]
        try:
            import json
            cache_set(session_key, json.dumps(chat_history), ttl=86400) # 24 hrs TTL
        except Exception as e:
            print(f"Error saving session history: {e}")

    return ChatResponse(
        response=final_state.get("final_response") or "An error occurred generating response.",
        generated_sql=final_state.get("generated_sql"),
        execution_time_ms=final_state.get("execution_time_ms", 0),
        rows_returned=final_state.get("rows_returned", 0),
        cache_hit=final_state.get("cache_hit", False),
        domain=final_state.get("domain", "academics"),
        sql_valid=final_state.get("sql_valid", True),
        sql_error=final_state.get("sql_error"),
        query_result=final_state.get("query_result")
    )

@app.get("/conversation/{session_id}")
def get_conversation_history(session_id: str):
    """
    Returns the message exchange logs cached for a specific session ID.
    """
    session_key = f"history:{session_id}"
    history_raw = cache_get(session_key)
    if history_raw:
        try:
            import json
            return json.loads(history_raw)
        except Exception:
            pass
    return []

@app.get("/metrics")
def get_analytics_metrics(db: Session = Depends(get_db)):
    """
    Returns metrics and logs of queries processed by the system.
    Calculates cache hit ratios, accuracy ratios, and performance durations.
    """
    try:
        total = db.execute(text("SELECT COUNT(*) FROM audit_logs")).scalar() or 0
        hits = db.execute(text("SELECT COUNT(*) FROM audit_logs WHERE cache_hit = 1")).scalar() or 0
        
        # SQL validation errors or database execution errors
        failures = db.execute(
            text("SELECT COUNT(*) FROM audit_logs WHERE response LIKE 'Query Blocked%' OR response LIKE 'Database Execution Error%'")
        ).scalar() or 0
        
        avg_speed = db.execute(
            text("SELECT AVG(execution_time_ms) FROM audit_logs WHERE cache_hit = 0")
        ).scalar() or 0
        
        # Recent audit logs
        logs_query = text("""
            SELECT log_id, user_role, question, generated_sql, response, execution_time_ms, rows_returned, cache_hit, timestamp 
            FROM audit_logs 
            ORDER BY timestamp DESC 
            LIMIT 20
        """)
        rows = db.execute(logs_query).fetchall()
        
        recent_logs = []
        for r in rows:
            recent_logs.append({
                "log_id": r.log_id,
                "user_role": r.user_role,
                "question": r.question,
                "generated_sql": r.generated_sql,
                "response": r.response,
                "execution_time_ms": r.execution_time_ms,
                "rows_returned": r.rows_returned,
                "cache_hit": bool(r.cache_hit),
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            })
            
        accuracy_rate = 100.0 if total == 0 else ((total - failures) / total) * 100
        cache_hit_rate = 0.0 if total == 0 else (hits / total) * 100
        
        return {
            "total_queries": total,
            "cache_hits": hits,
            "failures": failures,
            "accuracy_rate_percent": round(accuracy_rate, 2),
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "average_execution_speed_ms": round(float(avg_speed), 2) if avg_speed else 0.0,
            "recent_queries": recent_logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
