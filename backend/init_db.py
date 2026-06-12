import mysql.connector
from mysql.connector import errorcode
import datetime

# Database config
DB_NAME = "university_erp"
config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'raise_on_warnings': False
}

def create_database(cursor):
    try:
        cursor.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
        print(f"Database {DB_NAME} created successfully.")
    except mysql.connector.Error as err:
        print(f"Failed creating database: {err}")
        exit(1)

def run_init():
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
    except mysql.connector.Error as err:
        if err.errno == errorcode.CR_CONN_HOST_ERROR or err.errno == 2003:
            print("Error: Could not connect to MySQL server. Please ensure XAMPP MySQL is running.")
            return False
        else:
            print(f"Error connecting to MySQL: {err}")
            return False

    try:
        cursor.execute(f"USE {DB_NAME}")
        print(f"Database {DB_NAME} already exists. Re-creating tables...")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            conn.database = DB_NAME
        else:
            print(err)
            return False

    # Define tables
    TABLES = {}

    TABLES['departments'] = (
        "CREATE TABLE `departments` ("
        "  `department_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `department_name` varchar(100) NOT NULL,"
        "  PRIMARY KEY (`department_id`)"
        ") ENGINE=InnoDB"
    )

    TABLES['faculty'] = (
        "CREATE TABLE `faculty` ("
        "  `faculty_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `first_name` varchar(50) NOT NULL,"
        "  `last_name` varchar(50) NOT NULL,"
        "  `email` varchar(100) NOT NULL UNIQUE,"
        "  `department_id` int(11),"
        "  PRIMARY KEY (`faculty_id`),"
        "  FOREIGN KEY (`department_id`) REFERENCES `departments` (`department_id`) ON DELETE SET NULL"
        ") ENGINE=InnoDB"
    )

    TABLES['courses'] = (
        "CREATE TABLE `courses` ("
        "  `course_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `course_name` varchar(100) NOT NULL,"
        "  `course_code` varchar(20) NOT NULL UNIQUE,"
        "  `department_id` int(11),"
        "  PRIMARY KEY (`course_id`),"
        "  FOREIGN KEY (`department_id`) REFERENCES `departments` (`department_id`) ON DELETE SET NULL"
        ") ENGINE=InnoDB"
    )

    TABLES['semesters'] = (
        "CREATE TABLE `semesters` ("
        "  `semester_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `semester_name` varchar(50) NOT NULL,"
        "  `is_active` boolean DEFAULT FALSE,"
        "  PRIMARY KEY (`semester_id`)"
        ") ENGINE=InnoDB"
    )

    TABLES['subjects'] = (
        "CREATE TABLE `subjects` ("
        "  `subject_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `subject_name` varchar(100) NOT NULL,"
        "  `subject_code` varchar(20) NOT NULL UNIQUE,"
        "  `course_id` int(11),"
        "  PRIMARY KEY (`subject_id`),"
        "  FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['students'] = (
        "CREATE TABLE `students` ("
        "  `student_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `first_name` varchar(50) NOT NULL,"
        "  `last_name` varchar(50) NOT NULL,"
        "  `email` varchar(100) NOT NULL UNIQUE,"
        "  `enrollment_no` varchar(50) NOT NULL UNIQUE,"
        "  `status` varchar(20) DEFAULT 'Active',"
        "  `cgpa` decimal(3,2) DEFAULT 0.00,"
        "  `course_id` int(11),"
        "  PRIMARY KEY (`student_id`),"
        "  FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE SET NULL"
        ") ENGINE=InnoDB"
    )

    TABLES['results'] = (
        "CREATE TABLE `results` ("
        "  `result_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `student_id` int(11) NOT NULL,"
        "  `subject_id` int(11) NOT NULL,"
        "  `marks_obtained` int(11) NOT NULL,"
        "  `max_marks` int(11) DEFAULT 100,"
        "  `grade` varchar(5) NOT NULL,"
        "  `semester_id` int(11) NOT NULL,"
        "  PRIMARY KEY (`result_id`),"
        "  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`semester_id`) REFERENCES `semesters` (`semester_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['attendance'] = (
        "CREATE TABLE `attendance` ("
        "  `attendance_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `student_id` int(11) NOT NULL,"
        "  `subject_id` int(11) NOT NULL,"
        "  `classes_attended` int(11) NOT NULL,"
        "  `total_classes` int(11) NOT NULL,"
        "  `percentage` decimal(5,2) NOT NULL,"
        "  PRIMARY KEY (`attendance_id`),"
        "  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['attendance_logs'] = (
        "CREATE TABLE `attendance_logs` ("
        "  `log_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `student_id` int(11) NOT NULL,"
        "  `subject_id` int(11) NOT NULL,"
        "  `date` date NOT NULL,"
        "  `status` varchar(10) NOT NULL,"
        "  PRIMARY KEY (`log_id`),"
        "  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['fee_structure'] = (
        "CREATE TABLE `fee_structure` ("
        "  `fee_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `course_id` int(11) NOT NULL,"
        "  `academic_year` varchar(20) NOT NULL,"
        "  `total_amount` decimal(10,2) NOT NULL,"
        "  PRIMARY KEY (`fee_id`),"
        "  FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['fee_payments'] = (
        "CREATE TABLE `fee_payments` ("
        "  `payment_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `student_id` int(11) NOT NULL,"
        "  `amount_paid` decimal(10,2) NOT NULL,"
        "  `payment_date` date NOT NULL,"
        "  `pending_amount` decimal(10,2) NOT NULL,"
        "  PRIMARY KEY (`payment_id`),"
        "  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['scholarships'] = (
        "CREATE TABLE `scholarships` ("
        "  `scholarship_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `student_id` int(11) NOT NULL,"
        "  `amount` decimal(10,2) NOT NULL,"
        "  `type` varchar(50) NOT NULL,"
        "  PRIMARY KEY (`scholarship_id`),"
        "  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['faculty_workload'] = (
        "CREATE TABLE `faculty_workload` ("
        "  `workload_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `faculty_id` int(11) NOT NULL,"
        "  `subject_id` int(11) NOT NULL,"
        "  `hours_per_week` int(11) NOT NULL,"
        "  PRIMARY KEY (`workload_id`),"
        "  FOREIGN KEY (`faculty_id`) REFERENCES `faculty` (`faculty_id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`subject_id`) REFERENCES `subjects` (`subject_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['admissions'] = (
        "CREATE TABLE `admissions` ("
        "  `admission_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `student_id` int(11) NOT NULL,"
        "  `admission_date` date NOT NULL,"
        "  `batch` varchar(20) NOT NULL,"
        "  PRIMARY KEY (`admission_id`),"
        "  FOREIGN KEY (`student_id`) REFERENCES `students` (`student_id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    )

    TABLES['notifications'] = (
        "CREATE TABLE `notifications` ("
        "  `notification_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `title` varchar(200) NOT NULL,"
        "  `message` text NOT NULL,"
        "  `target_role` varchar(50) NOT NULL,"
        "  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,"
        "  PRIMARY KEY (`notification_id`)"
        ") ENGINE=InnoDB"
    )

    TABLES['audit_logs'] = (
        "CREATE TABLE `audit_logs` ("
        "  `log_id` int(11) NOT NULL AUTO_INCREMENT,"
        "  `user_role` varchar(50) NOT NULL,"
        "  `question` text NOT NULL,"
        "  `generated_sql` text,"
        "  `response` text,"
        "  `execution_time_ms` int(11),"
        "  `rows_returned` int(11),"
        "  `cache_hit` boolean,"
        "  `timestamp` timestamp DEFAULT CURRENT_TIMESTAMP,"
        "  PRIMARY KEY (`log_id`)"
        ") ENGINE=InnoDB"
    )

    # Drop tables in reverse order to respect foreign key constraints
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for name in list(TABLES.keys()):
        cursor.execute(f"DROP TABLE IF EXISTS `{name}`")
        print(f"Dropped table `{name}` if existed.")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # Create tables
    for name, sql in TABLES.items():
        try:
            print(f"Creating table `{name}`: ", end="")
            cursor.execute(sql)
            print("OK")
        except mysql.connector.Error as err:
            print(err.msg)
            return False

    # Insert Dummy Data
    print("Seeding database...")

    # Departments
    departments = [
        ("Computer Applications",),
        ("Computer Science & Engineering",),
        ("Business Administration",)
    ]
    cursor.executemany("INSERT INTO departments (department_name) VALUES (%s)", departments)
    
    # Faculty
    faculty = [
        ("Rajesh", "Kumar", "rajesh.kumar@university.edu", 1),
        ("Sunita", "Sharma", "sunita.sharma@university.edu", 1),
        ("Amit", "Verma", "amit.verma@university.edu", 2),
        ("Pooja", "Rao", "pooja.rao@university.edu", 2),
        ("Sanjay", "Gupta", "sanjay.gupta@university.edu", 3)
    ]
    cursor.executemany("INSERT INTO faculty (first_name, last_name, email, department_id) VALUES (%s, %s, %s, %s)", faculty)

    # Courses
    courses = [
        ("Master of Computer Applications", "MCA", 1),
        ("Bachelor of Technology in CSE", "BTECH-CSE", 2),
        ("Master of Business Administration", "MBA", 3)
    ]
    cursor.executemany("INSERT INTO courses (course_name, course_code, department_id) VALUES (%s, %s, %s)", courses)

    # Semesters
    semesters = [
        ("MCA 1st Trimester", False),
        ("MCA 4th Trimester", True),
        ("B.Tech 4th Semester", True),
        ("MBA 2nd Semester", True)
    ]
    cursor.executemany("INSERT INTO semesters (semester_name, is_active) VALUES (%s, %s)", semesters)

    # Subjects
    subjects = [
        ("Data Structures", "MCA-101", 1),
        ("Database Management Systems", "MCA-102", 1),
        ("Python Programming", "MCA-401", 1),
        ("Advanced Software Engineering", "MCA-402", 1),
        ("Design and Analysis of Algorithms", "CS-201", 2),
        ("Operating Systems", "CS-202", 2),
        ("Financial Management", "MBA-201", 3),
        ("Marketing Analytics", "MBA-202", 3)
    ]
    cursor.executemany("INSERT INTO subjects (subject_name, subject_code, course_id) VALUES (%s, %s, %s)", subjects)

    # Students
    # Dynamic generation of 40 students with realistic emails, enrollment numbers, status, and course mappings
    first_names = ["Rahul", "Priya", "Amit", "Sneha", "Rohan", "Vikram", "Divya", "Manish", "Arjun", "Neha", 
                   "Aarav", "Ananya", "Kabir", "Diya", "Vivaan", "Ishaan", "Aanya", "Sai", "Aadhya", "Krishna", 
                   "Aditya", "Meera", "Ishita", "Aryan", "Pranav", "Siddharth", "Kiara", "Rhea", "Avani", "Rudra", 
                   "Reyansh", "Anika", "Vihaan", "Dhruv", "Zara", "Amina", "Saisha", "Yash", "Karan", "Simran"]
    
    last_names = ["Sharma", "Patel", "Sen", "Reddy", "Malhotra", "Singh", "Nair", "Gupta", "Das", "Kapoor", 
                  "Kumar", "Joshi", "Mehta", "Iyer", "Rao", "Pillai", "Choudhury", "Bose", "Chatterjee", "Mukherjee", 
                  "Verma", "Prasad", "Mishra", "Pandey", "Trivedi", "Desai", "Kulkarni", "Patil", "Bhat", "Shenoy"]

    students = []
    # Build list of 40 students
    for i in range(1, 41):
        fn = first_names[(i - 1) % len(first_names)]
        ln = last_names[(i - 1) % len(last_names)]
        email = f"{fn.lower()}.{ln.lower()}{i}@student.edu"
        
        course_id = ((i - 1) % 3) + 1  # 1: MCA, 2: BTECH-CSE, 3: MBA
        prefix = "MCA" if course_id == 1 else ("CS" if course_id == 2 else "MBA")
        year = 2024 if course_id == 1 else (2022 if course_id == 2 else 2025)
        enrollment_no = f"{prefix}{year}{i:02d}"
        
        # Student 6 is Graduated, others Active
        status = "Graduated" if i == 6 else "Active"
        cgpa = round(5.5 + (i * 0.13) % 4.3, 2)
        if cgpa > 10.0:
            cgpa = 10.00
            
        students.append((fn, ln, email, enrollment_no, status, cgpa, course_id))

    cursor.executemany("INSERT INTO students (first_name, last_name, email, enrollment_no, status, cgpa, course_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", students)

    # Fetch inserted student IDs to keep relations consistent
    cursor.execute("SELECT student_id, course_id FROM students")
    db_students = cursor.fetchall()  # list of (student_id, course_id)

    # Dynamic Results Generation
    # Loop through all students and insert results for active semesters
    # MCA (course 1): semesters 1 and 2 (subjects 1, 2, 3, 4)
    # BTech (course 2): semester 3 (subjects 5, 6)
    # MBA (course 3): semester 4 (subjects 7, 8)
    results = []
    grades = [
        (90, "O"), (80, "A+"), (70, "A"), (60, "B+"), (50, "B"), (40, "C"), (0, "F")
    ]
    for student_id, course_id in db_students:
        if course_id == 1:
            subject_ids = [1, 2] # Data Structures, DBMS (Trimester 1)
            semester_id = 1
        elif course_id == 2:
            subject_ids = [5, 6] # DAA, OS (Semester 3)
            semester_id = 3
        else:
            subject_ids = [7, 8] # FM, MA (Semester 4)
            semester_id = 4
            
        for sub_id in subject_ids:
            # Deterministic marks based on student_id
            marks = int(50 + (student_id * 7 + sub_id * 13) % 49)
            grade = "F"
            for threshold, g in grades:
                if marks >= threshold:
                    grade = g
                    break
            results.append((student_id, sub_id, marks, 100, grade, semester_id))
            
    cursor.executemany("INSERT INTO results (student_id, subject_id, marks_obtained, max_marks, grade, semester_id) VALUES (%s, %s, %s, %s, %s, %s)", results)

    # Dynamic Attendance Generation
    # Loop through students and create attendance records for their registered subjects
    attendance = []
    for student_id, course_id in db_students:
        if course_id == 1:
            subject_ids = [1, 2, 3] # DS, DBMS, Python (MCA)
        elif course_id == 2:
            subject_ids = [5, 6] # DAA, OS (BTech)
        else:
            subject_ids = [7, 8] # FM, MA (MBA)
            
        for sub_id in subject_ids:
            total_classes = 40 if sub_id in [1, 2, 7, 8] else 50
            # Some students have low attendance (Amit = id 3, Manish = id 8, etc.)
            # Deterministic formula to distribute attendance percentages
            factor = 0.55 if student_id in [3, 8, 15, 23, 31] else 0.78
            classes_attended = int(total_classes * (factor + (student_id * 3 + sub_id * 7) % 20 / 100))
            if classes_attended > total_classes:
                classes_attended = total_classes
            percentage = round((classes_attended / total_classes) * 100, 2)
            attendance.append((student_id, sub_id, classes_attended, total_classes, percentage))
            
    cursor.executemany("INSERT INTO attendance (student_id, subject_id, classes_attended, total_classes, percentage) VALUES (%s, %s, %s, %s, %s)", attendance)

    # Dynamic Attendance Logs (daily logs for the first 15 students over 10 days)
    log_date_base = datetime.date(2026, 6, 1)
    attendance_logs = []
    for student_id, course_id in db_students[:15]: # log for first 15 students
        sub_id = 1 if course_id == 1 else (5 if course_id == 2 else 7)
        for day in range(10):
            current_date = log_date_base + datetime.timedelta(days=day)
            if current_date.weekday() >= 5:
                continue
            # Some absents
            status = "Absent" if (student_id + day) % 7 == 0 else "Present"
            attendance_logs.append((student_id, sub_id, current_date, status))
            
    cursor.executemany("INSERT INTO attendance_logs (student_id, subject_id, date, status) VALUES (%s, %s, %s, %s)", attendance_logs)

    # Fee Structure
    fee_structures = [
        (1, "2024-2026", 120000.00), # MCA
        (2, "2022-2026", 180000.00), # BTech CSE
        (3, "2025-2027", 250000.00)  # MBA
    ]
    cursor.executemany("INSERT INTO fee_structure (course_id, academic_year, total_amount) VALUES (%s, %s, %s)", fee_structures)

    # Dynamic Fee Payments & Scholarships
    fee_payments = []
    scholarships = []
    for student_id, course_id in db_students:
        expected = 120000.00 if course_id == 1 else (180000.00 if course_id == 2 else 250000.00)
        
        # Payment category
        # Full payment: 70% of students
        # Partial payment: 20% of students
        # Unpaid/Defaulter: 10% of students
        category = student_id % 10
        if category in [0, 1, 2, 3, 4, 5, 6]:
            paid = expected
            pending = 0.00
        elif category in [7, 8]:
            paid = expected - 40000.00
            pending = 40000.00
        else:
            paid = 0.00
            pending = expected
            
        if paid > 0:
            fee_payments.append((student_id, paid, datetime.date(2025, 8, 10 + (student_id % 15)), pending))
            
        # Scholarships for high CGPA students (top 15% of CGPAs)
        # We can dynamically give scholarships
        if student_id % 7 == 0:
            amt = 30000.00 if student_id % 2 == 0 else 50000.00
            type_str = "Merit-based Academic Scholarship" if student_id % 2 == 0 else "Dean's List Scholarship"
            scholarships.append((student_id, amt, type_str))
            
    cursor.executemany("INSERT INTO fee_payments (student_id, amount_paid, payment_date, pending_amount) VALUES (%s, %s, %s, %s)", fee_payments)
    cursor.executemany("INSERT INTO scholarships (student_id, amount, type) VALUES (%s, %s, %s)", scholarships)

    # Faculty Workload
    faculty_workloads = [
        (1, 1, 12), # Rajesh Kumar teaches DS (12 hrs/wk)
        (1, 2, 8),  # Rajesh Kumar teaches DBMS (8 hrs/wk)
        (2, 3, 16), # Sunita Sharma teaches Python (16 hrs/wk)
        (3, 5, 14), # Amit Verma teaches DAA (14 hrs/wk)
        (4, 6, 12), # Pooja Rao teaches OS (12 hrs/wk)
        (5, 7, 10), # Sanjay Gupta teaches FM (10 hrs/wk)
        (5, 8, 10)  # Sanjay Gupta teaches MA (10 hrs/wk)
    ]
    cursor.executemany("INSERT INTO faculty_workload (faculty_id, subject_id, hours_per_week) VALUES (%s, %s, %s)", faculty_workloads)

    # Admissions
    admissions = []
    for student_id, course_id in db_students:
        prefix = "MCA Batch 2024" if course_id == 1 else ("BTech CSE Batch 2022" if course_id == 2 else "MBA Batch 2025")
        year = 2024 if course_id == 1 else (2022 if course_id == 2 else 2025)
        admission_date = datetime.date(year, 7, 10 + (student_id % 15))
        admissions.append((student_id, admission_date, prefix))
        
    cursor.executemany("INSERT INTO admissions (student_id, admission_date, batch) VALUES (%s, %s, %s)", admissions)

    # Notifications
    notifications = [
        ("Trimester End Examinations", "Trimester end exams for MCA 4th Trimester will commence from July 5, 2026. Make sure your dues are cleared.", "Student"),
        ("Faculty Meeting", "All Department Faculty meeting with the Dean on June 25, 2026, in the main seminar hall.", "Faculty"),
        ("Fee Dues Alert", "Students with pending fees are requested to clear their dues before June 30, 2026, to avoid penalty.", "Student"),
        ("New Course Syllabus approved", "The syllabus for Marketing Analytics MBA-202 has been updated.", "Faculty")
    ]
    cursor.executemany("INSERT INTO notifications (title, message, target_role) VALUES (%s, %s, %s)", notifications)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database seeding completed successfully.")
    return True

if __name__ == "__main__":
    run_init()
