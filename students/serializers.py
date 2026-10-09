from rest_framework import serializers
from .models import Course, Student, User


class SuperAdminLoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={"input_type": "password"}
    )


class OTPVerifySerializer(serializers.Serializer):

    email = serializers.EmailField()
    otp = serializers.CharField(
        max_length=6,
        min_length=6
    )



class SuperAdminPasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
 
    def validate(self, attrs):
        user = self.context["request"].user
 
        # Verify old password
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError("Old password is incorrect.")
 
        # Check new == confirm
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("New password and confirm password do not match.")
 
        # Prevent same password reuse
        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError("New password cannot be the same as old password.")
 
        return attrs
 
    def save(self, **kwargs):
        user = self.context["request"].user
        new_password = self.validated_data["new_password"]
        user.set_password(new_password)
        user.save()
        return user
 
class CourseSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "description",
            "duration",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

# =========================================================
# STUDENT SERIALIZER
# =========================================================
class StudentSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=False,
        style={"input_type": "password"}
    )

    confirm_password = serializers.CharField(
        write_only=True,
        required=False,
        style={"input_type": "password"}
    )

    class Meta:
        model = Student

        fields = [
            "id",
            "name",
            "email",
            "password",
            "confirm_password",
            "age",
            "phone",
            "address",
            "course",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate(self, data):

        password = data.get("password")
        confirm_password = data.get("confirm_password")

        # During creation, both are required
        if self.instance is None:

            if not password:
                raise serializers.ValidationError({
                    "password": "Password is required."
                })

            if not confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": "Confirm password is required."
                })

            if password != confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": "Passwords do not match."
                })

        # confirm_password must also be supplied
        elif password or confirm_password:

            if password != confirm_password:
                raise serializers.ValidationError({
                    "confirm_password": "Passwords do not match."
                })

        return data

    def create(self, validated_data):

        password = validated_data.pop("password")
        validated_data.pop("confirm_password")

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=password,
            full_name=validated_data["name"],
            role="USER"
        )

        student = Student.objects.create(
            user=user,
            **validated_data
        )

        return student

    def update(self, instance, validated_data):

        password = validated_data.pop("password", None)
        validated_data.pop("confirm_password", None)

        # Update Student fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        # Update User password if supplied
        if password:
            instance.user.set_password(password)
            instance.user.save()

        return instance