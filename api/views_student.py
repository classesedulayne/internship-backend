import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .db import applications_col, users_col, serialize_doc
from .auth import auth_required, hash_password, generate_jwt_token, decode_jwt_token


def _get_decoded(request):
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return decode_jwt_token(auth_header.split(" ")[1])
    return None


@api_view(["POST"])
def student_signup(request):
    name = request.data.get("name", "").strip()
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "").strip()

    if not name or not email or not password:
        return Response({"error": "Name, email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    if len(password) < 6:
        return Response({"error": "Password must be at least 6 characters."}, status=status.HTTP_400_BAD_REQUEST)

    if users_col.find_one({"email": email}):
        return Response({"error": "An account with this email already exists."}, status=status.HTTP_409_CONFLICT)

    hashed = hash_password(password)
    result = users_col.insert_one({
        "name": name, "email": email, "password_hash": hashed,
        "role": "student",
        "created_at": datetime.datetime.now(datetime.timezone.utc),
    })

    token = generate_jwt_token({"user_id": str(result.inserted_id), "email": email, "role": "student", "name": name}, hours_valid=72)
    return Response({"token": token, "user": {"name": name, "email": email, "role": "student"}, "application": None}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def student_dashboard(request):
    decoded = _get_decoded(request)
    if not decoded:
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    email = decoded.get("email")
    app_id = decoded.get("application_id")
    app = None
    if app_id:
        app = applications_col.find_one({"application_id": app_id})
    if not app and email:
        app = applications_col.find_one({"email": email})
    return Response({
        "user": {"name": decoded.get("name", ""), "email": email, "role": decoded.get("role", "student"), "application_id": app.get("application_id") if app else None},
        "application": serialize_doc(app),
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@auth_required
def get_student_application(request):
    user = getattr(request, "current_user", None) or _get_decoded(request)
    if not user:
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    app_id = user.get("application_id")
    email = user.get("email")
    query = {"application_id": app_id} if app_id else ({"email": email} if email else None)
    if not query:
        return Response({"error": "No identifier found"}, status=status.HTTP_400_BAD_REQUEST)
    app = applications_col.find_one(query)
    if not app:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"application": serialize_doc(app)}, status=status.HTTP_200_OK)


@api_view(["PUT"])
@auth_required
def update_student_profile(request):
    user = getattr(request, "current_user", None) or _get_decoded(request)
    if not user:
        return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
    app_id = user.get("application_id")
    email = user.get("email")
    query = {"application_id": app_id} if app_id else {"email": email}
    app = applications_col.find_one(query)
    if not app:
        return Response({"error": "Application not found"}, status=status.HTTP_404_NOT_FOUND)
    allowed = ["contact_number", "hod_name", "hod_contact", "registration_no", "department"]
    updates = {f: request.data[f] for f in allowed if f in request.data}
    if updates:
        updates["updated_at"] = datetime.datetime.now(datetime.timezone.utc)
        applications_col.update_one(query, {"$set": updates})
    updated_app = applications_col.find_one(query)
    return Response({"message": "Profile updated", "application": serialize_doc(updated_app)}, status=status.HTTP_200_OK)

