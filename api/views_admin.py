import csv
import datetime
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .db import applications_col, settings_col, programs_col, domains_col, serialize_doc, serialize_docs
from .auth import superadmin_required

@api_view(["GET"])
@superadmin_required
def get_dashboard_stats(request):
    """SuperAdmin analytics dashboard statistics"""
    total_apps = applications_col.count_documents({})
    
    # Program breakdown
    fyugp_count = applications_col.count_documents({"program_code": "FYUGP"})
    btech_count = applications_col.count_documents({"program_code": "BTECH"})
    pg_count = applications_col.count_documents({"program_code": "PG"})

    # Payment status breakdown
    pending_payments = applications_col.count_documents({"payment_status": "Pending"})
    verified_payments = applications_col.count_documents({"payment_status": "Verified"})
    rejected_payments = applications_col.count_documents({"payment_status": "Rejected"})

    # Application status breakdown
    approved_count = applications_col.count_documents({"application_status": "Approved"})
    enrolled_count = applications_col.count_documents({"application_status": "Enrolled"})
    under_review_count = applications_col.count_documents({"application_status": "Under Review"})

    # Domain breakdown
    domain_stats = []
    all_domains = list(domains_col.find())
    for d in all_domains:
        d_name = d.get("name")
        c = applications_col.count_documents({"$or": [{"domain": d_name}, {"domain_id": d.get("id")}]})
        domain_stats.append({
            "name": d_name,
            "id": d.get("id"),
            "color": d.get("color", "#3B82F6"),
            "count": c
        })

    # Recent applications
    recent = list(applications_col.find().sort("created_at", -1).limit(5))

    return Response({
        "total_applications": total_apps,
        "programs": {
            "FYUGP": fyugp_count,
            "BTECH": btech_count,
            "PG": pg_count
        },
        "payments": {
            "pending": pending_payments,
            "verified": verified_payments,
            "rejected": rejected_payments
        },
        "statuses": {
            "approved": approved_count,
            "enrolled": enrolled_count,
            "under_review": under_review_count,
            "pending": pending_payments
        },
        "domains": domain_stats,
        "recent_applications": serialize_docs(recent)
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@superadmin_required
def get_all_applications(request):
    """Retrieve filtered and searched list of applications for superadmin"""
    query = {}

    # Filter by program
    program = request.query_params.get("program")
    if program and program != "ALL":
        query["program_code"] = program.upper()

    # Filter by domain
    domain = request.query_params.get("domain")
    if domain and domain != "ALL":
        query["$or"] = [{"domain": domain}, {"domain_id": domain}]

    # Filter by payment status
    payment_status = request.query_params.get("payment_status")
    if payment_status and payment_status != "ALL":
        query["payment_status"] = payment_status

    # Filter by application status
    app_status = request.query_params.get("status")
    if app_status and app_status != "ALL":
        query["application_status"] = app_status

    # Search keyword
    search = request.query_params.get("search", "").strip()
    if search:
        search_filter = {
            "$or": [
                {"student_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"contact_number": {"$regex": search, "$options": "i"}},
                {"college_name": {"$regex": search, "$options": "i"}},
                {"department": {"$regex": search, "$options": "i"}},
                {"application_id": {"$regex": search, "$options": "i"}},
                {"transaction_id": {"$regex": search, "$options": "i"}},
                {"hod_name": {"$regex": search, "$options": "i"}}
            ]
        }
        if "$or" in query:
            query = {"$and": [query, search_filter]}
        else:
            query.update(search_filter)

    apps = list(applications_col.find(query).sort("created_at", -1))
    return Response({
        "count": len(apps),
        "applications": serialize_docs(apps)
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@superadmin_required
def get_application_detail(request, application_id):
    """Get single application detail"""
    app = applications_col.find_one({"application_id": application_id})
    if not app:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(serialize_doc(app), status=status.HTTP_200_OK)


@api_view(["PATCH"])
@superadmin_required
def update_application_status(request, application_id):
    """Update verification status, application status, or admin notes"""
    app = applications_col.find_one({"application_id": application_id})
    if not app:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)

    updates = {}
    if "payment_status" in request.data:
        updates["payment_status"] = request.data["payment_status"]
        # If payment verified and status still submitted, advance to Approved
        if request.data["payment_status"] == "Verified" and app.get("application_status") in ["Submitted", "Under Review"]:
            updates["application_status"] = "Approved"

    if "application_status" in request.data:
        updates["application_status"] = request.data["application_status"]

    if "admin_notes" in request.data:
        updates["admin_notes"] = request.data["admin_notes"]

    updates["updated_at"] = datetime.datetime.now(datetime.timezone.utc)

    applications_col.update_one({"application_id": application_id}, {"$set": updates})
    updated_app = applications_col.find_one({"application_id": application_id})

    return Response({
        "message": "Application updated successfully",
        "application": serialize_doc(updated_app)
    }, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@superadmin_required
def delete_application(request, application_id):
    """Delete an application"""
    res = applications_col.delete_one({"application_id": application_id})
    if res.deleted_count == 0:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": f"Application {application_id} deleted successfully."}, status=status.HTTP_200_OK)


@api_view(["GET"])
@superadmin_required
def export_applications_csv(request):
    """Export all applications to CSV file for Excel analysis"""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="internship_registrations.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Application ID",
        "Program",
        "Student Name",
        "Email",
        "Phone",
        "College Name",
        "Department",
        "Academic Year",
        "Registration No",
        "Domain Track",
        "Internship Month",
        "HOD Name",
        "HOD Contact",
        "Transaction / UTR ID",
        "Payment Status",
        "Application Status",
        "Admin Notes",
        "Registration Date"
    ])

    apps = list(applications_col.find().sort("created_at", -1))
    for app in apps:
        writer.writerow([
            app.get("application_id", ""),
            app.get("program_code", ""),
            app.get("student_name", ""),
            app.get("email", ""),
            app.get("contact_number", ""),
            app.get("college_name", ""),
            app.get("department", ""),
            app.get("academic_year", ""),
            app.get("registration_no", ""),
            app.get("domain", ""),
            app.get("internship_month", "May 2026"),
            app.get("hod_name", ""),
            app.get("hod_contact", ""),
            app.get("transaction_id", ""),
            app.get("payment_status", ""),
            app.get("application_status", ""),
            app.get("admin_notes", ""),
            app.get("created_at", "")
        ])

    return response


@api_view(["GET", "POST"])
@superadmin_required
def admin_settings_view(request):
    """View and update portal settings (UPI ID, QR code placeholder, fee)"""
    if request.method == "GET":
        s = settings_col.find_one({"key": "main_settings"})
        return Response(serialize_doc(s), status=status.HTTP_200_OK)

    elif request.method == "POST":
        data = request.data
        updates = {
            "portal_name": data.get("portal_name", "Looka Internship Portal"),
            "upi_id": data.get("upi_id", "looka.internship@upi"),
            "upi_name": data.get("upi_name", "Looka EdTech"),
            "default_fee": data.get("default_fee", 999),
            "support_email": data.get("support_email", "internships@looka.com"),
            "support_phone": data.get("support_phone", "+91 98765 43210"),
            "qr_code_note": data.get("qr_code_note", "Scan UPI QR code"),
            "updated_at": datetime.datetime.now(datetime.timezone.utc)
        }
        if "qr_code_image" in data:
            updates["qr_code_image"] = data["qr_code_image"]

        settings_col.update_one({"key": "main_settings"}, {"$set": updates}, upsert=True)
        return Response({"message": "Settings updated successfully", "settings": updates}, status=status.HTTP_200_OK)
