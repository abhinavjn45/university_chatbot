BUSINESS_RULES = """
- Detained: attendance.percentage < 75.00
- Topper: Highest students.cgpa in course, or highest results.marks_obtained in subject
- Defaulter: fee_payments.pending_amount > 0
- Active/Graduated Student: students.status = 'Active' / 'Graduated'
- Current Semester: semesters.is_active = 1
- Expected Course Fee: fee_structure.total_amount for that course (join fee_structure to courses via course_id, and students to courses via course_id).
- Fee Payments: belongs to Student (fee_payments.student_id = students.student_id). There is NO fee_id in fee_payments.
"""

# Compact representation of DDL schemas to minimize prompt tokens
DOMAIN_SCHEMAS = {
    "academics": """
students(student_id PK, first_name, last_name, email UNIQUE, enrollment_no UNIQUE, status, cgpa, course_id FK)
courses(course_id PK, course_name, course_code UNIQUE, department_id FK)
semesters(semester_id PK, semester_name, is_active)
subjects(subject_id PK, subject_name, subject_code UNIQUE, course_id FK)
results(result_id PK, student_id FK, subject_id FK, marks_obtained, max_marks, grade, semester_id FK)
""",

    "attendance": """
attendance(attendance_id PK, student_id FK references students(student_id), subject_id FK, classes_attended, total_classes, percentage)
attendance_logs(log_id PK, student_id FK references students(student_id), subject_id FK, date, status)
students(student_id PK, first_name, last_name, enrollment_no, status, cgpa, course_id FK)
subjects(subject_id PK, subject_name, subject_code)
""",

    "fees": """
fee_structure(fee_id PK, course_id FK references courses(course_id), academic_year, total_amount)
fee_payments(payment_id PK, student_id FK references students(student_id), amount_paid, payment_date, pending_amount)
scholarships(scholarship_id PK, student_id FK references students(student_id), amount, type)
students(student_id PK, first_name, last_name, enrollment_no, status, cgpa, course_id FK references courses(course_id))
courses(course_id PK, course_name, course_code)
""",

    "faculty": """
faculty(faculty_id PK, first_name, last_name, email UNIQUE, department_id FK)
departments(department_id PK, department_name)
faculty_workload(workload_id PK, faculty_id FK references faculty(faculty_id), subject_id FK, hours_per_week)
subjects(subject_id PK, subject_name, subject_code)
""",

    "administration": """
admissions(admission_id PK, student_id FK references students(student_id), admission_date, batch)
departments(department_id PK, department_name)
notifications(notification_id PK, title, message, target_role, created_at)
students(student_id PK, first_name, last_name, enrollment_no, status, cgpa)
"""
}

# Ultra-short role constraints
ROLE_RESTRICTIONS = {
    "Student": "Only read own data. Filter by student_id={student_id}.",
    "Faculty": "Read class grades, attendance, workloads. No student fees or HR salaries.",
    "Department Admin": "Read student records, academic/attendance/fees. No super admin settings.",
    "Super Admin": "No restrictions."
}
