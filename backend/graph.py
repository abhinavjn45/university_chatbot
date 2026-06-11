import time
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from sqlalchemy import text
from backend.database import engine
from backend.config import settings
from backend import agent
from backend import cache

# Define Graph State
class AgentState(TypedDict):
    question: str
    user_role: str
    student_id: Optional[int]
    chat_history: List[Dict[str, Any]]
    domain: Optional[str]
    generated_sql: Optional[str]
    sql_valid: Optional[bool]
    sql_error: Optional[str]
    query_result: Optional[List[Any]]
    final_response: Optional[str]
    execution_time_ms: Optional[int]
    rows_returned: Optional[int]
    cache_hit: Optional[bool]
    audit_logged: Optional[bool]

# Node 1: Classify Domain
def classify_domain_node(state: AgentState) -> Dict[str, Any]:
    domain = agent.classify_domain(state["question"])
    return {"domain": domain}

# Node 2: Check Cache
def check_cache_node(state: AgentState) -> Dict[str, Any]:
    # We only cache successful runs.
    # Cache key is based on: role + student_id + question
    cache_key = f"qcache:{state['user_role']}:{state.get('student_id')}:{state['question'].strip().lower()}"
    cached_data = cache.cache_get(cache_key)
    
    if cached_data:
        try:
            import json
            data = json.loads(cached_data)
            return {
                "generated_sql": data.get("generated_sql"),
                "query_result": data.get("query_result"),
                "final_response": data.get("final_response"),
                "rows_returned": data.get("rows_returned", 0),
                "cache_hit": True,
                "sql_valid": True
            }
        except Exception:
            pass
            
    return {"cache_hit": False}

# Node 3: Generate SQL
def generate_sql_node(state: AgentState) -> Dict[str, Any]:
    if state.get("cache_hit"):
        return {"cache_hit": True}
        
    sql = agent.generate_sql(
        query=state["question"],
        domain=state["domain"],
        role=state["user_role"],
        student_id=state.get("student_id"),
        chat_history=state.get("chat_history")
    )
    return {"generated_sql": sql}

# Node 4: Validate SQL
def validate_sql_node(state: AgentState) -> Dict[str, Any]:
    if state.get("cache_hit"):
        return {"cache_hit": True}
        
    is_valid, err = agent.validate_sql(
        sql_query=state["generated_sql"],
        role=state["user_role"],
        domain=state["domain"],
        student_id=state.get("student_id")
    )
    if not is_valid:
        return {
            "sql_valid": False,
            "sql_error": err,
            "final_response": f"Query Blocked for Safety: {err}"
        }
    return {"sql_valid": True, "sql_error": None}

# Node 5: Execute Query
def execute_query_node(state: AgentState) -> Dict[str, Any]:
    if state.get("cache_hit"):
        return {"cache_hit": True}
        
    if not state.get("sql_valid"):
        return {"query_result": [], "rows_returned": 0}

    sql = state["generated_sql"]
    start_time = time.time()
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            if result.returns_rows:
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                # Clean Decimals & Dates for JSON response serialization
                for row in rows:
                    for k, v in row.items():
                        import decimal
                        import datetime
                        if isinstance(v, decimal.Decimal):
                            row[k] = float(v)
                        elif isinstance(v, (datetime.date, datetime.datetime)):
                            row[k] = v.isoformat()
                            
                execution_time = int((time.time() - start_time) * 1000)
                return {
                    "query_result": rows,
                    "rows_returned": len(rows),
                    "execution_time_ms": execution_time
                }
            else:
                execution_time = int((time.time() - start_time) * 1000)
                return {
                    "query_result": [],
                    "rows_returned": 0,
                    "execution_time_ms": execution_time
                }
    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        raw_error = str(e)
        role = state.get("user_role")
        
        # Mask detailed database schemas/errors for Students & Faculty (Information Disclosure protection)
        if role in ["Super Admin", "Department Admin"]:
            display_error = raw_error
            logged_error = raw_error
        else:
            display_error = "An unexpected error occurred while executing the query. Please contact the administrator."
            logged_error = "Database execution failed (detailed error hidden for security)."
            
        return {
            "query_result": [],
            "rows_returned": 0,
            "sql_error": logged_error,
            "final_response": f"Database Execution Error: {display_error}",
            "execution_time_ms": execution_time
        }

