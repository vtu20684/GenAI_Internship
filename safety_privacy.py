"""
Payroll AI Copilot - Safety & Privacy Strategy
Data redaction, PII protection, and privacy enforcement
"""

import re
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

class DataSensitivityLevel(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

@dataclass
class PIIPattern:
    name: str
    pattern: str
    replacement: str
    sensitivity: DataSensitivityLevel

class SafetyPrivacyManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # PII Detection Patterns
        self.pii_patterns = [
            # Social Security Numbers
            PIIPattern(
                name="ssn_full",
                pattern=r'\b\d{3}-\d{2}-\d{4}\b',
                replacement='XXX-XX-XXXX',
                sensitivity=DataSensitivityLevel.RESTRICTED
            ),
            PIIPattern(
                name="ssn_nodash",
                pattern=r'\b\d{9}\b',
                replacement='XXXXXXXXX',
                sensitivity=DataSensitivityLevel.RESTRICTED
            ),
            
            # Bank Account Numbers
            PIIPattern(
                name="bank_account",
                pattern=r'\b\d{10,17}\b',
                replacement='XXXXXXXXXXXXXXX',
                sensitivity=DataSensitivityLevel.RESTRICTED
            ),
            
            # Credit Card Numbers
            PIIPattern(
                name="credit_card",
                pattern=r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
                replacement='XXXX-XXXX-XXXX-XXXX',
                sensitivity=DataSensitivityLevel.RESTRICTED
            ),
            
            # Email Addresses (partial masking)
            PIIPattern(
                name="email",
                pattern=r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                replacement='[REDACTED_EMAIL]',
                sensitivity=DataSensitivityLevel.CONFIDENTIAL
            ),
            
            # Phone Numbers
            PIIPattern(
                name="phone_us",
                pattern=r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',
                replacement='(XXX) XXX-XXXX',
                sensitivity=DataSensitivityLevel.CONFIDENTIAL
            ),
            
            # Addresses
            PIIPattern(
                name="street_address",
                pattern=r'\b\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Boulevard|Blvd|Drive|Dr|Lane|Ln|Road|Rd|Court|Ct|Way|Place|Pl)\b',
                replacement='[REDACTED_ADDRESS]',
                sensitivity=DataSensitivityLevel.CONFIDENTIAL
            ),
            
            # Tax IDs (EIN)
            PIIPattern(
                name="ein",
                pattern=r'\b\d{2}-\d{7}\b',
                replacement='XX-XXXXXXX',
                sensitivity=DataSensitivityLevel.RESTRICTED
            ),
            
            # Driver's License Numbers
            PIIPattern(
                name="drivers_license",
                pattern=r'\b[A-Za-z]{1,2}\d{6,8}\b',
                replacement='XXXXXXX',
                sensitivity=DataSensitivityLevel.RESTRICTED
            ),
            
            # Passport Numbers
            PIIPattern(
                name="passport",
                pattern=r'\b[A-Za-z]{1,2}\d{7,9}\b',
                replacement='XXXXXXXXX',
                sensitivity=DataSensitivityLevel.RESTRICTED
            )
        ]
        
        # Sensitive keywords that trigger privacy alerts
        self.sensitive_keywords = [
            "password", "ssn", "social security", "bank account", "credit card",
            "routing number", "tax id", "ein", "driver license", "passport",
            "salary", "compensation", "wage", "pay rate", "bonus amount"
        ]
        
        # Forbidden content patterns
        self.forbidden_patterns = [
            r"hack\s+payroll",
            r"steal\s+employee\s+data",
            r"access\s+unauthorized",
            r"bypass\s+security",
            r"exploit\s+system"
        ]
    
    def redact_pii(self, text: str, user_role: str = "employee") -> Tuple[str, List[Dict]]:
        """
        Redact PII from text based on user role and sensitivity level
        
        Returns:
            Tuple of (redacted_text, redaction_log)
        """
        redacted_text = text
        redaction_log = []
        
        # Determine what level of redaction to apply based on role
        if user_role == "employee":
            max_sensitivity = DataSensitivityLevel.CONFIDENTIAL
        elif user_role in ["hr", "finance"]:
            max_sensitivity = DataSensitivityLevel.RESTRICTED
        else:
            max_sensitivity = DataSensitivityLevel.INTERNAL
        
        for pii_pattern in self.pii_patterns:
            if self._should_redact(pii_pattern.sensitivity, max_sensitivity):
                matches = re.finditer(pii_pattern.pattern, redacted_text, re.IGNORECASE)
                for match in matches:
                    redaction_log.append({
                        "type": pii_pattern.name,
                        "original": match.group(),
                        "replacement": pii_pattern.replacement,
                        "position": match.span(),
                        "sensitivity": pii_pattern.sensitivity.value
                    })
                
                redacted_text = re.sub(
                    pii_pattern.pattern,
                    pii_pattern.replacement,
                    redacted_text,
                    flags=re.IGNORECASE
                )
        
        return redacted_text, redaction_log
    
    def _should_redact(self, pattern_sensitivity: DataSensitivityLevel, 
                      max_allowed_sensitivity: DataSensitivityLevel) -> bool:
        """Determine if a pattern should be redacted based on sensitivity levels"""
        sensitivity_hierarchy = {
            DataSensitivityLevel.PUBLIC: 0,
            DataSensitivityLevel.INTERNAL: 1,
            DataSensitivityLevel.CONFIDENTIAL: 2,
            DataSensitivityLevel.RESTRICTED: 3
        }
        
        return sensitivity_hierarchy[pattern_sensitivity] >= sensitivity_hierarchy[max_allowed_sensitivity]
    
    def detect_privacy_violations(self, text: str, user_context: Dict) -> List[Dict]:
        """Detect potential privacy violations in user queries"""
        violations = []
        text_lower = text.lower()
        
        # Check for attempts to access other employees' data
        if user_context.get("role") == "employee":
            employee_access_patterns = [
                r"another\s+employee",
                r"other\s+employee",
                r"coworker\s+pay",
                r"colleague\s+salary",
                r"john\s+doe",
                r"employee\s+\d+"
            ]
            
            for pattern in employee_access_patterns:
                if re.search(pattern, text_lower):
                    violations.append({
                        "type": "unauthorized_employee_access",
                        "severity": "high",
                        "description": "Attempt to access another employee's information",
                        "pattern": pattern
                    })
        
        # Check for sensitive data requests
        for keyword in self.sensitive_keywords:
            if keyword in text_lower:
                violations.append({
                    "type": "sensitive_data_request",
                    "severity": "medium",
                    "keyword": keyword,
                    "description": f"Query contains sensitive keyword: {keyword}"
                })
        
        # Check for forbidden content
        for pattern in self.forbidden_patterns:
            if re.search(pattern, text_lower):
                violations.append({
                    "type": "forbidden_content",
                    "severity": "critical",
                    "description": "Query contains potentially malicious content",
                    "pattern": pattern
                })
        
        return violations
    
    def validate_data_access(self, user_context: Dict, requested_data: Dict) -> Dict[str, Any]:
        """Validate if user has permission to access requested data"""
        role = user_context.get("role", "employee")
        employee_id = user_context.get("employee_id")
        requested_employee_id = requested_data.get("employee_id")
        data_type = requested_data.get("data_type")
        
        validation_result = {
            "allowed": True,
            "reason": "",
            "restrictions": []
        }
        
        # Employees can only access their own data
        if role == "employee" and requested_employee_id != employee_id:
            validation_result["allowed"] = False
            validation_result["reason"] = "Employees can only access their own payroll data"
            return validation_result
        
        # Check data type permissions
        role_permissions = {
            "employee": ["own_salary", "own_deductions", "own_benefits"],
            "hr": ["salary", "deductions", "benefits", "personal_info"],
            "finance": ["salary", "deductions", "benefits", "tax_info", "financial_data"]
        }
        
        allowed_data_types = role_permissions.get(role, [])
        if data_type not in allowed_data_types:
            validation_result["allowed"] = False
            validation_result["reason"] = f"Role '{role}' does not have permission to access '{data_type}'"
            return validation_result
        
        return validation_result
    
    def create_audit_log(self, user_context: Dict, query: str, response: str, 
                         redactions: List[Dict]) -> Dict:
        """Create audit log for privacy compliance"""
        audit_entry = {
            "timestamp": self._get_timestamp(),
            "user_id": user_context.get("employee_id"),
            "role": user_context.get("role"),
            "query_hash": self._hash_data(query),
            "response_hash": self._hash_data(response),
            "redactions_count": len(redactions),
            "redaction_types": list(set(r["type"] for r in redactions)),
            "privacy_violations": self.detect_privacy_violations(query, user_context),
            "jurisdiction": user_context.get("jurisdiction")
        }
        
        return audit_entry
    
    def _hash_data(self, data: str) -> str:
        """Create hash of sensitive data for audit purposes"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for audit logging"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def apply_privacy_filters(self, response: str, user_context: Dict) -> str:
        """Apply privacy filters to AI responses"""
        filtered_response = response
        
        # Add privacy disclaimers based on content
        if any(keyword in response.lower() for keyword in ["salary", "pay", "compensation"]):
            filtered_response += "\n\n*This compensation information is confidential and intended for your viewing only.*"
        
        if any(keyword in response.lower() for keyword in ["tax", "deduction"]):
            filtered_response += "\n\n*This information does not constitute tax or legal advice. Please consult a qualified professional for personal tax guidance.*"
        
        # Add role-specific reminders
        if user_context.get("role") == "employee":
            filtered_response += "\n\n*Remember: This information is for your personal use only and should not be shared with others.*"
        
        return filtered_response
    
    def sanitize_query(self, query: str) -> str:
        """Sanitize user query to prevent injection attacks"""
        # Remove potential SQL injection patterns
        sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bUPDATE\b.*\bSET\b)",
            r"(\bDELETE\b.*\bFROM\b)"
        ]
        
        sanitized = query
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized
