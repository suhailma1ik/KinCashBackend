"""
Custom exception handlers for H.E.L.P Backend.

This module provides a custom exception handler that ensures all API responses
follow the standardized format defined in the API documentation with clear,
specific error messages that are easy to understand.
"""
from rest_framework import status
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework.exceptions import (
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    Throttled,
    APIException,
    MethodNotAllowed,
    ParseError,
)
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import IntegrityError
import traceback
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns responses in a standardized format
    with clear, specific error messages.
    
    Format:
    {
        "status": "error",
        "message": <specific_error_message>,
        "errors": <detailed_errors> (optional)
    }
    """
    # Get request details for better context
    request = context.get('request')
    view = context.get('view')
    view_name = view.__class__.__name__ if view else 'Unknown'
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle specific exceptions that DRF doesn't catch
    if response is None:
        if isinstance(exc, Http404):
            resource_name = getattr(view, 'basename', 'Resource') if view else 'Resource'
            message = f"{resource_name} not found"
            data = {
                "status": "error",
                "message": message
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)
        
        elif isinstance(exc, DjangoPermissionDenied):
            data = {
                "status": "error",
                "message": "You don't have permission to perform this action"
            }
            return Response(data, status=status.HTTP_403_FORBIDDEN)
            
        elif isinstance(exc, IntegrityError):
            # Extract useful information from database integrity errors
            error_msg = str(exc)
            if 'unique constraint' in error_msg.lower():
                message = "This record already exists"
                if 'Key (email)' in error_msg:
                    message = "A user with this email already exists"
                elif 'Key (phone)' in error_msg:
                    message = "A user with this phone number already exists"
            else:
                message = "Database integrity error"
                
            data = {
                "status": "error",
                "message": message
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
        # For unexpected errors, log the exception and return a 500 response
        logger.error(f"Unhandled exception in {view_name}: {str(exc)}\n{traceback.format_exc()}")
        data = {
            "status": "error",
            "message": "Something went wrong on our end. Our team has been notified."
        }
        return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Get the status code and initialize the response data
    status_code = response.status_code
    
    # Format the response data
    data = {
        "status": "error",
        "message": get_error_message(exc, status_code, context)
    }
    
    # Handle validation errors with more specific details
    if isinstance(exc, ValidationError):
        errors = {}
        # Format validation errors to be more readable
        for field, error_details in response.data.items():
            if isinstance(error_details, list):
                # Join multiple error messages for the same field
                errors[field] = error_details[0] if len(error_details) == 1 else error_details
            else:
                errors[field] = error_details
        
        data["errors"] = errors
        
        # If there's only one field with an error, make the main message more specific
        if len(errors) == 1:
            field = list(errors.keys())[0]
            error_value = errors[field]
            if isinstance(error_value, str):
                data["message"] = f"Invalid {field}: {error_value}"
    
    # Replace the response data with our custom format
    response.data = data
    
    return response


def get_error_message(exc, status_code, context=None):
    """
    Get a specific and user-friendly error message based on the exception type and status code.
    
    Args:
        exc: The exception that was raised
        status_code: The HTTP status code
        context: The exception handler context (contains request and view)
    
    Returns:
        A clear, specific error message
    """
    # Extract useful context when available
    view = context.get('view') if context else None
    request = context.get('request') if context else None
    method = request.method if request else 'Unknown'
    
    # Get resource name from view if available
    resource_name = None
    if view:
        if hasattr(view, 'get_queryset') and callable(view.get_queryset):
            try:
                model = view.get_queryset().model
                resource_name = model._meta.verbose_name.title()
            except:
                pass
        
        if not resource_name and hasattr(view, 'basename'):
            resource_name = view.basename.replace('_', ' ').title()
    
    resource_name = resource_name or 'Resource'
    
    # Handle specific exception types with clear messages
    if isinstance(exc, ValidationError):
        # Look for common validation patterns and provide better messages
        if hasattr(exc, 'detail'):
            detail = exc.detail
            if isinstance(detail, dict) and len(detail) == 1:
                field = list(detail.keys())[0]
                if field == 'non_field_errors' and isinstance(detail[field], list):
                    return detail[field][0]
                elif isinstance(detail[field], list) and len(detail[field]) > 0:
                    return f"Invalid {field.replace('_', ' ')}: {detail[field][0]}"
        return "Please check your input and try again"
        
    elif isinstance(exc, AuthenticationFailed):
        if hasattr(exc, 'detail'):
            return str(exc.detail)
        return "Invalid credentials"
        
    elif isinstance(exc, NotAuthenticated):
        return "You must be logged in to perform this action"
        
    elif isinstance(exc, PermissionDenied):
        return "You don't have permission to perform this action"
        
    elif isinstance(exc, NotFound):
        return f"{resource_name} not found"
        
    elif isinstance(exc, MethodNotAllowed):
        allowed_methods = ', '.join(getattr(exc, 'available_actions', []))
        if allowed_methods:
            return f"{method} not allowed. Allowed methods: {allowed_methods}"
        return f"{method} method is not supported for this endpoint"
        
    elif isinstance(exc, Throttled):
        wait_time = getattr(exc, 'wait', None)
        if wait_time:
            return f"Too many requests. Please try again in {wait_time} seconds"
        return "Too many requests. Please try again later"
        
    elif isinstance(exc, ParseError):
        return "Invalid request format. Please check your request data"
        
    # Handle based on status codes for other exceptions
    elif status_code == status.HTTP_400_BAD_REQUEST:
        return "Invalid request data. Please check your input"
        
    elif status_code == status.HTTP_401_UNAUTHORIZED:
        return "Authentication credentials are invalid or expired"
        
    elif status_code == status.HTTP_403_FORBIDDEN:
        return "You don't have permission to perform this action"
        
    elif status_code == status.HTTP_404_NOT_FOUND:
        return f"{resource_name} not found"
        
    elif status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return f"{method} method is not supported for this endpoint"
        
    elif status_code == status.HTTP_406_NOT_ACCEPTABLE:
        return "The requested content type is not acceptable"
        
    elif status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE:
        return "Unsupported media type. Please check your Content-Type header"
        
    elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return "Too many requests. Please try again later"
        
    elif 400 <= status_code < 500:
        return "There was a problem with your request"
        
    else:
        return "Something went wrong on our end. Our team has been notified"