# Node 6: Format Response
def generate_response_node(state: AgentState) -> Dict[str, Any]:
    if state.get("cache_hit"):
        return {"cache_hit": True}
        
    if state.get("sql_error") or not state.get("sql_valid"):
        return {"sql_valid": state.get("sql_valid")}

    response = agent.format_response(
        query=state["question"],
        sql=state["generated_sql"],
        results=state["query_result"],
        role=state["user_role"]
    )
    
    # Save to Cache
    cache_key = f"qcache:{state['user_role']}:{state.get('student_id')}:{state['question'].strip().lower()}"
    try:
        import json
        cache_data = {
            "generated_sql": state["generated_sql"],
            "query_result": state["query_result"],
            "final_response": response,
            "rows_returned": state["rows_returned"]
        }
        cache.cache_set(cache_key, json.dumps(cache_data), ttl=3600) # 1 hour TTL
    except Exception as e:
        print(f"Error caching result: {e}")
        
    return {"final_response": response}

# Node 7: Log Audit
def audit_logging_node(state: AgentState) -> Dict[str, Any]:
    # Log execution stats
    user_role = state["user_role"]
    student_id = state.get('student_id')
    user_identifier = f"Student ID: {student_id}" if student_id else user_role
    
    question = state["question"]
    generated_sql = state.get("generated_sql")
    response = state.get("final_response")
    execution_time = state.get("execution_time_ms", 0)
    rows = state.get("rows_returned", 0)
    hit = state.get("cache_hit", False)

    try:
        with engine.connect() as conn:
            log_sql = """
            INSERT INTO audit_logs (user_role, question, generated_sql, response, execution_time_ms, rows_returned, cache_hit)
            VALUES (:role, :question, :sql, :resp, :time_ms, :rows, :hit)
            """
            conn.execute(
                text(log_sql),
                {
                    "role": user_identifier,
                    "question": question,
                    "sql": generated_sql,
                    "resp": response,
                    "time_ms": execution_time,
                    "rows": rows,
                    "hit": hit
                }
            )
            conn.commit()
    except Exception as e:
        print(f"Failed writing audit log to DB: {e}")
        
    return {"audit_logged": True}

# Router to determine workflow path based on Cache
def cache_router(state: AgentState):
    if state.get("cache_hit"):
        # Skip generating, validating, executing and formatting. Go straight to Logging
        return "audit_logging"
    else:
        return "generate_sql"

# Router for SQL validation
def sql_validation_router(state: AgentState):
    if state.get("sql_valid") is False:
        # Skip Execution and Response Generation. Go to Logging
        return "audit_logging"
    else:
        return "execute_query"

# Router for SQL execution
def sql_execution_router(state: AgentState):
    if state.get("sql_error") is not None:
        # Database failed. Go straight to logging
        return "audit_logging"
    else:
        return "generate_response"

# Build LangGraph workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("classify_domain", classify_domain_node)
workflow.add_node("check_cache", check_cache_node)
workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("validate_sql", validate_sql_node)
workflow.add_node("execute_query", execute_query_node)
workflow.add_node("generate_response", generate_response_node)
workflow.add_node("audit_logging", audit_logging_node)

# Connect edges
workflow.add_edge(START, "classify_domain")
workflow.add_edge("classify_domain", "check_cache")

# Conditional path after check cache
workflow.add_conditional_edges(
    "check_cache",
    cache_router,
    {
        "generate_sql": "generate_sql",
        "audit_logging": "audit_logging"
    }
)

workflow.add_edge("generate_sql", "validate_sql")

# Conditional path after validation
workflow.add_conditional_edges(
    "validate_sql",
    sql_validation_router,
    {
        "execute_query": "execute_query",
        "audit_logging": "audit_logging"
    }
)

# Conditional path after execution
workflow.add_conditional_edges(
    "execute_query",
    sql_execution_router,
    {
        "generate_response": "generate_response",
        "audit_logging": "audit_logging"
    }
)

workflow.add_edge("generate_response", "audit_logging")
workflow.add_edge("audit_logging", END)

# Compile graph
app_graph = workflow.compile()
