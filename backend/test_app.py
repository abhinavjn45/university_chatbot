import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agent import validate_sql, classify_domain
from backend.cache import InMemoryCache, get_query_hash

def test_sql_validation():
    print("Running SQL Validation & Safety Tests...")
    
    # Test valid queries (Admin access)
    valid_queries = [
        "SELECT * FROM students",
        "SELECT cgpa, first_name FROM students WHERE student_id = 1",
        "WITH active_sems AS (SELECT semester_id FROM semesters WHERE is_active = 1) SELECT * FROM results WHERE semester_id IN (SELECT semester_id FROM active_sems)",
        "SELECT student_id, COUNT(*) FROM attendance GROUP BY student_id HAVING COUNT(*) > 1 LIMIT 10",
        "select email from faculty"
    ]
    
    for q in valid_queries:
        ok, err = validate_sql(q, role="Super Admin", domain="academics")
        assert ok, f"Query '{q}' should be valid for Super Admin. Error: {err}"
        print(f"  [PASS] Valid query allowed: '{q[:40]}...'" if len(q) > 40 else f"  [PASS] Valid query allowed: '{q}'")

    # Test invalid/malicious queries (Injection tests)
    invalid_queries = [
        "DROP TABLE students",
        "DELETE FROM students WHERE student_id = 1",
        "UPDATE students SET cgpa = 10.00 WHERE student_id = 1",
        "INSERT INTO students (first_name) VALUES ('Hacker')",
        "ALTER TABLE students ADD COLUMN hacked VARCHAR(100)",
        "TRUNCATE TABLE audit_logs",
        "CREATE TABLE test (id int)",
        "SELECT * FROM students; DROP TABLE results", 
        "GRANT ALL PRIVILEGES ON *.* TO 'hacker'@'%'",
        "SELECT LOAD_FILE('/etc/passwd')"
    ]

    for q in invalid_queries:
        ok, err = validate_sql(q, role="Super Admin", domain="academics")
        assert not ok, f"Query '{q}' should have been blocked!"
        print(f"  [PASS] Forbidden query blocked: '{q[:40]}...' (Reason: {err})")

    # Test Role-Based Access Control (RBAC) programmatic limits
    print("\nRunning Programmatic RBAC Verification Tests...")
    
    # Faculty querying fees (should block)
    faculty_fee_query = "SELECT * FROM fee_payments"
    ok, err = validate_sql(faculty_fee_query, role="Faculty", domain="fees")
    assert not ok, "Faculty should be blocked from querying fees!"
    print(f"  [PASS] Faculty blocked from fees: '{faculty_fee_query}' (Reason: {err})")

    # Student querying general students table without filter (should block)
    student_unfiltered = "SELECT * FROM students"
    ok, err = validate_sql(student_unfiltered, role="Student", domain="academics", student_id=1)
    assert not ok, "Student should be blocked from unfiltered student table queries!"
    print(f"  [PASS] Student blocked from unfiltered queries: '{student_unfiltered}' (Reason: {err})")

    # Student querying own student_id (should allow)
    student_own = "SELECT cgpa FROM students WHERE student_id = 1"
    ok, err = validate_sql(student_own, role="Student", domain="academics", student_id=1)
    assert ok, f"Student should be allowed to query own records: '{student_own}'. Error: {err}"
    print(f"  [PASS] Student allowed to query own record: '{student_own}'")

    # Student querying another student's id (should block)
    student_other = "SELECT cgpa FROM students WHERE student_id = 2"
    ok, err = validate_sql(student_other, role="Student", domain="academics", student_id=1)
    assert not ok, "Student should be blocked from querying other student IDs!"
    print(f"  [PASS] Student blocked from other student ID: '{student_other}' (Reason: {err})")

    # Student querying audit logs (should block)
    student_logs = "SELECT * FROM audit_logs"
    ok, err = validate_sql(student_logs, role="Student", domain="administration")
    assert not ok, "Student should be blocked from audit logs!"
    print(f"  [PASS] Student blocked from audit logs: '{student_logs}' (Reason: {err})")

    # Admin querying audit logs (should block)
    admin_logs = "SELECT * FROM audit_logs"
    ok, err = validate_sql(admin_logs, role="Department Admin", domain="administration")
    assert not ok, "Department Admin should be blocked from audit logs!"
    print(f"  [PASS] Department Admin blocked from audit logs: '{admin_logs}' (Reason: {err})")


def test_cache():
    print("\nRunning Caching Tests...")
    cache = InMemoryCache()
    
    # Test set & get
    cache.set("test_key", "cached_value", ttl=10)
    val = cache.get("test_key")
    assert val == "cached_value", f"Cache get failed. Expected 'cached_value', got '{val}'"
    print("  [PASS] Cache write & read successful.")

    # Test TTL expiration
    cache.set("expired_key", "expired_value", ttl=-1) # expire instantly
    val_expired = cache.get("expired_key")
    assert val_expired is None, "Cache should have expired!"
    print("  [PASS] Cache TTL expiration working.")

    # Test query hashing
    hash1 = get_query_hash("Student", "What is my CGPA?")
    hash2 = get_query_hash("Student", "What is my CGPA?")
    hash3 = get_query_hash("Admin", "What is my CGPA?")
    assert hash1 == hash2, "Identical queries must produce matching hashes."
    assert hash1 != hash3, "Different roles must produce different hashes."
    print("  [PASS] Query hashing logic correct.")

def test_domain_heuristics():
    print("\nRunning Domain Classification Heuristics Tests...")
    
    # Test heuristics fallback when API key is unconfigured
    queries = {
        "What is my attendance in python?": "attendance",
        "List all fee defaulters": "fees",
        "Who is the teacher for operating systems?": "faculty",
        "Show latest university announcements": "administration",
        "Who are the toppers in MCA?": "academics"
    }

    for q, expected in queries.items():
        domain = classify_domain(q)
        assert domain == expected, f"Expected domain '{expected}' for '{q}', got '{domain}'"
        print(f"  [PASS] Classified '{q}' -> '{domain}'")

if __name__ == "__main__":
    print("=========================================")
    print("        STARTING BACKEND TESTS           ")
    print("=========================================")
    
    test_sql_validation()
    test_cache()
    test_domain_heuristics()
    
    print("=========================================")
    print("        ALL TESTS PASSED SUCCESSFULLY!    ")
    print("=========================================")
