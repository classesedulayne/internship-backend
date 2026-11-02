import os
import random
import datetime
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
from .db import (
    programs_col,
    domains_col,
    settings_col,
    applications_col,
    users_col,
    serialize_doc,
    serialize_docs
)
from .auth import hash_password

@api_view(["GET"])
def get_programs(request):
    """Retrieve all available internship programs (FYUGP, B.Tech, PG)"""
    programs = list(programs_col.find())
    return Response(serialize_docs(programs), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_domains(request):
    """Retrieve all internship domains (AI Data Science, AIML, Full Stack, Full Stack with AI, Cybersecurity)"""
    domains = list(domains_col.find())
    return Response(serialize_docs(domains), status=status.HTTP_200_OK)


@api_view(["GET"])
def get_public_settings(request):
    """Retrieve public payment info (UPI ID, QR code placeholder, contact info)"""
    app_settings = settings_col.find_one({"key": "main_settings"})
    if not app_settings:
        app_settings = {
            "portal_name": "Looka Internship Portal",
            "upi_id": "looka.internship@upi",
            "upi_name": "Looka EdTech & Hiring Solutions",
            "default_fee": 999,
            "qr_code_image": "/media/qr_placeholder.png",
            "support_email": "internships@looka.com",
            "support_phone": "+91 98765 43210"
        }
    return Response(serialize_doc(app_settings), status=status.HTTP_200_OK)


@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def register_application(request):
    """
    Register a student for an internship:
    Validates mandatory name, college, contact, department, HOD, and domain.
    """
    data = request.data

    # Required fields validation
    required_fields = [
        ("student_name", "Student Name"),
        ("college_name", "College Name"),
        ("contact_number", "Contact Number"),
        ("email", "Email Address"),
        ("department", "Department"),
        ("hod_name", "HOD Name"),
        ("domain", "Internship Domain"),
        ("program_code", "Internship Program (FYUGP / B.Tech / PG)")
    ]

    missing = []
    for field, label in required_fields:
        if not data.get(field) or str(data.get(field)).strip() == "":
            missing.append(label)

    if missing:
        return Response({
            "error": f"Please fill all mandatory fields: {', '.join(missing)}"
        }, status=status.HTTP_400_BAD_REQUEST)

    # Screenshot is optional (payment not required)
    screenshot_file = request.FILES.get("screenshot")
    screenshot_url = None

    if screenshot_file:
        ext = os.path.splitext(screenshot_file.name)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp", ".pdf"]:
            return Response({"error": "Unsupported file format. Please upload PNG, JPG, or PDF."}, status=status.HTTP_400_BAD_REQUEST)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = f"receipt_{timestamp}_{random.randint(1000, 9999)}{ext}"
        save_path = os.path.join(settings.MEDIA_ROOT, "receipts", clean_name)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb+") as destination:
            for chunk in screenshot_file.chunks():
                destination.write(chunk)

        screenshot_url = f"/media/receipts/{clean_name}"

    # Program details
    program_code = data.get("program_code", "FYUGP").upper()
    prog_info = programs_col.find_one({"code": program_code})
    program_title = prog_info.get("title") if prog_info else program_code

    # Generate unique application ID
    year_prefix = datetime.datetime.now().year
    prog_short = program_code[:4]
    random_num = random.randint(1000, 9999)
    application_id = f"INTR-{year_prefix}-{prog_short}-{random_num}"

    # Verify uniqueness
    while applications_col.find_one({"application_id": application_id}):
        random_num = random.randint(1000, 9999)
        application_id = f"INTR-{year_prefix}-{prog_short}-{random_num}"

    new_app = {
        "application_id": application_id,
        "program_code": program_code,
        "program_title": program_title,
        "student_name": data.get("student_name", "").strip(),
        "email": data.get("email", "").strip().lower(),
        "contact_number": data.get("contact_number", "").strip(),
        "college_name": data.get("college_name", "").strip(),
        "department": data.get("department", "").strip(),
        "hod_name": data.get("hod_name", "").strip(),
        "hod_contact": data.get("hod_contact", "").strip(),
        "domain": data.get("domain", "").strip(),
        "domain_id": data.get("domain_id", ""),
        "internship_month": data.get("internship_month", "May 2026").strip(),
        "duration_months": data.get("duration_months", "1 Month").strip(),
        "internship_hours": data.get("internship_hours", "120 Hours").strip(),
        "academic_year": data.get("academic_year", "Not specified").strip(),
        "registration_no": data.get("registration_no", "").strip(),
        "transaction_id": data.get("transaction_id", "").strip(),
        "screenshot_url": screenshot_url,
        "payment_status": "Not Required",      # Not Required, Pending, Verified, Rejected
        "application_status": "Submitted",    # Submitted, Under Review, Approved, Enrolled, Rejected
        "admin_notes": "Application received. Verification in progress.",
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at": datetime.datetime.now(datetime.timezone.utc)
    }

    result = applications_col.insert_one(new_app)

    # Send admin notification email and student confirmation email
    from .emails import send_admin_new_application_email, send_student_application_confirmation_email
    send_admin_new_application_email(new_app)
    send_student_application_confirmation_email(new_app)

    # Also create student user record if not present
    existing_user = users_col.find_one({"email": new_app["email"]})
    if not existing_user:
        student_user = {
            "name": new_app["student_name"],
            "email": new_app["email"],
            "phone": new_app["contact_number"],
            "role": "student",
            "application_id": application_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }
        users_col.insert_one(student_user)

    from .auth import generate_jwt_token
    token = generate_jwt_token({
        "application_id": application_id,
        "email": new_app["email"],
        "role": "student",
        "name": new_app["student_name"]
    }, hours_valid=72)

    return Response({
        "message": "Internship registration submitted successfully!",
        "application_id": application_id,
        "token": token,
        "user": {
            "name": new_app["student_name"],
            "email": new_app["email"],
            "role": "student",
            "application_id": application_id
        },
        "application": serialize_doc(new_app)
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def get_application_status(request, application_id):
    """Lookup application status by Application ID or Email"""
    app = applications_col.find_one({
        "$or": [
            {"application_id": application_id.upper()},
            {"email": application_id.lower()}
        ]
    })
    if not app:
        return Response({"error": "Application not found with the provided identifier."}, status=status.HTTP_404_NOT_FOUND)

    return Response(serialize_doc(app), status=status.HTTP_200_OK)
