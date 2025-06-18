# user_service/app/validation/user_validators.py
"""
User-specific validation utilities following shared_architecture patterns.
Based on shared_architecture.validation.trade_validators design.
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from shared_architecture.validation.trade_validators import ValidationResult, ValidationSeverity
from shared_architecture.enums import UserRole, AccountStatus
from shared_architecture.exceptions.trade_exceptions import ValidationException, ErrorContext

class UserValidator:
    """Comprehensive validation for user-related data"""
    
    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+\d{10,15}$')
    NAME_PATTERN = re.compile(r'^[a-zA-Z\s]{1,50}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,30}$')
    
    # Limits
    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 50
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 30
    
    @staticmethod
    def validate_email(email: str, context: ErrorContext = None) -> ValidationResult:
        """Validate email format"""
        if not email:
            return ValidationResult(
                is_valid=False,
                field_name="email",
                message="Email is required",
                severity=ValidationSeverity.ERROR
            )
        
        if not isinstance(email, str):
            return ValidationResult(
                is_valid=False,
                field_name="email",
                message=f"Email must be a string, got {type(email).__name__}",
                severity=ValidationSeverity.ERROR
            )
        
        if not UserValidator.EMAIL_PATTERN.match(email):
            return ValidationResult(
                is_valid=False,
                field_name="email",
                message=f"Invalid email format: {email}",
                severity=ValidationSeverity.ERROR,
                suggested_value=email.lower().strip() if '@' in email else None
            )
        
        return ValidationResult(
            is_valid=True,
            field_name="email",
            message="Valid email format"
        )
    
    @staticmethod
    def validate_phone_number(phone: str, context: ErrorContext = None) -> ValidationResult:
        """Validate phone number format"""
        if not phone:
            return ValidationResult(
                is_valid=False,
                field_name="phone_number",
                message="Phone number is required",
                severity=ValidationSeverity.ERROR
            )
        
        if not isinstance(phone, str):
            return ValidationResult(
                is_valid=False,
                field_name="phone_number",
                message=f"Phone number must be a string, got {type(phone).__name__}",
                severity=ValidationSeverity.ERROR
            )
        
        if not UserValidator.PHONE_PATTERN.match(phone):
            return ValidationResult(
                is_valid=False,
                field_name="phone_number",
                message=f"Invalid phone number format: {phone}. Must start with + and contain 10-15 digits",
                severity=ValidationSeverity.ERROR,
                suggested_value=f"+{phone}" if phone.isdigit() and len(phone) >= 10 else None
            )
        
        return ValidationResult(
            is_valid=True,
            field_name="phone_number",
            message="Valid phone number format"
        )
    
    @staticmethod
    def validate_name(name: str, field_name: str = "name", context: ErrorContext = None) -> ValidationResult:
        """Validate name fields (first_name, last_name)"""
        if not name:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                message=f"{field_name} is required",
                severity=ValidationSeverity.ERROR
            )
        
        if not isinstance(name, str):
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                message=f"{field_name} must be a string, got {type(name).__name__}",
                severity=ValidationSeverity.ERROR
            )
        
        name = name.strip()
        
        if len(name) < UserValidator.MIN_NAME_LENGTH:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                message=f"{field_name} must be at least {UserValidator.MIN_NAME_LENGTH} character(s)",
                severity=ValidationSeverity.ERROR
            )
        
        if len(name) > UserValidator.MAX_NAME_LENGTH:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                message=f"{field_name} cannot exceed {UserValidator.MAX_NAME_LENGTH} characters",
                severity=ValidationSeverity.ERROR,
                suggested_value=name[:UserValidator.MAX_NAME_LENGTH]
            )
        
        if not UserValidator.NAME_PATTERN.match(name):
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                message=f"Invalid {field_name} format: {name}. Only letters and spaces allowed",
                severity=ValidationSeverity.ERROR,
                suggested_value=re.sub(r'[^a-zA-Z\s]', '', name) if name else None
            )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            message=f"Valid {field_name} format"
        )
    
    @staticmethod
    def validate_user_role(role: str, context: ErrorContext = None) -> ValidationResult:
        """Validate user role"""
        if not role:
            return ValidationResult(
                is_valid=False,
                field_name="role",
                message="User role is required",
                severity=ValidationSeverity.ERROR
            )
        
        if not isinstance(role, str):
            return ValidationResult(
                is_valid=False,
                field_name="role",
                message=f"User role must be a string, got {type(role).__name__}",
                severity=ValidationSeverity.ERROR
            )
        
        try:
            UserRole(role.upper())
        except ValueError:
            return ValidationResult(
                is_valid=False,
                field_name="role",
                message=f"Invalid user role: {role}. Valid roles: {[r.value for r in UserRole]}",
                severity=ValidationSeverity.ERROR,
                suggested_value=role.upper() if role.upper() in [r.value for r in UserRole] else None
            )
        
        return ValidationResult(
            is_valid=True,
            field_name="role",
            message="Valid user role"
        )
    
    @staticmethod
    def validate_account_status(status: str, context: ErrorContext = None) -> ValidationResult:
        """Validate account status"""
        if not status:
            return ValidationResult(
                is_valid=False,
                field_name="status",
                message="Account status is required",
                severity=ValidationSeverity.ERROR
            )
        
        if not isinstance(status, str):
            return ValidationResult(
                is_valid=False,
                field_name="status",
                message=f"Account status must be a string, got {type(status).__name__}",
                severity=ValidationSeverity.ERROR
            )
        
        try:
            AccountStatus(status.lower())
        except ValueError:
            return ValidationResult(
                is_valid=False,
                field_name="status",
                message=f"Invalid account status: {status}. Valid statuses: {[s.value for s in AccountStatus]}",
                severity=ValidationSeverity.ERROR,
                suggested_value=status.lower() if status.lower() in [s.value for s in AccountStatus] else None
            )
        
        return ValidationResult(
            is_valid=True,
            field_name="status",
            message="Valid account status"
        )
    
    @staticmethod
    def validate_username(username: str, context: ErrorContext = None) -> ValidationResult:
        """Validate username format"""
        if not username:
            return ValidationResult(
                is_valid=False,
                field_name="username",
                message="Username is required",
                severity=ValidationSeverity.ERROR
            )
        
        if not isinstance(username, str):
            return ValidationResult(
                is_valid=False,
                field_name="username",
                message=f"Username must be a string, got {type(username).__name__}",
                severity=ValidationSeverity.ERROR
            )
        
        if len(username) < UserValidator.MIN_USERNAME_LENGTH:
            return ValidationResult(
                is_valid=False,
                field_name="username",
                message=f"Username must be at least {UserValidator.MIN_USERNAME_LENGTH} characters",
                severity=ValidationSeverity.ERROR
            )
        
        if len(username) > UserValidator.MAX_USERNAME_LENGTH:
            return ValidationResult(
                is_valid=False,
                field_name="username",
                message=f"Username cannot exceed {UserValidator.MAX_USERNAME_LENGTH} characters",
                severity=ValidationSeverity.ERROR,
                suggested_value=username[:UserValidator.MAX_USERNAME_LENGTH]
            )
        
        if not UserValidator.USERNAME_PATTERN.match(username):
            return ValidationResult(
                is_valid=False,
                field_name="username",
                message=f"Invalid username format: {username}. Only letters, numbers, underscore, and hyphen allowed",
                severity=ValidationSeverity.ERROR
            )
        
        return ValidationResult(
            is_valid=True,
            field_name="username",
            message="Valid username format"
        )

class UserRegistrationValidator:
    """Specialized validator for user registration data"""
    
    @staticmethod
    def validate_complete_user(user_data: Dict[str, Any], context: ErrorContext = None) -> List[ValidationResult]:
        """Validate complete user registration data"""
        results = []
        
        # Required fields validation
        required_fields = ['first_name', 'last_name', 'email']
        
        for field in required_fields:
            if field not in user_data or user_data[field] is None:
                results.append(ValidationResult(
                    is_valid=False,
                    field_name=field,
                    message=f"Required field '{field}' is missing",
                    severity=ValidationSeverity.ERROR
                ))
        
        # Individual field validation
        if 'first_name' in user_data:
            results.append(UserValidator.validate_name(user_data['first_name'], 'first_name', context))
        
        if 'last_name' in user_data:
            results.append(UserValidator.validate_name(user_data['last_name'], 'last_name', context))
        
        if 'email' in user_data:
            results.append(UserValidator.validate_email(user_data['email'], context))
        
        if 'phone_number' in user_data and user_data['phone_number']:
            results.append(UserValidator.validate_phone_number(user_data['phone_number'], context))
        
        if 'role' in user_data and user_data['role']:
            results.append(UserValidator.validate_user_role(user_data['role'], context))
        
        if 'username' in user_data and user_data['username']:
            results.append(UserValidator.validate_username(user_data['username'], context))
        
        return results
    
    @staticmethod
    def validate_user_update(update_data: Dict[str, Any], context: ErrorContext = None) -> List[ValidationResult]:
        """Validate user update data"""
        results = []
        
        # No fields provided
        if not any(v is not None for v in update_data.values()):
            results.append(ValidationResult(
                is_valid=False,
                field_name="update_data",
                message="No fields provided for update",
                severity=ValidationSeverity.ERROR
            ))
            return results
        
        # Validate individual fields if present
        if 'first_name' in update_data and update_data['first_name'] is not None:
            results.append(UserValidator.validate_name(update_data['first_name'], 'first_name', context))
        
        if 'last_name' in update_data and update_data['last_name'] is not None:
            results.append(UserValidator.validate_name(update_data['last_name'], 'last_name', context))
        
        if 'email' in update_data and update_data['email'] is not None:
            results.append(UserValidator.validate_email(update_data['email'], context))
        
        if 'phone_number' in update_data and update_data['phone_number'] is not None:
            results.append(UserValidator.validate_phone_number(update_data['phone_number'], context))
        
        if 'role' in update_data and update_data['role'] is not None:
            results.append(UserValidator.validate_user_role(update_data['role'], context))
        
        return results

def validate_and_raise_user_errors(validation_results: List[ValidationResult], context: ErrorContext = None):
    """Check validation results and raise ValidationException if any errors found"""
    errors = [r for r in validation_results if not r.is_valid and r.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]]
    
    if errors:
        error_messages = [f"{r.field_name}: {r.message}" for r in errors]
        raise ValidationException(
            message=f"User validation failed: {'; '.join(error_messages)}",
            context=context,
            field_name=errors[0].field_name if len(errors) == 1 else None
        )

def validate_user_with_warnings(validation_results: List[ValidationResult]) -> Dict[str, List[str]]:
    """Return user validation summary with errors and warnings"""
    return {
        "errors": [f"{r.field_name}: {r.message}" for r in validation_results 
                  if not r.is_valid and r.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]],
        "warnings": [f"{r.field_name}: {r.message}" for r in validation_results 
                    if not r.is_valid and r.severity == ValidationSeverity.WARNING],
        "suggestions": {r.field_name: r.suggested_value for r in validation_results 
                       if r.suggested_value is not None}
    }