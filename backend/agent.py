import re
import csv
import io
from openai import OpenAI
from backend.config import settings
from backend.rules import BUSINESS_RULES, DOMAIN_SCHEMAS, ROLE_RESTRICTIONS

# Helper to get Groq client
def get_groq_client():
    if not settings.groq_api_key or settings.groq_api_key == "YOUR_GROQ_API_KEY_HERE" or settings.groq_api_key.strip() == "":
        return None
    return OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1"
    )

def check_api_key_configured() -> bool:
    client = get_groq_client()
    return client is not None

def classify_domain(query: str) -> str:
    """
    Classifies a natural language query into one of the ERP domains using high-speed, 
    zero-token heuristic keyword matching. Saves 100% of LLM domain classification cost.
    """
    q = query.lower()
    
    # Keyword domain mappings
    if any(x in q for x in ["attendance", "present", "absent", "detain", "classes", "log", "roll"]):
        return "attendance"
    elif any(x in q for x in ["fee", "pay", "due", "defaulter", "scholarship", "amount", "paid", "balance", "cost", "revenue"]):
        return "fees"
    elif any(x in q for x in ["faculty", "teacher", "workload", "teach", "professor", "department", "work"]):
        return "faculty"
    elif any(x in q for x in ["admission", "notify", "announcement", "batch", "notification", "alert"]):
        return "administration"
        
    return "academics"

def generate_sql(query: str, domain: str, role: str, student_id: int = None, chat_history: list = None) -> str:
    """
    Generates a secure MySQL query for the user request. Uses compressed prompts to save tokens.
    """
    client = get_groq_client()
    if not client:
        return "ERROR: Groq API Key not configured. Please add your GROQ_API_KEY to backend/.env."

    schema = DOMAIN_SCHEMAS.get(domain, DOMAIN_SCHEMAS["academics"])
    role_restriction = ROLE_RESTRICTIONS.get(role, ROLE_RESTRICTIONS["Student"])
    
    # Conditional student context injection
    student_context = ""
    if role == "Student" and student_id is not None:
        student_context = f"\nUser is Student (id={student_id}). Filter tables by student_id={student_id}."

    # Condensed chat history
    history_str = ""
    if chat_history:
        history_str = "\nHistory:\n"
        for item in chat_history[-2:]: # last 2 turns only
            history_str += f"Q: {item.get('question')} | SQL: {item.get('generated_sql')}\n"

    # High-density, short instructions prompt (approx. 70% smaller)
    prompt = f"""Generate a MySQL SELECT query. Output raw SQL only (no markdown codeblocks or quotes).
Schema: {schema.strip()}
Rules: {BUSINESS_RULES.strip()}
Role Limits: {role_restriction.strip()}{student_context}{history_str}
Question: {query}
SQL:"""

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=150
        )
        sql = response.choices[0].message.content.strip()
        # Clean any accidental code blocks
        sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"^```\s*", "", sql, flags=re.IGNORECASE)
        sql = re.sub(r"\s*```$", "", sql, flags=re.IGNORECASE)
        return sql.strip()
    except Exception as e:
        return f"ERROR: Failed to generate SQL via Groq: {e}"

