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
    # Rahul Sharma (MCA, cgpa 9.2)
    # Priya Patel (MCA, cgpa 8.7)
    # Amit Sen (MCA, cgpa 6.8, attendance below 75% - detained)
    # Sneha Reddy (B.Tech, cgpa 9.5)
    # Rohan Malhotra (B.Tech, cgpa 7.1, fee defaulter)
    # Vikram Singh (B.Tech, graduated, cgpa 8.1)
    # Divya Nair (MBA, cgpa 8.9)
    # Manish Gupta (MBA, cgpa 5.4, fee defaulter and detained)
    students = [
        ("Rahul", "Sharma", "rahul.sharma@student.edu", "MCA202401", "Active", 9.20, 1),
        ("Priya", "Patel", "priya.patel@student.edu", "MCA202402", "Active", 8.70, 1),
        ("Amit", "Sen", "amit.sen@student.edu", "MCA202403", "Active", 6.80, 1),
        ("Sneha", "Reddy", "sneha.reddy@student.edu", "CS202201", "Active", 9.50, 2),
        ("Rohan", "Malhotra", "rohan.malhotra@student.edu", "CS202202", "Active", 7.10, 2),
        ("Vikram", "Singh", "vikram.singh@student.edu", "CS202203", "Graduated", 8.10, 2),
        ("Divya", "Nair", "divya.nair@student.edu", "MBA202501", "Active", 8.90, 3),
        ("Manish", "Gupta", "manish.gupta@student.edu", "MBA202502", "Active", 5.40, 3),
        ("Arjun", "Das", "arjun.das@student.edu", "MCA202404", "Active", 7.80, 1),
        ("Neha", "Kapoor", "neha.kapoor@student.edu", "CS202204", "Active", 8.45, 2)
    ]
    cursor.executemany("INSERT INTO students (first_name, last_name, email, enrollment_no, status, cgpa, course_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", students)

    # Results (For MCA 1st Trimester subjects and other sem results)
    results = [
        # Student 1: Rahul Sharma
        (1, 1, 95, 100, "O", 1), # DS
        (1, 2, 90, 100, "A+", 1), # DBMS
        # Student 2: Priya Patel
        (2, 1, 88, 100, "A", 1),
        (2, 2, 85, 100, "A", 1),
        # Student 3: Amit Sen
        (3, 1, 65, 100, "B", 1),
        (3, 2, 70, 100, "B+", 1),
        # Student 4: Sneha Reddy
        (4, 5, 98, 100, "O", 3), # DAA
        (4, 6, 94, 100, "O", 3), # OS
        # Student 5: Rohan Malhotra
        (5, 5, 72, 100, "B+", 3),
        (5, 6, 70, 100, "B+", 3),
        # Student 7: Divya Nair
        (7, 7, 91, 100, "A+", 4), # FM
        (7, 8, 87, 100, "A", 4), # MA
        # Student 8: Manish Gupta
        (8, 7, 52, 100, "C", 4),
        (8, 8, 56, 100, "C", 4)
    ]
    cursor.executemany("INSERT INTO results (student_id, subject_id, marks_obtained, max_marks, grade, semester_id) VALUES (%s, %s, %s, %s, %s, %s)", results)

    # Attendance (Calculated percentages: attended, total, percent)
    # Rahul Sharma
    # Priya Patel
    # Amit Sen (detained, attendance < 75%)
    # Sneha Reddy
    # Rohan Malhotra
    # Divya Nair
    # Manish Gupta (detained, attendance < 75%)
    attendance = [
        (1, 1, 38, 40, 95.00), # Rahul Sharma, DS
        (1, 2, 36, 40, 90.00), # Rahul Sharma, DBMS
        (1, 3, 29, 30, 96.67), # Rahul Sharma, Python
        (2, 1, 34, 40, 85.00), # Priya, DS
        (2, 2, 35, 40, 87.50), # Priya, DBMS
        (2, 3, 27, 30, 90.00), # Priya, Python
        (3, 1, 24, 40, 60.00), # Amit Sen, DS (Detained in DS)
        (3, 2, 32, 40, 80.00), # Amit Sen, DBMS
        (3, 3, 18, 30, 60.00), # Amit Sen, Python (Detained in Python)
        (4, 5, 48, 50, 96.00), # Sneha, DAA
        (4, 6, 47, 50, 94.00), # Sneha, OS
        (5, 5, 39, 50, 78.00), # Rohan, DAA
        (5, 6, 40, 50, 80.00), # Rohan, OS
        (7, 7, 32, 35, 91.43), # Divya, FM
        (7, 8, 31, 35, 88.57), # Divya, MA
        (8, 7, 20, 35, 57.14), # Manish, FM (Detained in FM)
        (8, 8, 22, 35, 62.86)  # Manish, MA (Detained in MA)
    ]
    cursor.executemany("INSERT INTO attendance (student_id, subject_id, classes_attended, total_classes, percentage) VALUES (%s, %s, %s, %s, %s)", attendance)

    # Attendance Logs (for recent dates to show records)
    log_date_base = datetime.date(2026, 6, 1)
    attendance_logs = []
    for day in range(10):
        current_date = log_date_base + datetime.timedelta(days=day)
        # Weekends off
        if current_date.weekday() >= 5:
            continue
        
        # Student 1 present mostly
        attendance_logs.append((1, 1, current_date, "Present"))
        attendance_logs.append((1, 2, current_date, "Present"))
        
        # Student 3 absent mostly
        status_s3 = "Present" if day % 3 == 0 else "Absent"
        attendance_logs.append((3, 1, current_date, status_s3))
        attendance_logs.append((3, 3, current_date, status_s3))

        # Student 8 absent mostly
        status_s8 = "Present" if day % 4 == 0 else "Absent"
        attendance_logs.append((8, 7, current_date, status_s8))
        attendance_logs.append((8, 8, current_date, status_s8))

    cursor.executemany("INSERT INTO attendance_logs (student_id, subject_id, date, status) VALUES (%s, %s, %s, %s)", attendance_logs)

    # Fee Structure
    fee_structures = [
        (1, "2024-2026", 120000.00), # MCA
        (2, "2022-2026", 180000.00), # BTech CSE
        (3, "2025-2027", 250000.00)  # MBA
    ]
    cursor.executemany("INSERT INTO fee_structure (course_id, academic_year, total_amount) VALUES (%s, %s, %s)", fee_structures)

    # Fee Payments
    # Student 1: Rahul (Paid full)
    # Student 2: Priya (Paid full)
    # Student 3: Amit (Paid 100k, 20k pending)
    # Student 4: Sneha (Paid full)
    # Student 5: Rohan (Paid 100k, 80k pending - defaulter)
    # Student 7: Divya (Paid full)
    # Student 8: Manish (Paid 120k, 130k pending - defaulter)
    fee_payments = [
        (1, 120000.00, datetime.date(2025, 8, 10), 0.00),
        (2, 120000.00, datetime.date(2025, 8, 12), 0.00),
        (3, 100000.00, datetime.date(2025, 9, 1), 20000.00),
        (4, 180000.00, datetime.date(2025, 7, 20), 0.00),
        (5, 100000.00, datetime.date(2025, 8, 5), 80000.00),
        (7, 250000.00, datetime.date(2025, 7, 15), 0.00),
        (8, 120000.00, datetime.date(2025, 8, 25), 130000.00)
    ]
    cursor.executemany("INSERT INTO fee_payments (student_id, amount_paid, payment_date, pending_amount) VALUES (%s, %s, %s, %s)", fee_payments)

    # Scholarships
    scholarships = [
        (1, 30000.00, "Merit-based Academic Scholarship"),
        (4, 50000.00, "Super topper scholarship")
    ]
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
    admissions = [
        (1, datetime.date(2024, 7, 15), "MCA Batch 2024"),
        (2, datetime.date(2024, 7, 16), "MCA Batch 2024"),
        (3, datetime.date(2024, 7, 20), "MCA Batch 2024"),
        (4, datetime.date(2022, 8, 1), "BTech CSE Batch 2022"),
        (5, datetime.date(2022, 8, 3), "BTech CSE Batch 2022"),
        (7, datetime.date(2025, 7, 10), "MBA Batch 2025"),
        (8, datetime.date(2025, 7, 12), "MBA Batch 2025")
    ]
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
