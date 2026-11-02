import logging
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)

def _send_email_async(subject, body_text, body_html, recipient_list):
    """Internal helper to dispatch email safely in a background thread."""
    def task():
        try:
            from_email = getattr(settings, "EMAIL_HOST_USER", "").strip()
            if not from_email or not getattr(settings, "EMAIL_HOST_PASSWORD", "").strip():
                print(f"[EMAIL SERVICE WARNING] Email not sent ('{subject}'): EMAIL_HOST_USER or EMAIL_HOST_PASSWORD is not configured in backend/.env")
                return

            email = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=from_email,
                to=recipient_list
            )
            if body_html:
                email.attach_alternative(body_html, "text/html")

            email.send(fail_silently=False)
            safe_subj = subject.encode("ascii", "ignore").decode("ascii").strip()
            print(f"[EMAIL SERVICE SUCCESS] Sent email '{safe_subj}' to {recipient_list}")
        except Exception as e:
            safe_subj = subject.encode("ascii", "ignore").decode("ascii").strip()
            print(f"[EMAIL SERVICE ERROR] Failed to send email '{safe_subj}': {str(e)}")

    thread = threading.Thread(target=task, daemon=True)
    thread.start()


# ====================================================================
# 1. NOTIFICATIONS FOR ADMIN
# ====================================================================

def send_admin_new_application_email(app_data):
    """
    Sends an email notification to the Admin when a student submits an internship application.
    """
    admin_email = getattr(settings, "ADMIN_EMAIL", "contact.edulayne@gmail.com")
    student_name = app_data.get("student_name", "Student")
    student_email = app_data.get("email", "")
    app_id = app_data.get("application_id", "N/A")
    program = app_data.get("program_title", app_data.get("program_code", "Internship Program"))
    domain = app_data.get("domain", "General")
    college = app_data.get("college_name", "Not specified")
    dept = app_data.get("department", "Not specified")
    phone = app_data.get("contact_number", "Not specified")
    duration = app_data.get("duration_months", "1 Month")
    hours = app_data.get("internship_hours", "120 Hours")

    subject = f"🎓 New Internship Registration: {student_name} ({app_id})"

    text_content = f"""
NEW INTERNSHIP APPLICATION RECEIVED
===================================
A new student has registered for an internship program:

Application ID: {app_id}
Student Name:   {student_name}
Email Address:  {student_email}
Contact Number: {phone}
College Name:   {college}
Department:     {dept}
Program:        {program}
Domain:         {domain}
Duration:       {duration}
Required Hours: {hours}

Please log in to the admin dashboard to review and manage this application.
"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ background: #ffffff; border-radius: 12px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%); color: #ffffff; padding: 28px 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; }}
        .body {{ padding: 24px; }}
        .badge {{ display: inline-block; background: #e0f2fe; color: #0284c7; padding: 4px 12px; border-radius: 9999px; font-size: 13px; font-weight: 600; margin-bottom: 16px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        td.label {{ font-weight: 600; color: #64748b; width: 35%; }}
        td.value {{ color: #0f172a; font-weight: 500; }}
        .footer {{ background: #f8fafc; padding: 16px 24px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>🎓 New Student Registration</h1>
          <p>Internship Application Portal Notification</p>
        </div>
        <div class="body">
          <div class="badge">Application ID: {app_id}</div>
          <p style="margin: 0 0 16px 0; font-size: 15px;">A new internship application has just been submitted by <strong>{student_name}</strong>:</p>
          <table>
            <tr><td class="label">Student Name</td><td class="value">{student_name}</td></tr>
            <tr><td class="label">Email Address</td><td class="value"><a href="mailto:{student_email}">{student_email}</a></td></tr>
            <tr><td class="label">Phone</td><td class="value">{phone}</td></tr>
            <tr><td class="label">College</td><td class="value">{college}</td></tr>
            <tr><td class="label">Department</td><td class="value">{dept}</td></tr>
            <tr><td class="label">Program</td><td class="value"><strong>{program}</strong></td></tr>
            <tr><td class="label">Domain</td><td class="value"><span style="color: #2563eb; font-weight: 600;">{domain}</span></td></tr>
            <tr><td class="label">Duration</td><td class="value">{duration}</td></tr>
            <tr><td class="label">Required Hours</td><td class="value"><span style="color: #2563eb; font-weight: 700;">{hours}</span></td></tr>
          </table>
        </div>
        <div class="footer">
          Internship Portal &bull; Automated Admin Notification
        </div>
      </div>
    </body>
    </html>
    """

    _send_email_async(
        subject=subject,
        body_text=text_content,
        body_html=html_content,
        recipient_list=[admin_email]
    )


