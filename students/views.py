from django.shortcuts import render
from django.core.cache import cache
from django.utils import timezone as dj_timezone
from django.contrib.auth import authenticate

from django.core.mail import send_mail
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import request, status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework_simplejwt.authentication import JWTAuthentication

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.utils import timezone as dj_timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

from datetime import timedelta
from students.mixins import custom200, custom201, custom400, custom401, custom404
from students.permissions import IsSuperAdmin
from students.tasks import send_otp_email
 

from .models import User, Course, Student

from .serializers import (
    SuperAdminLoginSerializer,
    OTPVerifySerializer,
    CourseSerializer,
    StudentSerializer,
    SuperAdminPasswordChangeSerializer,
)

# =========================================================
# IMPORT OTP FUNCTIONS FROM utils.py
# =========================================================

from .utils import (
    flatten_errors,
    generate_otp,
    send_password_reset,
    store_otp,
    try_except_wrapper,
    verify_otp,
)



# =========================================================
# SUPERADMIN LOGIN API
# =========================================================

class SuperAdminLoginView(APIView):

    authentication_classes = []

    permission_classes = [AllowAny]

    MAX_ATTEMPTS = 3

    BLOCK_TIME_MINUTES = 5

    def post(self, request):

        # ----------------------------------
        # VALIDATE INPUT
        # ----------------------------------

        serializer = SuperAdminLoginSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return custom400(
                "Invalid input",
                serializer.errors
            )

        email = serializer.validated_data["email"]

        password = serializer.validated_data["password"]

        # ----------------------------------
        # GET IP ADDRESS
        # ----------------------------------

        ip_address = request.META.get(
            "REMOTE_ADDR",
            "unknown"
        )

        now = dj_timezone.now()

        # ----------------------------------
        # ATTEMPT CACHE KEY
        # ----------------------------------

        attempts_key = (
            f"superadmin_login_attempts:"
            f"{ip_address}:"
            f"{email.lower()}"
        )

        attempts_data = cache.get(
            attempts_key
        )

        # ----------------------------------
        # CHECK BLOCK STATUS
        # ----------------------------------

        if attempts_data:

            attempts, last_attempt = attempts_data

            if attempts >= self.MAX_ATTEMPTS:

                time_diff = (
                    now - last_attempt
                )

                if time_diff < timedelta(
                    minutes=self.BLOCK_TIME_MINUTES
                ):

                    remaining = (
                        timedelta(
                            minutes=self.BLOCK_TIME_MINUTES
                        ) - time_diff
                    ).seconds

                    minutes, seconds = divmod(
                        remaining,
                        60
                    )

                    return custom400(
                        f"Too many failed attempts. "
                        f"Try again after "
                        f"{minutes} minute(s) "
                        f"{seconds} second(s)."
                    )

                # Block time finished

                cache.delete(
                    attempts_key
                )

                attempts_data = None

        # ----------------------------------
        # FIND USER
        # ----------------------------------

        try:

            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            return custom404(
                "Email is not registered"
            )

        # ----------------------------------
        # ROLE VALIDATION
        # ----------------------------------

        if user.role != "SUPERADMIN":

            attempts = (
                attempts_data[0] + 1
                if attempts_data
                else 1
            )

            cache.set(
                attempts_key,
                (attempts, now),
                timeout=self.BLOCK_TIME_MINUTES * 60
            )

            remaining_attempts = max(
                0,
                self.MAX_ATTEMPTS - attempts
            )

            return custom400(
                f"Only SuperAdmins can login here. "
                f"{remaining_attempts} attempt(s) left."
            )

        # ----------------------------------
        # AUTHENTICATE PASSWORD
        # ----------------------------------

        authenticated_user = authenticate(
            request,
            username=user.email,
            password=password
        )

        if authenticated_user is None:

            attempts = (
                attempts_data[0] + 1
                if attempts_data
                else 1
            )

            cache.set(
                attempts_key,
                (attempts, now),
                timeout=self.BLOCK_TIME_MINUTES * 60
            )

            remaining_attempts = max(
                0,
                self.MAX_ATTEMPTS - attempts
            )

            return custom401(
                f"Invalid credentials. "
                f"{remaining_attempts} attempt(s) left."
            )

        # ----------------------------------
        # SUCCESSFUL PASSWORD LOGIN
        # ----------------------------------

        cache.delete(
            attempts_key
        )

        # ----------------------------------
        # GENERATE OTP
        # ----------------------------------

        otp = generate_otp()

        # ----------------------------------
        # STORE OTP
        # OTP VALID FOR 5 MINUTES
        # ----------------------------------

        store_otp(
            user.email,
            otp
        )

        # ----------------------------------
        # SEND OTP EMAIL
        # ----------------------------------

        send_otp_email.delay(
            email,
            otp
        )

        # ----------------------------------
        # SUCCESS RESPONSE
        # ----------------------------------

        return custom200(
            "A new OTP has been sent to your email."
        )
