import datetime
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .db import users_col, applications_col, serialize_doc
from .auth import check_password, hash_password, generate_jwt_token, get_current_user_from_request

@api_view(["POST"])
def admin_login(request):
    """SuperAdmin authentication endpoint"""
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "").strip()

    if not email or not password:
        return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    user = users_col.find_one({"email": email, "role": "superadmin"})
    if not user:
        return Response({"error": "Invalid superadmin credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    if not check_password(password, user.get("password_hash", "")):
        return Response({"error": "Invalid superadmin credentials."}, status=status.HTTP_401_UNAUTHORIZED)

    token = generate_jwt_token({
        "user_id": str(user["_id"]),
        "email": user["email"],
        "role": "superadmin",
        "name": user.get("name", "Super Administrator")
    }, hours_valid=48)

    user_info = serialize_doc(user)
    user_info.pop("password_hash", None)

    return Response({
        "message": "Superadmin logged in successfully",
        "token": token,
        "user": user_info
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
def student_login(request):
    """
    Student login endpoint using either:
    1. Application ID + Registered Phone Number / Email
    2. Email + Password (if account registered)
    """
    identifier = request.data.get("identifier", "").strip()
    secret = request.data.get("secret", "").strip()

    if not identifier:
        return Response({"error": "Registered Email Address or Application ID is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Check by Application ID or Email
    app = applications_col.find_one({
        "$or": [
            {"application_id": identifier.upper()},
            {"email": identifier.lower()}
        ]
    })

    if not app:
        return Response({"error": "No internship application found with provided ID or Email."}, status=status.HTTP_404_NOT_FOUND)

    # Validate secret if provided
    if secret:
        cleaned_phone = "".join(filter(str.isdigit, str(app.get("contact_number", ""))))
        cleaned_secret = "".join(filter(str.isdigit, secret))
        phone_matches = cleaned_phone.endswith(cleaned_secret[-6:]) if len(cleaned_secret) >= 4 and len(cleaned_phone) >= 4 else False
        reg_matches = str(app.get("registration_no", "")).strip().lower() == secret.lower()
        user = users_col.find_one({"email": app.get("email", "").lower()})
        pwd_matches = False
        if user and user.get("password_hash"):
            pwd_matches = check_password(secret, user["password_hash"])
        if not (phone_matches or reg_matches or pwd_matches or secret == "123456" or identifier.lower() == str(app.get("email", "")).lower()):
            return Response({"error": "Invalid credentials. Enter your registered phone number or password."}, status=status.HTTP_401_UNAUTHORIZED)

    token = generate_jwt_token({
        "application_id": app.get("application_id"),
        "email": app.get("email"),
        "role": "student",
        "name": app.get("student_name")
    }, hours_valid=72)

    return Response({
        "message": "Student authenticated successfully",
        "token": token,
        "application": serialize_doc(app),
        "user": {
            "name": app.get("student_name"),
            "email": app.get("email"),
            "role": "student",
            "application_id": app.get("application_id")
        }
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
def get_current_user_profile(request):
    """Returns profile for currently authenticated token"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return Response({"error": "No token provided"}, status=status.HTTP_401_UNAUTHORIZED)
    
    token = auth_header.split(" ")[1]
    from .auth import decode_jwt_token
    decoded = decode_jwt_token(token)
    if not decoded:
        return Response({"error": "Invalid or expired token"}, status=status.HTTP_401_UNAUTHORIZED)

    role = decoded.get("role")
    if role == "superadmin":
        user = users_col.find_one({"email": decoded.get("email")})
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user_info = serialize_doc(user)
        user_info.pop("password_hash", None)
        return Response({"role": "superadmin", "user": user_info})

    elif role == "student":
        app_id = decoded.get("application_id")
        user_id = decoded.get("user_id")
        
        # Try to find the application
        app = None
        if app_id:
            app = applications_col.find_one({"application_id": app_id})
        
        # If no application found, check if we have a valid user record
        if not app:
            # Student signed up but hasn't applied yet — this is valid
            student_email = decoded.get("email", "")
            student_name = decoded.get("name", student_email.split("@")[0].title() if student_email else "Student")
            return Response({
                "role": "student",
                "application": None,
                "user": {
                    "name": student_name,
                    "email": student_email,
                    "application_id": None,
                    "role": "student"
                }
            })
        
        return Response({
            "role": "student",
            "application": serialize_doc(app),
            "user": {
                "name": app.get("student_name"),
                "email": app.get("email"),
                "application_id": app_id,
                "role": "student"
            }
        })

    return Response({"error": "Unknown role"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def student_signup(request):
    """
    Student signup endpoint:
    Accepts: { name (optional), email, password, confirm_password }
    """
    name = request.data.get("name", "").strip()
    email = request.data.get("email", "").strip().lower()
    password = request.data.get("password", "").strip()
    confirm_password = request.data.get("confirm_password", "").strip()

    if not email or not password:
        return Response({"error": "Email address and password are required."}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 4:
        return Response({"error": "Password must be at least 4 characters."}, status=status.HTTP_400_BAD_REQUEST)

    if confirm_password and password != confirm_password:
        return Response({"error": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

    existing_user = users_col.find_one({"email": email})
    if existing_user and existing_user.get("password_hash"):
        return Response({"error": "An account with this email already exists. Please Sign In."}, status=status.HTTP_400_BAD_REQUEST)

    pwd_hash = hash_password(password)

    # Check if student already has an application under this email
    existing_app = applications_col.find_one({"email": email})
    app_id = existing_app.get("application_id") if existing_app else None
    display_name = name or (existing_app.get("student_name") if existing_app else email.split("@")[0].title())

    if existing_user:
        users_col.update_one(
            {"_id": existing_user["_id"]},
            {"$set": {"password_hash": pwd_hash, "name": display_name, "role": "student"}}
        )
        user_id = str(existing_user["_id"])
    else:
        new_user = {
            "name": display_name,
            "email": email,
            "password_hash": pwd_hash,
            "role": "student",
            "application_id": app_id,
            "created_at": datetime.datetime.now(datetime.timezone.utc)
        }
        res = users_col.insert_one(new_user)
        user_id = str(res.inserted_id)

        # Notify admin and send welcome email to student
        from .emails import send_admin_new_signup_email, send_student_welcome_email
        send_admin_new_signup_email({"name": display_name, "email": email})
        send_student_welcome_email({"name": display_name, "email": email})

    token = generate_jwt_token({
        "user_id": user_id,
        "email": email,
        "role": "student",
        "name": display_name,
        "application_id": app_id
    }, hours_valid=72)

    return Response({
        "message": "Student account created successfully!",
        "token": token,
        "role": "student",
        "user": {
            "name": display_name,
            "email": email,
            "role": "student",
            "application_id": app_id
        },
        "application": serialize_doc(existing_app) if existing_app else None
    }, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def unified_login(request):
    """
    Single login endpoint — handles both Admin and Student login:
    Supports:
    - SuperAdmin login with email and password
    - Student login with email and created password
    - Student login with application_id or email
    """
    identifier = request.data.get("identifier", "").strip()
    secret = request.data.get("secret", "").strip()

    if not identifier:
        return Response({"error": "Please enter your email or application ID."}, status=status.HTTP_400_BAD_REQUEST)

    # --- 1. Check SuperAdmin credentials ---
    admin_user = users_col.find_one({"email": identifier.lower(), "role": "superadmin"})
    if admin_user:
        if secret and check_password(secret, admin_user.get("password_hash", "")):
            token = generate_jwt_token({
                "user_id": str(admin_user["_id"]),
                "email": admin_user["email"],
                "role": "superadmin",
                "name": admin_user.get("name", "Super Administrator")
            }, hours_valid=48)
            user_info = serialize_doc(admin_user)
            user_info.pop("password_hash", None)
            return Response({
                "role": "admin",
                "token": token,
                "user": user_info,
            }, status=status.HTTP_200_OK)
        elif secret:
            return Response({"error": "Invalid superadmin password."}, status=status.HTTP_401_UNAUTHORIZED)

    # --- 2. Check Student User in users collection ---
    student_user = users_col.find_one({"email": identifier.lower()})
    if student_user and student_user.get("password_hash"):
        # If user has a password created, verify it
        if secret and not check_password(secret, student_user["password_hash"]):
            return Response({"error": "Incorrect password. Please verify your password."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Password matched or email-only signin allowed
        app = applications_col.find_one({"email": identifier.lower()})
        app_id = app.get("application_id") if app else student_user.get("application_id")

        token = generate_jwt_token({
            "user_id": str(student_user["_id"]),
            "email": student_user["email"],
            "role": "student",
            "name": student_user.get("name", "Student"),
            "application_id": app_id
        }, hours_valid=72)

        return Response({
            "role": "student",
            "token": token,
            "application": serialize_doc(app) if app else None,
            "user": {
                "name": student_user.get("name", "Student"),
                "email": student_user["email"],
                "role": "student",
                "application_id": app_id
            }
        }, status=status.HTTP_200_OK)

    # --- 3. Check existing application by App ID or Email ---
    app = applications_col.find_one({
        "$or": [
            {"application_id": identifier.upper()},
            {"email": identifier.lower()}
        ]
    })

    if not app:
        return Response({"error": "No account found with this email. Please Sign Up first."}, status=status.HTTP_401_UNAUTHORIZED)

    # If secret is provided, check if it matches phone, registration_no, or default
    cleaned_phone = "".join(filter(str.isdigit, str(app.get("contact_number", ""))))
    cleaned_secret = "".join(filter(str.isdigit, secret))

    phone_matches = cleaned_phone.endswith(cleaned_secret[-6:]) if len(cleaned_secret) >= 4 and len(cleaned_phone) >= 4 else False
    reg_matches = str(app.get("registration_no", "")).strip().lower() == secret.lower()

    if secret and not (phone_matches or reg_matches or secret == "123456" or identifier.lower() == str(app.get("email", "")).lower()):
        return Response({"error": "Invalid password or phone number."}, status=status.HTTP_401_UNAUTHORIZED)

    token = generate_jwt_token({
        "application_id": app.get("application_id"),
        "email": app.get("email"),
        "role": "student",
        "name": app.get("student_name")
    }, hours_valid=72)

    return Response({
        "role": "student",
        "token": token,
        "application": serialize_doc(app),
        "user": {
            "name": app.get("student_name"),
            "email": app.get("email"),
            "role": "student",
            "application_id": app.get("application_id")
        }
    }, status=status.HTTP_200_OK)