def send_admin_new_signup_email(user_data):
    """
    Sends an email notification to the Admin when a new student creates an account.
    """
    admin_email = getattr(settings, "ADMIN_EMAIL", "contact.edulayne@gmail.com")
    name = user_data.get("name", "New Student")
    email = user_data.get("email", "")

    subject = f"👤 New Student Account Created: {name}"

    text_content = f"""
NEW STUDENT ACCOUNT CREATED
===========================
A new student has signed up on the Internship Portal:

Name:  {name}
Email: {email}
"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ background: #ffffff; border-radius: 12px; max-width: 500px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; overflow: hidden; }}
        .header {{ background: #0f172a; color: #ffffff; padding: 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; }}
        .body {{ padding: 24px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        td.label {{ font-weight: 600; color: #64748b; width: 35%; }}
        td.value {{ color: #0f172a; font-weight: 500; }}
        .footer {{ background: #f8fafc; padding: 14px 24px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>👤 New Student Account</h1>
        </div>
        <div class="body">
          <p style="margin: 0 0 16px 0; font-size: 14px;">A new student has registered an account:</p>
          <table>
            <tr><td class="label">Name</td><td class="value"><strong>{name}</strong></td></tr>
            <tr><td class="label">Email</td><td class="value"><a href="mailto:{email}">{email}</a></td></tr>
            <tr><td class="label">Role</td><td class="value">Student</td></tr>
          </table>
        </div>
        <div class="footer">
          Internship Portal &bull; Admin Alert
        </div>
      </div>
    </body>
    </html>
    """

    _send_email_async(
        subject=subject,
        body_text=text_content,
        body_html=html_content,
        recipient_list=[admin_email]
    )


# ====================================================================
# 2. NOTIFICATIONS FOR STUDENTS
# ====================================================================

def send_student_welcome_email(user_data):
    """
    Sends a warm welcome email to a student when they sign up for an account.
    """
    student_name = user_data.get("name", "Student")
    student_email = user_data.get("email", "").strip()

    if not student_email or "@" not in student_email:
        return

    subject = f"🎉 Welcome to Internship Portal, {student_name}!"

    text_content = f"""
Welcome to Internship Portal, {student_name}!
==============================================

Dear {student_name},

Thank you for creating your student account with the Internship Portal.

Your Registered Email: {student_email}

Next Steps:
1. Browse through available internship programs (FYUGP, B.Tech, PG, etc.).
2. Select your specialized domain (AI Data Science, AIML, Full Stack, Cybersecurity, etc.).
3. Complete your registration to secure your internship slot.
4. Track your application status anytime using your registered email.

If you have any questions or require assistance, feel free to reach out to our team at contact.edulayne@gmail.com.

Best regards,
Internship Portal Team
contact.edulayne@gmail.com
"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ background: #ffffff; border-radius: 12px; max-width: 580px; margin: 0 auto; box-shadow: 0 4px 14px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; padding: 32px 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.95; font-size: 15px; }}
        .body {{ padding: 28px 24px; line-height: 1.6; }}
        .steps {{ background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px 20px; margin: 20px 0; }}
        .step-item {{ margin: 8px 0; font-size: 14px; color: #166534; }}
        .footer {{ background: #f8fafc; padding: 18px 24px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; }}
        .btn {{ display: inline-block; background: #059669; color: #ffffff !important; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>🎉 Welcome to Internship Portal!</h1>
          <p>Your student account is ready</p>
        </div>
        <div class="body">
          <p style="font-size: 16px; margin-top: 0;">Dear <strong>{student_name}</strong>,</p>
          <p>Thank you for signing up on the <strong>Internship Portal</strong>. Your account has been successfully created with <strong>{student_email}</strong>.</p>
          
          <div class="steps">
            <h3 style="margin: 0 0 10px 0; font-size: 15px; color: #14532d;">🚀 What you can do next:</h3>
            <div class="step-item">&bull; <strong>Explore Programs:</strong> Discover internship tracks tailored for FYUGP, B.Tech, and PG students.</div>
            <div class="step-item">&bull; <strong>Choose Your Domain:</strong> AI & Data Science, AIML, Full Stack Development, and Cybersecurity.</div>
            <div class="step-item">&bull; <strong>Submit Application:</strong> Register online with your academic details and track status anytime.</div>
          </div>

          <p style="font-size: 14px; color: #475569;">
            Have questions? Contact our admissions and support team at <a href="mailto:contact.edulayne@gmail.com" style="color: #059669; font-weight: 600;">contact.edulayne@gmail.com</a>.
          </p>
        </div>
        <div class="footer">
          &copy; Internship Portal &bull; <a href="mailto:contact.edulayne@gmail.com" style="color: #64748b; text-decoration: none;">contact.edulayne@gmail.com</a>
        </div>
      </div>
    </body>
    </html>
    """

    _send_email_async(
        subject=subject,
        body_text=text_content,
        body_html=html_content,
        recipient_list=[student_email]
    )


