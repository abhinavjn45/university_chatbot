import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agent import validate_sql

def run_tests():
    print("==================================================")
    print("  RUNNING SECURITY & ROBUSTNESS HARDENING TESTS   ")
    print("==================================================")
    
    # 1. Test False Positive SQL Validation Bypasses (Keywords in string literals)
    print("Testing legitimate queries containing forbidden keywords in string values:")
    
    query1 = "SELECT * FROM students WHERE email = 'drop@example.com'"
    ok, err = validate_sql(query1, role="Super Admin", domain="academics")
    assert ok, f"Query with email 'drop@example.com' was false-positively blocked: {err}"
    print(f"  [PASS] Allowed keyword in literal: '{query1}'")

    query2 = "SELECT * FROM notifications WHERE title = 'Notice: System update today'"
    ok, err = validate_sql(query2, role="Super Admin", domain="administration")
    assert ok, f"Query with keyword 'update' in literal was false-positively blocked: {err}"
    print(f"  [PASS] Allowed keyword in literal: '{query2}'")

    # 2. Test Semicolons in String Literals
    query3 = "SELECT * FROM notifications WHERE message LIKE '%;%'"
    ok, err = validate_sql(query3, role="Super Admin", domain="administration")
    assert ok, f"Query with semicolon in literal was false-positively blocked: {err}"
    print(f"  [PASS] Allowed semicolon in literal: '{query3}'")

    # 3. Test Actual Stacked SQL Injection (Should still block)
    query4 = "SELECT * FROM students; DROP TABLE results"
    ok, err = validate_sql(query4, role="Super Admin", domain="academics")
    assert not ok, "Failed to block actual stacked SQL injection!"
    print(f"  [PASS] Blocked actual injection: '{query4}' (Reason: {err})")

    # 4. Test Actual Forbidden Keyword (Should still block)
    query5 = "DROP TABLE students"
    ok, err = validate_sql(query5, role="Super Admin", domain="academics")
    assert not ok, "Failed to block forbidden command DROP!"
    print(f"  [PASS] Blocked actual forbidden keyword: '{query5}' (Reason: {err})")

    # 5. Test Watertight Student RBAC
    print("\nTesting Watertight Student RBAC filters:")

    # Student 1 query own grades (valid alias and spacing)
    query6 = "SELECT grade FROM results s WHERE s.student_id = 1"
    ok, err = validate_sql(query6, role="Student", domain="academics", student_id=1)
    assert ok, f"Query with student alias should be allowed: {err}"
    print(f"  [PASS] Allowed student own data query: '{query6}'")

    # Student 1 query own grades (valid reverse order check)
    query7 = "SELECT grade FROM results WHERE 1 = student_id"
    ok, err = validate_sql(query7, role="Student", domain="academics", student_id=1)
    assert ok, f"Query with reverse student ID comparison should be allowed: {err}"
    print(f"  [PASS] Allowed student own data query (reverse order): '{query7}'")

    # Student 1 attempting to query Student 2 grades (Should Block)
    query8 = "SELECT grade FROM results WHERE student_id = 2"
    ok, err = validate_sql(query8, role="Student", domain="academics", student_id=1)
    assert not ok, "Failed to block student querying another student's ID!"
    print(f"  [PASS] Blocked student querying different student ID: '{query8}' (Reason: {err})")

    # Student attempting to query forbidden faculty table (Should Block)
    query_stud_fac = "SELECT * FROM faculty"
    ok, err = validate_sql(query_stud_fac, role="Student", domain="academics", student_id=1)
    assert not ok, "Failed to block student querying faculty table!"
    print(f"  [PASS] Blocked student querying faculty table: '{query_stud_fac}' (Reason: {err})")

    # 6. Test Watertight Faculty Workload & Subject Filter RBAC
    print("\nTesting Watertight Faculty RBAC filters:")

    # Faculty 2 querying workloads associated with their own ID (Should Allow)
    query_fac_ok = "SELECT * FROM faculty_workload WHERE faculty_id = 2"
    ok, err = validate_sql(query_fac_ok, role="Faculty", domain="faculty", faculty_id=2)
    assert ok, f"Query with faculty workload filter should be allowed: {err}"
    print(f"  [PASS] Allowed faculty querying own workload: '{query_fac_ok}'")

    # Faculty 2 querying attendance of a subject they teach (Should Allow)
    query_fac_att_ok = "SELECT a.* FROM attendance a JOIN faculty_workload fw ON a.subject_id = fw.subject_id WHERE fw.faculty_id = 2"
    ok, err = validate_sql(query_fac_att_ok, role="Faculty", domain="attendance", faculty_id=2)
    assert ok, f"Query joining workloads and filtering by faculty_id should be allowed: {err}"
    print(f"  [PASS] Allowed faculty querying own subjects attendance: '{query_fac_att_ok}'")

    # Faculty 2 attempting to query workloads of another faculty member (Should Block)
    query_fac_other = "SELECT * FROM faculty_workload WHERE faculty_id = 3"
    ok, err = validate_sql(query_fac_other, role="Faculty", domain="faculty", faculty_id=2)
    assert not ok, "Failed to block faculty querying another faculty's workload!"
    print(f"  [PASS] Blocked faculty querying other faculty ID: '{query_fac_other}' (Reason: {err})")

    # Faculty 2 attempting to query attendance without any workload filter (Should Block)
    query_fac_no_filter = "SELECT * FROM attendance"
    ok, err = validate_sql(query_fac_no_filter, role="Faculty", domain="attendance", faculty_id=2)
    assert not ok, "Failed to block faculty query with missing workload filter!"
    print(f"  [PASS] Blocked faculty query missing workload filter: '{query_fac_no_filter}' (Reason: {err})")

    print("==================================================")
    print("       ALL HARDENING TESTS PASSED SUCCESSFULLY!   ")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