# =========================================================
# SUPERADMIN OTP VERIFICATION API
# =========================================================

class VerifySuperAdminOTPView(APIView):

    authentication_classes = []

    permission_classes = [AllowAny]

    def post(self, request):

        # ----------------------------------
        # VALIDATE INPUT
        # ----------------------------------

        serializer = OTPVerifySerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return custom400(
                "Invalid input",
                serializer.errors
            )

        email = serializer.validated_data[
            "email"
        ]

        otp = serializer.validated_data[
            "otp"
        ]

        # ----------------------------------
        # VERIFY OTP
        # ----------------------------------

        if not verify_otp(
            email,
            otp
        ):

            return custom400(
                "Invalid or expired OTP"
            )

        # ----------------------------------
        # FIND SUPERADMIN
        # ----------------------------------

        user = User.objects.filter(
            email=email,
            role="SUPERADMIN"
        ).first()

        if not user:

            return custom404(
                "SuperAdmin account not found"
            )

        # ----------------------------------
        # CREATE JWT TOKENS
        # ----------------------------------

        refresh = RefreshToken.for_user(
            user
        )

        data = {

            "access": str(
                refresh.access_token
            ),

            "refresh": str(
                refresh
            ),

            "user": {

                "id": str(
                    user.id
                ),

                "email":
                user.email,

                "username":
                user.username,

                "full_name":
                user.full_name,

                "role":
                user.role,
            }
        }

        # ----------------------------------
        # SUCCESS RESPONSE
        # ----------------------------------

        return custom200(
            "Login successful",
            data
        )



class ResendSuperAdminOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
 
    def post(self, request):
        email = request.data.get("email")
 
        if not email:
            return custom400("Email is required")
 
        # Ensure the user exists and is a SuperAdmin
        user = User.objects.filter(email=email, is_superuser=True).first()
        if not user:
            return custom400("SuperAdmin account not found")
 
        # Generate & store new OTP (overrides previous one in Redis)
        otp = generate_otp()
        store_otp(email, otp, ttl=300)  # 5 minutes expiry
 
        # Send OTP via Celery
        send_otp_email.delay(email, otp)
 
        return custom200("A new OTP has been sent to your email.")
   
class SuperAdminForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
 
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return custom400("Email is required")
 
        user = User.objects.filter(email=email, is_superuser=True).first()
        if not user:
            return custom404("SuperAdmin with this email not found")
 
        # Generate token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
 
        # Pick a frontend base URL safely
        frontend_url = "https://pos-restaurant.neurox.co.in"
        if not frontend_url:
            origins = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
            frontend_url = origins[0] if origins else "http://localhost:3000"
 
        reset_link = f"{frontend_url}/superadmin/reset-password/{uid}/{token}/"
 
        try:
            send_password_reset(email, reset_link)
        except Exception as e:
            return custom400(f"Error sending password reset email: {str(e)}")
 
        return custom200("Password reset link has been sent to your email.")
 
 
class SuperAdminResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
 
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
 
        if not uidb64 or not token or not new_password:
            return custom400("uid, token, and new_password are required")
 
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid, is_superuser=True)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return custom404("Invalid reset link")
 
        if not default_token_generator.check_token(user, token):
            return custom400("Link expired")
 
        user.set_password(new_password)
        user.save()
 
        return custom200("Password has been reset successfully.")
   
 
class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = []
 
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token is None:
            return custom400("Refresh token required.")
 
        token = RefreshToken(refresh_token)
        token.blacklist()
 
        return custom200("Logged out successfully.")
    

class SuperAdminChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdmin]
 
    @try_except_wrapper
    def post(self, request):
        serializer = SuperAdminPasswordChangeSerializer(
            data=request.data,
            context={"request": request}
        )
 
        if serializer.is_valid():
            serializer.save()
            return custom200("Password changed successfully")
 
        # Convert errors to your single string
        return custom400("Validation Error", flatten_errors(serializer.errors))
 
   
 


# =========================================================
# COURSE LIST + CREATE API
# =========================================================

class CourseListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdmin]



    # ----------------------------------
    # GET - LIST ALL COURSES
    # ----------------------------------

    def get(self, request):

        courses = Course.objects.all().order_by(
            "created_at"
        )

        serializer = CourseSerializer(
            courses,
            many=True
        )

        return custom200(
            "Courses list fetched successfully",
            serializer.data
        )

    # ----------------------------------
    # POST - CREATE COURSE
    # ----------------------------------

    def post(self, request):

        serializer = CourseSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return custom201(
                "Course created successfully",
                serializer.data
            )

        return custom400(
            "Validation Error",
            serializer.errors
        )


# =========================================================
# COURSE DETAIL API
# =========================================================

class CourseDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdmin]
    

    # ----------------------------------
    # GET COURSE OBJECT
    # ----------------------------------

    def get_object(self, pk):

        try:

            return Course.objects.get(
                pk=pk
            )

        except Course.DoesNotExist:

            return None

    # ----------------------------------
    # GET - SINGLE COURSE
    # ----------------------------------

    def get(self, request, pk):

        course = self.get_object(pk)

        if course is None:

            return custom404(
                "Course not found"
            )

        serializer = CourseSerializer(
            course
        )

        return custom200(
            "Course details fetched successfully",
            serializer.data
        )

    # ----------------------------------
    # PUT - UPDATE COMPLETE COURSE
    # ----------------------------------

    def put(self, request, pk):

        course = self.get_object(pk)

        if course is None:

            return custom404(
                "Course not found"
            )

        serializer = CourseSerializer(
            course,
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return custom200(
                "Course updated successfully",
                serializer.data
            )

        return custom400(
            "Validation Error",
            serializer.errors
        )

    # ----------------------------------
    # PATCH - PARTIAL UPDATE
    # ----------------------------------

    def patch(self, request, pk):

        course = self.get_object(pk)

        if course is None:

            return custom404(
                "Course not found"
            )

        serializer = CourseSerializer(
            course,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return custom200(
                "Course updated successfully",
                serializer.data
            )

        return custom400(
            "Validation Error",
            serializer.errors
        )

    # ----------------------------------
    # DELETE - DELETE COURSE
    # ----------------------------------

    def delete(self, request, pk):

        course = self.get_object(pk)

        if course is None:

            return custom404(
                "Course not found"
            )

        course.delete()

        return custom200(
            "Course deleted successfully"
        )


# =========================================================
# STUDENT PAGINATION
# =========================================================

class StudentPagination(PageNumberPagination):

    page_size = 10

    page_size_query_param = "page_size"

    max_page_size = 100


# =========================================================
# STUDENT LIST + CREATE
# =========================================================

class StudentListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdmin]


    # =====================================================
    # GET - List Students
    # =====================================================

    def get(self, request):

        students = Student.objects.select_related(
            "course"
        ).all()

        # -------------------------------------------------
        # Filter by Student ID
        # -------------------------------------------------

        student_id = request.GET.get("student_id")

        if student_id:

            students = students.filter(
                id=student_id
            )

        # -------------------------------------------------
        # Search by Student Name (with search_type)
        # -------------------------------------------------

        search_query = request.GET.get("search")
        search_type = request.GET.get(
            "search_type",
            "icontains"
        )

        if search_query:

            allowed_search_types = [
                "exact",
                "iexact",
                "contains",
                "icontains",
                "startswith",
                "istartswith",
                "endswith",
                "iendswith",
            ]

            if search_type not in allowed_search_types:

                return custom400(
                    "Invalid search_type"
                )

            lookup = f"name__{search_type}"

            students = students.filter(
                **{
                    lookup: search_query
                }
            ).order_by(
                "name"
            )

        else:

            # -------------------------------------------------
            # Sorting
            # -------------------------------------------------

            sort = request.GET.get(
                "sort",
                "created_at"
            )

            allowed_sort_fields = [
                "name",
                "-name",
                "age",
                "-age",
                "created_at",
                "-created_at",
                "updated_at",
                "-updated_at",
            ]

            if sort not in allowed_sort_fields:

                sort = "created_at"

            students = students.order_by(
                sort
            )

        # -------------------------------------------------
        # Pagination
        # -------------------------------------------------

        paginator = StudentPagination()

        paginated_students = paginator.paginate_queryset(
            students,
            request
        )

        serializer = StudentSerializer(
            paginated_students,
            many=True
        )

        paginator_data= paginator.get_paginated_response(
            serializer.data
        ).data
        return custom200(
            "students list fetched successfully",paginator_data
        )
    

    # =====================================================
    # POST - Create Student
    # =====================================================

    def post(self, request):

        serializer = StudentSerializer(
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return custom201(
                "Student created successfully",
                serializer.data
            )

        return custom400(
            "Validation Error",
            serializer.errors
        )


# =========================================================
# STUDENT DETAIL
# =========================================================

class StudentDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdmin]


    # =====================================================
    # Get Student Object
    # =====================================================

    def get_object(self, pk):

        try:

            return Student.objects.select_related(
                "course",
                "user"
            ).get(
                pk=pk
            )

        except Student.DoesNotExist:

            return None

    # =====================================================
    # GET - Single Student
    # =====================================================

    def get(self, request, pk):

        student = self.get_object(pk)

        if student is None:

            return custom404(
                "Student not found"
            )

        serializer = StudentSerializer(
            student
        )

        return custom200(
            "Student details fetched successfully",
            serializer.data
        )

    # =====================================================
    # PUT - Update Entire Student
    # =====================================================

    def put(self, request, pk):

        student = self.get_object(pk)

        if student is None:

            return custom404(
                "Student not found"
            )

        serializer = StudentSerializer(
            student,
            data=request.data
        )

        if serializer.is_valid():

            serializer.save()

            return custom200(
                "Student updated successfully",
                serializer.data
            )

        return custom400(
            "Validation Error",
            serializer.errors
        )

    # =====================================================
    # PATCH - Partial Update
    # =====================================================

    def patch(self, request, pk):

        student = self.get_object(pk)

        if student is None:

            return custom404(
                "Student not found"
            )

        serializer = StudentSerializer(
            student,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return custom200(
                "Student updated successfully",
                serializer.data
            )

        return custom400(
            "Validation Error",
            serializer.errors
        )

    # =====================================================
    # DELETE - Delete Student
    # =====================================================

    def delete(self, request, pk):

        student = self.get_object(pk)

        if student is None:

            return custom404(
                "Student not found"
            )

        student.delete()

        return custom200(
            "Student deleted successfully"
        )