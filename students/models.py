from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser, Group, Permission
from students.manager import UserManager

#CUSTOM 
class User(AbstractUser):
    ROLE_CHOICES = [
        ("SUPERADMIN", "SuperAdmin"),
        ("USER", "User")
    ]
 
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)
    full_name = models.CharField(max_length=255, null=True, blank=True)
 
    groups = models.ManyToManyField(Group, related_name="profile_set", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="profile_set", blank=True)
 
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # keep username required internally
 
    # hook up the custom manager
    objects = UserManager()
 
    
    def __str__(self):
        return f"{self.email} ({self.role})"



# =========================================================
# COURSE
# =========================================================

class Course(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    duration = models.CharField(
        max_length=50
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.name} - {self.duration}"


# =========================================================
# STUDENT
# =========================================================

class Student(models.Model):

    # Connect Student with User
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )

    name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True
    )

    age = models.PositiveIntegerField()

    phone = models.CharField(
        max_length=15
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="students"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


# =========================================================
# MARK
# =========================================================

class Mark(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="marks"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="marks"
    )

    mark = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.student.name} - {self.course.name} - {self.mark}"



 
 

class Product(models.Model):

 

    name = models.CharField(

        max_length=100

    )

 

    description = models.TextField(

        blank=True,

        null=True

    )

 

    is_active = models.BooleanField(

        default=True

    )

 

    created_at = models.DateTimeField(

        auto_now_add=True

    )

 

    updated_at = models.DateTimeField(

        auto_now=True

    )

 

    def __str__(self):

        return self.name
 
 