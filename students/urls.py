from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views as s


urlpatterns = [

    path("superadmin/login/",s.SuperAdminLoginView.as_view(),name="superadmin-login-api"),

    path("superadmin/verify-otp/",s.VerifySuperAdminOTPView.as_view(),name="superadmin-verify-otp-api"),

    path("courses/",s.CourseListCreateView.as_view(),name="course-list-create"),

    path("courses/<int:pk>/",s.CourseDetailView.as_view(),name="course-detail"),

    path("students/",s.StudentListCreateView.as_view(),name="student-list-create"),

    path("students/<int:pk>/",s.StudentDetailView.as_view(),name="student-detail"),

    path("resend-otp/", s.ResendSuperAdminOTPView.as_view(), name="superadmin-resend-otp"),
    path('logout/', s.LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   
    path("forgot-password/", s.SuperAdminForgotPasswordView.as_view(), name="superadmin-forgot-password"),
    path("reset-password/", s.SuperAdminResetPasswordView.as_view(), name="superadmin-reset-password"),
    path("change-password/", s.SuperAdminChangePasswordView.as_view(), name="superadmin-change-password"),
 
 
 
 
]