import os
import sys
import django
import datetime

# Setup django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "internship_backend.settings")
django.setup()

from api.db import users_col, programs_col, domains_col, settings_col, applications_col
from api.auth import hash_password

def seed():
    print("[INFO] Starting database seeding for Internship Registration Portal...")

    # 1. Seed SuperAdmin
    superadmin_email = "nandananb2003@gmail.com"
    existing_admin = users_col.find_one({"email": superadmin_email})
    if not existing_admin:
        admin_doc = {
            "name": "Super Administrator",
            "email": superadmin_email,
            "password_hash": hash_password("nandana@123"),
            "role": "superadmin",
            "created_at": datetime.datetime.now(datetime.timezone.utc),
            "phone": "+91 9876543210"
        }
        users_col.insert_one(admin_doc)
        print("[SUCCESS] SuperAdmin created: nandananb2003@gmail.com / nandana@123")
    else:
        print("[INFO] SuperAdmin already exists: nandananb2003@gmail.com")

    # 2. Seed Programs (FYUGP, B.Tech, PG)
    programs = [
        {
            "code": "FYUGP",
            "title": "Four Year Undergraduate Programme (FYUGP)",
            "subtitle": "National Education Policy Aligned Industrial Track",
            "badge": "NEP 2020 Aligned",
            "duration": "1 - 6 Months",
            "eligibility": "1st to 4th Year FYUGP Undergraduates",
            "icon": "GraduationCap",
            "description": "Structured curriculum designed for FYUGP students providing university credit validation, hands-on production codebases, and capstone project mentorship.",
            "perks": [
                "Curriculum Credit Certificate & Letter of Recommendation",
                "1-on-1 Senior Industry Architect Mentorship",
                "Flexible Shift Timings for College Schedules",
                "Direct Fast-Track to Job Portal Placements"
            ],
            "popular": False,
            "fee": 999
        },
        {
            "code": "BTECH",
            "title": "B.Tech / B.E Engineering Internship",
            "subtitle": "Core Engineering & Production Level Experience",
            "badge": "Most Popular",
            "duration": "1 - 6 Months",
            "eligibility": "B.Tech / B.E Students (All Branches - CSE, IT, ECE, etc.)",
            "icon": "Cpu",
            "description": "Intensive engineering development track. Build scalable microservices, AI pipelines, modern web applications, and cyber protection architectures.",
            "perks": [
                "Real-World Production Repository Contributions",
                "Internship Experience Letter & Verified Credential URL",
                "Mock Technical Interviews & Resume Optimization",
                "Direct Interview Referrals to Partner Companies"
            ],
            "popular": True,
            "fee": 999
        },
        {
            "code": "PG",
            "title": "Postgraduate Advanced Internship (PG)",
            "subtitle": "Masters & Specialized Research Cohort",
            "badge": "Advanced Track",
            "duration": "3 - 6 Months",
            "eligibility": "MCA, M.Tech, M.Sc CS/IT/Data Science Students",
            "icon": "Award",
            "description": "Tailored for master's degree candidates seeking enterprise-grade problem statements, advanced AI/ML research papers, and distributed systems architecture.",
            "perks": [
                "Master's Final Year Major Project Guidance & Proof",
                "Deep-dive High Concurrency & Cloud Native Systems",
                "Letter of Recommendation from CTO / Head of Engineering",
                "Priority Placement Pipeline for Senior Engineering Roles"
            ],
            "popular": False,
            "fee": 1299
        }
    ]

    for prog in programs:
        programs_col.update_one({"code": prog["code"]}, {"$set": prog}, upsert=True)
    print("[SUCCESS] Seeded 3 Core Internship Programs: FYUGP, B.Tech, PG")

    # 3. Seed Domains (Specified by user)
    domains = [
        {
            "id": "ai_datascience",
            "name": "AI Data Science",
            "description": "Exploratory Data Analysis, Pandas, NumPy, Scikit-Learn, Predictive Modeling, and Real-World Analytics Dashboards.",
            "skills": ["Python", "Pandas", "Scikit-Learn", "Data Viz", "SQL"],
            "color": "#3B82F6"
        },
        {
            "id": "aiml",
            "name": "AIML (Artificial Intelligence & Machine Learning)",
            "description": "Deep Learning, Neural Networks, Computer Vision, NLP, PyTorch/TensorFlow, and Model Deployment.",
            "skills": ["PyTorch", "TensorFlow", "Transformers", "OpenCV", "FastAPI"],
            "color": "#8B5CF6"
        },
        {
            "id": "fullstack",
            "name": "Full Stack",
            "description": "Modern frontend with React/Next.js, scalable backend with Python/Django/Node, MongoDB/PostgreSQL, and REST APIs.",
            "skills": ["React", "Python/Django", "MongoDB", "Tailwind CSS", "REST APIs"],
            "color": "#10B981"
        },
        {
            "id": "fullstack_ai",
            "name": "Full Stack with AI",
            "description": "Building next-gen AI-powered Web Apps: LLM orchestration, LangChain, RAG pipelines, OpenAI/Groq APIs, and Full Stack integration.",
            "skills": ["React", "Python/Django", "LangChain", "Vector DBs", "RAG Systems"],
            "color": "#F59E0B"
        },
        {
            "id": "cybersecurity",
            "name": "Cybersecurity",
            "description": "Ethical Hacking, Penetration Testing, Network Security, Web Application Security (OWASP Top 10), and SOC Operations.",
            "skills": ["Ethical Hacking", "OWASP Top 10", "Burp Suite", "Network Security", "Linux"],
            "color": "#EC4899"
        }
    ]

    for dom in domains:
        domains_col.update_one({"id": dom["id"]}, {"$set": dom}, upsert=True)
    print("[SUCCESS] Seeded 5 Internship Domains: AI Data Science, AIML, Full Stack, Full Stack with AI, Cybersecurity")

    # 4. Seed Portal Settings (UPI, QR placeholder, etc.)
    portal_settings = {
        "key": "main_settings",
        "portal_name": "Looka Internship Portal",
        "upi_id": "looka.internship@upi",
        "upi_name": "Looka EdTech & Hiring Solutions",
        "default_fee": 999,
        "support_email": "internships@looka.com",
        "support_phone": "+91 98765 43210",
        "qr_code_note": "Scan with any UPI App (GPay, PhonePe, Paytm) to pay the registration fee. Upload the screenshot and enter the Transaction/UTR ID below.",
        "qr_code_image": "/media/qr_placeholder.png",
        "updated_at": datetime.datetime.now(datetime.timezone.utc)
    }
    settings_col.update_one({"key": "main_settings"}, {"$set": portal_settings}, upsert=True)
    print("[SUCCESS] Seeded Portal Settings with UPI & Payment Details")

    # 5. Seed Demo Applications for SuperAdmin demo
    demo_apps = [
        {
            "application_id": "INTR-2026-FYU-1001",
            "program_code": "FYUGP",
            "program_title": "Four Year Undergraduate Programme (FYUGP)",
            "student_name": "Rahul Sharma",
            "email": "rahul.sharma@example.com",
            "contact_number": "+91 98471 23456",
            "college_name": "St. Joseph's College of Engineering",
            "department": "Computer Science & Design",
            "hod_name": "Dr. V. K. Nambiar",
            "hod_contact": "+91 94470 11223",
            "domain": "Full Stack with AI",
            "domain_id": "fullstack_ai",
            "academic_year": "3rd Year",
            "registration_no": "CS22D045",
            "transaction_id": "UPI/428910284729/GPay",
            "screenshot_url": "/media/receipts/sample_receipt_1.png",
            "payment_status": "Verified",
            "application_status": "Approved",
            "admin_notes": "Payment verified via UPI bank statement. Enrolled in Cohort A.",
            "created_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2),
            "updated_at": datetime.datetime.now(datetime.timezone.utc)
        },
        {
            "application_id": "INTR-2026-BTECH-1002",
            "program_code": "BTECH",
            "program_title": "B.Tech / B.E Engineering Internship",
            "student_name": "Ananya Nair",
            "email": "ananya.nair@example.com",
            "contact_number": "+91 97452 87654",
            "college_name": "Model Engineering College, Kochi",
            "department": "Computer Science & Engineering",
            "hod_name": "Prof. S. R. George",
            "hod_contact": "+91 94461 44556",
            "domain": "AIML",
            "domain_id": "aiml",
            "academic_year": "Final Year (4th Year)",
            "registration_no": "MEC21CS108",
            "transaction_id": "TXN_982347102938",
            "screenshot_url": "/media/receipts/sample_receipt_2.png",
            "payment_status": "Pending",
            "application_status": "Under Review",
            "admin_notes": "Awaiting UTR reconciliation from accounts.",
            "created_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=14),
            "updated_at": datetime.datetime.now(datetime.timezone.utc)
        },
        {
            "application_id": "INTR-2026-PG-1003",
            "program_code": "PG",
            "program_title": "Postgraduate Advanced Internship (PG)",
            "student_name": "Farhan Mohammed",
            "email": "farhan.m@example.com",
            "contact_number": "+91 99610 55443",
            "college_name": "National Institute of Technology (NIT)",
            "department": "Department of Computer Applications (MCA)",
            "hod_name": "Dr. T. Radhakrishnan",
            "hod_contact": "+91 98460 77889",
            "domain": "Cybersecurity",
            "domain_id": "cybersecurity",
            "academic_year": "2nd Year MCA",
            "registration_no": "NIT23MCA021",
            "transaction_id": "PAYTM_REF_8876129481",
            "screenshot_url": "/media/receipts/sample_receipt_3.png",
            "payment_status": "Verified",
            "application_status": "Approved",
            "admin_notes": "Excellent credentials. Assigned to Red Team Internship track.",
            "created_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1),
            "updated_at": datetime.datetime.now(datetime.timezone.utc)
        }
    ]

    for app in demo_apps:
        applications_col.update_one({"application_id": app["application_id"]}, {"$set": app}, upsert=True)
    print("[SUCCESS] Seeded Demo Applications")

    print("\n[DONE] Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
