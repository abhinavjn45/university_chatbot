# University ERP Conversational Analytics Assistant

## Product Requirements Document (PRD) & Technical Design Specification

### Version

v1.0

### Project Owner

Abhinav Jain

### Objective

Develop an AI-powered conversational assistant for a University ERP system that enables users to interact with ERP data using natural language instead of navigating multiple dashboards and reports.

The assistant should convert natural language questions into secure SQL queries, execute them against the ERP database, and return human-readable responses while maintaining context across conversations.

---

# Problem Statement

University ERP systems contain large volumes of information across academics, attendance, examinations, fees, faculty, admissions, and administration.

Users currently need to:

* Navigate multiple screens
* Apply filters manually
* Understand ERP workflows
* Generate reports manually

The proposed solution enables users to ask questions in natural language such as:

* Which students have attendance below 75%?
* Show fee defaulters from MCA 4th Trimester.
* Who are the toppers in Data Structures?
* How many students are currently enrolled in MCA?

and receive instant responses.

---

# Goals

## Primary Goals

* Natural language querying of ERP data
* Human-readable responses
* Context-aware follow-up questions
* Secure SQL execution
* Role-based access control
* Cost-optimized architecture

## Secondary Goals

* Analytics generation
* Trend analysis
* Administrative insights
* Reporting assistance

---

# User Roles

## Student

Allowed:

* Personal attendance
* Personal results
* Personal fee status
* Personal timetable

Restricted:

* Other students' records
* Faculty information
* Administrative reports

---

## Faculty

Allowed:

* Class attendance
* Subject analytics
* Student performance
* Course-related information

Restricted:

* Finance data
* HR data

---

## Department Admin

Allowed:

* Student records
* Academic reports
* Attendance reports
* Fee summaries

---

## Super Admin

Full access to all modules.

---

# Functional Requirements

## FR-01 Natural Language Queries

Users can ask questions in plain English.

Examples:

* Show students with attendance below 75%
* List fee defaulters
* Show toppers from MCA
* Which faculty handles DBMS?

---

## FR-02 Follow-Up Questions

Example:

User:
Show top 5 students by CGPA

Assistant:
Displays results

User:
Which one has highest attendance?

System should understand context.

---

## FR-03 Human Readable Responses

Instead of returning raw SQL data:

Bad:

Student_ID = 1021

Good:

Rahul Sharma currently has the highest attendance at 98%.

---

## FR-04 SQL Generation

System converts natural language into valid SQL queries.

---

## FR-05 SQL Validation

System must reject:

* DROP
* DELETE
* UPDATE
* ALTER
* INSERT
* TRUNCATE

Only read operations allowed.

---

## FR-06 Role-Based Access Control

Users only access permitted data.

---

## FR-07 Audit Logging

Store:

* User
* Query
* Generated SQL
* Response
* Timestamp
* Execution time

---

## FR-08 Query Caching

Frequently repeated queries should be served from cache.

---

# Business Rules Layer

The assistant must understand ERP terminology.

Examples:

Topper = Highest CGPA

Detained Student = Attendance < 75%

Fee Defaulter = Pending Fees > 0

Active Student = Status = Active

Graduated Student = Completion Status = Graduated

Current Semester = Latest Active Semester

These rules should be stored in a metadata repository.

---

# Domain Architecture

The ERP should be divided into domains.

## Academic Domain

Tables:

* students
* courses
* semesters
* subjects
* results

---

## Attendance Domain

Tables:

* attendance
* attendance_logs
* subjects

---

## Fees Domain

Tables:

* fee_structure
* fee_payments
* scholarships

---

## Faculty Domain

Tables:

* faculty
* departments
* faculty_workload

---

## Administration Domain

Tables:

* admissions
* departments
* notifications

---

# Non-Functional Requirements

## Performance

Average Response Time:
< 5 seconds

---

## Availability

Target:
99% uptime

---

## Scalability

Support:

* 100 concurrent users
* 10,000 daily requests

---

## Security

Read-only database access.

No write operations.

---

## Cost Optimization

Cache responses.

Cache schemas.

Summarize conversation history.

Minimize LLM calls.

---

# Technology Stack

Frontend

* React.js
* Axios
* Tailwind CSS

Deployment:
Vercel

---

Backend

* FastAPI
* SQLAlchemy
* LangGraph

Deployment:
Render

---

Database

* MySQL

Hosted:
Hostinger Remote MySQL

---

AI Layer

* Grok API

Provider abstraction must allow future replacement with:

* GPT
* Gemini
* Claude
* Local Models

---

Cache & Memory

* Redis
* Upstash Redis

---

Rate Limiting

* SlowAPI
* Redis-backed limiter

---

# System Architecture

User
→ React Frontend
→ FastAPI API Layer
→ Rate Limiter
→ Authentication Layer
→ LangGraph Workflow
→ SQL Validation Layer
→ MySQL Database
→ Response Generator
→ User

Supporting Services:

* Redis Cache
* Session Memory
* Audit Logs

---

# LangGraph Workflow

START

1. Authenticate User

2. Load Session Context

3. Determine User Role

4. Domain Classification

5. Retrieve Relevant Schema

6. Generate SQL

7. Validate SQL

8. Check Cache

9. Execute Query

10. Generate Human Response

11. Save Session Context

12. Store Audit Log

END

---

# Redis Strategy

## Session Memory

Key:

session:{session_id}

Stores:

* Previous questions
* Previous responses
* Conversation summary

TTL:
24 hours

---

## Query Cache

Key:

query_hash

Stores:

* SQL
* Results
* Final response

TTL:
1 hour

---

# Security Requirements

## SQL Restrictions

Allowed:

SELECT

WITH

Forbidden:

DROP

DELETE

UPDATE

ALTER

INSERT

TRUNCATE

---

## Query Timeout

Maximum:
10 seconds

---

## Automatic Result Limiting

Default:
LIMIT 100

---

## Prompt Injection Protection

Detect:

* Ignore instructions
* Reveal system prompt
* Show credentials
* Drop table

Reject requests automatically.

---

# Logging

Store:

Question

Generated SQL

Execution Time

Rows Returned

User Role

Cache Hit/Miss

Timestamp

---

# API Endpoints

POST /chat

POST /login

GET /conversation/{session_id}

GET /health

GET /metrics

---

# Success Metrics

SQL Accuracy:

> 90%

Average Response Time:
< 5 seconds

Cache Hit Rate:

> 30%

User Satisfaction:

> 80%

Query Failure Rate:
< 5%

---

# Future Enhancements

* Charts and graphs
* Export to PDF
* Voice queries
* Multi-language support
* Dashboard generation
* Predictive analytics
* Agentic workflows
* Fine-tuned university-specific model

---

# MVP Scope (Interview Demo)

Must Have:

✓ React Frontend

✓ FastAPI Backend

✓ MySQL Integration

✓ Grok API

✓ LangGraph Workflow

✓ Redis Memory

✓ SQL Validation

✓ Query Caching

✓ Rate Limiting

✓ Audit Logging

✓ Domain-Based Schema Retrieval

✓ Business Rules Layer

Nice To Have:

✓ RBAC

✓ Metrics Dashboard

✓ Query Analytics

Not Required:

✗ RAG

✗ Vector Database

✗ Multi-Agent Architecture

✗ Kubernetes

✗ Docker Swarm

✗ Fine-Tuning