def validate_sql(sql_query: str, role: str, domain: str, student_id: int = None) -> tuple[bool, str]:
    """
    Validates that the SQL query is read-only, free of injection, and satisfies 
    strict programmatic Role-Based Access Control (RBAC) rules.
    """
    if not sql_query:
        return False, "No SQL query generated."
    
    if sql_query.startswith("ERROR:"):
        return False, sql_query
        
    sql_clean = sql_query.strip().lower()
    
    # Block comments which can be used to bypass filtering or inject commands
    if '--' in sql_clean or '/*' in sql_clean or '*/' in sql_clean or '#' in sql_clean:
        return False, "Security Validation Failed: SQL comments (-- or /* or #) are not allowed in queries."
        
    # Block multiple statements (semicolon check)
    sql_stripped = sql_clean.rstrip(';')
    if ';' in sql_stripped:
        return False, "Security Validation Failed: Multiple SQL statements are not allowed."
    
    if not (sql_clean.startswith("select") or sql_clean.startswith("with")):
        return False, "Unauthorized SQL operation. Only SELECT or WITH queries are allowed."
        
    forbidden_keywords = [
        r'\bdrop\b', r'\bdelete\b', r'\bupdate\b', r'\binsert\b', 
        r'\balter\b', r'\btruncate\b', r'\breplace\b', r'\bcreate\b', 
        r'\bgrant\b', r'\brevoke\b', r'\bexec\b', r'\bexecute\b',
        r'\bload_file\b', r'\boutfile\b', r'\bdumpfile\b', r'\bunion\b'
    ]
    
    for kw in forbidden_keywords:
        if re.search(kw, sql_clean):
            clean_kw = kw.replace(r'\b', '').strip()
            return False, f"Security Validation Failed: Forbidden SQL command '{clean_kw}' detected."
            
    # Programmatic Role-Based Access Control (RBAC) Checks
    if role == "Faculty":
        # Block access to fees domain or fee tables
        if domain == "fees" or any(tbl in sql_clean for tbl in ["fee_structure", "fee_payments", "scholarships"]):
            return False, "Access Denied: Faculty members are not authorized to view financial or fee records."
            
    elif role == "Student":
        # Block access to faculty workload/departments or system logs
        if domain in ["faculty", "administration"] or any(tbl in sql_clean for tbl in ["faculty_workload", "audit_logs"]):
            return False, "Access Denied: Students are not authorized to access faculty workloads or system logs."
            
        # Ensure students only query records matching their own student_id
        sensitive_tables = ["students", "results", "attendance", "fee_payments", "scholarships", "attendance_logs"]
        if any(tbl in sql_clean for tbl in sensitive_tables):
            if student_id is not None:
                id_pattern = f"student_id\s*=\s*{student_id}"
                in_pattern = f"student_id\s+in\s*\(\s*{student_id}\s*\)"
                if not (re.search(id_pattern, sql_clean) or re.search(in_pattern, sql_clean)):
                    return False, f"Access Denied: You are only authorized to access records matching your own Student ID ({student_id})."
            else:
                return False, "Access Denied: Student ID is required to query personal records."
                
    elif role == "Department Admin":
        # Block access to system logs
        if "audit_logs" in sql_clean:
            return False, "Access Denied: Department Admins are not authorized to view system audit logs."
            
    return True, ""

def dict_list_to_csv(results: list) -> str:
    """
    Converts a list of dictionaries to a compact CSV string, reducing token overhead.
    """
    if not results:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
    return output.getvalue().strip()

def format_response(query: str, sql: str, results: list, role: str) -> str:
    """
    Translates raw database rows into a clear, conversational human-readable answer.
    Optimizes tokens through CSV compression, result truncation, and local programmatic shortcuts.
    """
    if not results or len(results) == 0:
        return "No matching records found in the database."

    # 1. Local Bypass: Count and Average shortcuts
    # If result is 1 row and 1 column, and is a count or average, format it locally to save 100% of LLM cost.
    if len(results) == 1 and len(results[0]) == 1:
        col_name = list(results[0].keys())[0]
        val = results[0][col_name]
        col_lower = col_name.lower()
        if "count" in col_lower or col_lower.startswith("cnt"):
            return f"I found a total of {val} matching records."
        elif "avg" in col_lower or "average" in col_lower:
            try:
                # Format average values nicely
                formatted_val = f"{float(val):.2f}" if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '', 1).replace('-', '', 1).isdigit()) else val
                return f"The calculated average is {formatted_val}."
            except Exception:
                pass

    client = get_groq_client()
    if not client:
        return f"Query returned {len(results)} rows. (Configure GROQ_API_KEY for conversational summary)."

    # 2. Adaptive Truncation & CSV Compression
    total_count = len(results)
    is_truncated = total_count > 3
    sample_results = results[:3] if is_truncated else results
    
    csv_data = dict_list_to_csv(sample_results)
    
    # High-density summary prompt instructing LLM to avoid drawing assumptions about unseen rows
    prompt = f"""User Question: {query}
SQL Query executed: {sql}
Total Database Rows: {total_count}
Results (CSV format, showing first 3 of {total_count} rows):
{csv_data}
""" if is_truncated else f"""User Question: {query}
SQL Query executed: {sql}
Total Database Rows: {total_count}
Results (CSV format):
{csv_data}
"""

    prompt += "\nSynthesize a brief, friendly, conversational summary of the results in 1-2 short sentences. DO NOT output a markdown table or duplicate the data list, as the frontend will render the complete table. Simply tell the user what was found."

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"I processed the query and found {total_count} rows. (Summary generation failed: {e})"
