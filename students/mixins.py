from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
 
 
def custom200(message, data=None):
    return Response({
        "status": "Success",
        "status_code": 200,
        "message": message,
        "data": data if data is not None else {}
    }, status=status.HTTP_200_OK)
 
 
def custom201(message, data=None):
    return Response({
        "status": "Created",
        "status_code": 201,
        "message": message,
        "data": data if data is not None else {}
    }, status=status.HTTP_201_CREATED)
 
 
def custom204(message, data=None):
    return Response({
        "status": "No Content",
        "status_code": 204,
        "message": message,
        "data": data if data is not None else {}
    }, status=status.HTTP_204_NO_CONTENT)
 
 
def custom400(message, errors=None):
    return Response({
        "status": "Bad Request",
        "status_code": 400,
        "message": message,
        "errors": errors if errors is not None else {}
    }, status=status.HTTP_400_BAD_REQUEST)
 
 
def custom401(message, errors=None):
    return Response({
        "status": "Unauthorized",
        "status_code": 401,
        "message": message,
        "errors": errors if errors is not None else {}
    }, status=status.HTTP_401_UNAUTHORIZED)
 
 
def custom404(message, errors=None):
    return Response({
        "status": "Failed 'Not Found'",
        "status_code": 404,
        "message": message,
        "errors": errors if errors else {}
    }, status=status.HTTP_404_NOT_FOUND)
 
 
def custom500(message="Internal Server Error", errors=None):
    return Response({
        "status": "Server Error",
        "status_code": 500,
        "message": message,
        "errors": errors if errors is not None else {}
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)