def send_student_application_confirmation_email(app_data):
    """
    Sends a detailed application receipt & confirmation email to the student upon internship registration.
    """
    student_name = app_data.get("student_name", "Student")
    student_email = app_data.get("email", "").strip()
    app_id = app_data.get("application_id", "N/A")
    program = app_data.get("program_title", app_data.get("program_code", "Internship Program"))
    domain = app_data.get("domain", "General Track")
    college = app_data.get("college_name", "Not specified")
    dept = app_data.get("department", "Not specified")
    duration = app_data.get("duration_months", "1 Month")
    month = app_data.get("internship_month", "Upcoming")
    hours = app_data.get("internship_hours", "120 Hours")

    if not student_email or "@" not in student_email:
        return

    subject = f"🎓 Internship Application Received: {program} ({app_id})"

    text_content = f"""
APPLICATION CONFIRMATION - INTERNSHIP PORTAL
===========================================

Dear {student_name},

Thank you for registering for the internship program! We have received your application successfully.

APPLICATION DETAILS:
-------------------
Application ID: {app_id}
Student Name:   {student_name}
Program:        {program}
Domain:         {domain}
Duration:       {duration}
Required Hours: {hours}
Batch / Month:  {month}
College:        {college}
Department:     {dept}

Status: Application Submitted & Under Review

WHAT HAPPENS NEXT?
------------------
1. Our admissions team is reviewing your application and credentials.
2. You can track your real-time application status anytime on the Student Portal using your Application ID ({app_id}) or your registered email ({student_email}).
3. Once approved, you will receive onboarding details and schedule.

If you have any questions, reach out to us at contact.edulayne@gmail.com.

Best regards,
Internship Portal Team
contact.edulayne@gmail.com
"""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ background: #ffffff; border-radius: 12px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 14px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; overflow: hidden; }}
        .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: #ffffff; padding: 28px 24px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; }}
        .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; }}
        .body {{ padding: 24px; }}
        .badge-box {{ text-align: center; margin: 16px 0 20px 0; }}
        .app-badge {{ display: inline-block; background: #eff6ff; color: #1d4ed8; padding: 8px 18px; border-radius: 8px; font-size: 16px; font-weight: 700; border: 1px dashed #93c5fd; letter-spacing: 0.5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
        td.label {{ font-weight: 600; color: #64748b; width: 35%; }}
        td.value {{ color: #0f172a; font-weight: 500; }}
        .info-box {{ background: #f8fafc; border-left: 4px solid #3b82f6; padding: 14px 16px; border-radius: 0 8px 8px 0; margin-top: 20px; font-size: 13.5px; color: #334155; line-height: 1.5; }}
        .footer {{ background: #f8fafc; padding: 16px 24px; text-align: center; font-size: 13px; color: #64748b; border-top: 1px solid #e2e8f0; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h1>🎓 Application Received!</h1>
          <p>Internship Registration Confirmation</p>
        </div>
        <div class="body">
          <p style="margin: 0; font-size: 15px;">Dear <strong>{student_name}</strong>,</p>
          <p style="margin: 8px 0 16px 0; font-size: 14px; color: #475569;">Thank you for registering for an internship program. Your application has been successfully submitted:</p>

          <div class="badge-box">
            <span style="font-size: 12px; color: #64748b; display: block; margin-bottom: 4px; text-transform: uppercase; font-weight: 600;">Your Application ID</span>
            <div class="app-badge">{app_id}</div>
          </div>

          <table>
            <tr><td class="label">Program</td><td class="value"><strong>{program}</strong></td></tr>
            <tr><td class="label">Domain Track</td><td class="value"><span style="color: #2563eb; font-weight: 600;">{domain}</span></td></tr>
            <tr><td class="label">Duration</td><td class="value">{duration}</td></tr>
            <tr><td class="label">Required Hours</td><td class="value"><span style="color: #2563eb; font-weight: 700;">{hours}</span></td></tr>
            <tr><td class="label">Batch</td><td class="value">{month}</td></tr>
            <tr><td class="label">College</td><td class="value">{college}</td></tr>
            <tr><td class="label">Department</td><td class="value">{dept}</td></tr>
            <tr><td class="label">Status</td><td class="value"><span style="color: #d97706; font-weight: 600;">Submitted / Under Review</span></td></tr>
          </table>

          <div class="info-box">
            <strong>What is next?</strong><br>
            Our team will review your application. You can log in to the Student Portal anytime using your Application ID <strong>({app_id})</strong> or registered email to check real-time approval status and updates.
          </div>

          <p style="font-size: 13px; color: #64748b; margin-top: 20px;">
            For any queries, please email us at <a href="mailto:contact.edulayne@gmail.com" style="color: #2563eb;">contact.edulayne@gmail.com</a> with your Application ID.
          </p>
        </div>
        <div class="footer">
          &copy; Internship Portal &bull; <a href="mailto:contact.edulayne@gmail.com" style="color: #64748b; text-decoration: none;">contact.edulayne@gmail.com</a>
        </div>
      </div>
    </body>
    </html>
    """

    _send_email_async(
        subject=subject,
        body_text=text_content,
        body_html=html_content,
        recipient_list=[student_email]
    )
