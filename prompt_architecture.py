"""
Payroll AI Copilot - Prompt Architecture
Role-based prompt system with context awareness and safety controls
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

class UserRole(Enum):
    EMPLOYEE = "employee"
    HR = "hr"
    FINANCE = "finance"

class Jurisdiction(Enum):
    US_FEDERAL = "us_federal"
    US_CALIFORNIA = "us_california"
    US_NEW_YORK = "us_new_york"
    UK = "uk"
    CANADA = "canada"

@dataclass
class UserContext:
    role: UserRole
    jurisdiction: Jurisdiction
    employee_id: Optional[str] = None
    department: Optional[str] = None
    access_level: int = 1  # 1=employee, 2=hr, 3=finance

class PromptArchitecture:
    def __init__(self):
        self.role_permissions = {
            UserRole.EMPLOYEE: {
                "can_view_own_payroll": True,
                "can_view_own_deductions": True,
                "can_view_company_policies": True,
                "can_view_others_data": False,
                "can_modify_data": False
            },
            UserRole.HR: {
                "can_view_own_payroll": True,
                "can_view_own_deductions": True,
                "can_view_company_policies": True,
                "can_view_others_data": True,
                "can_modify_data": True,
                "can_handle_disputes": True
            },
            UserRole.FINANCE: {
                "can_view_own_payroll": True,
                "can_view_own_deductions": True,
                "can_view_company_policies": True,
                "can_view_others_data": True,
                "can_modify_data": True,
                "can_process_payroll": True,
                "can_view_financial_reports": True
            }
        }
        
        self.base_system_prompt = """
You are a Payroll AI Copilot. Your mission is to provide accurate, compliant, and helpful payroll information.

CORE PRINCIPLES:
1. Role-based access: Only provide information within the user's role permissions
2. Legal compliance: Reference applicable laws but never give legal or tax advice
3. Privacy protection: Never expose sensitive employee data
4. Verified information: Use only official regulations or approved company policy
5. Transparency: Clearly state when information cannot be verified

SAFETY RULES:
- Redact or mask all PII (bank details, tax IDs, social security numbers)
- Never share another employee's payroll information
- If uncertain, state that information cannot be verified
- For disputes or compliance issues, recommend HR/Payroll escalation
- Always include appropriate disclaimers

RESPONSE STYLE:
- Clear, neutral, and concise
- Use plain language for complex payroll concepts
- Provide step-by-step explanations when helpful
- Include relevant law/regulation names when applicable
"""

    def build_contextual_prompt(self, user_context: UserContext, query: str) -> str:
        """Build role-aware prompt with context"""
        
        role_specific_instructions = self._get_role_instructions(user_context.role)
        jurisdiction_context = self._get_jurisdiction_context(user_context.jurisdiction)
        privacy_constraints = self._get_privacy_constraints(user_context.role)
        
        full_prompt = f"""
{self.base_system_prompt}

USER CONTEXT:
- Role: {user_context.role.value}
- Jurisdiction: {user_context.jurisdiction.value}
- Access Level: {user_context.access_level}

{role_specific_instructions}

{jurisdiction_context}

{privacy_constraints}

USER QUERY: {query}

Remember: Respond only within your role permissions and maintain strict privacy standards.
"""
        return full_prompt
    
    def _get_role_instructions(self, role: UserRole) -> str:
        """Get role-specific instructions"""
        instructions = {
            UserRole.EMPLOYEE: """
EMPLOYEE ROLE INSTRUCTIONS:
- You can only view your own payroll information
- Explain your own pay, deductions, and benefits
- Provide general payroll education and policy information
- Cannot access or discuss other employees' data
- For payroll errors, guide them to HR/Payroll department
""",
            UserRole.HR: """
HR ROLE INSTRUCTIONS:
- Can access employee payroll data for legitimate business purposes
- Handle payroll disputes and employee inquiries
- Explain company policies and procedures
- Can process payroll corrections and adjustments
- Must maintain employee confidentiality
- For complex legal issues, recommend legal counsel consultation
""",
            UserRole.FINANCE: """
FINANCE ROLE INSTRUCTIONS:
- Full access to payroll data and financial reports
- Process payroll runs and tax filings
- Handle financial compliance and reporting
- Analyze payroll costs and budgeting
- Access to sensitive financial data requires proper justification
- For audit or legal compliance, coordinate with HR and Legal departments
"""
        }
        return instructions.get(role, "")
    
    def _get_jurisdiction_context(self, jurisdiction: Jurisdiction) -> str:
        """Get jurisdiction-specific context"""
        contexts = {
            Jurisdiction.US_FEDERAL: """
US FEDERAL JURISDICTION:
- Reference: Fair Labor Standards Act (FLSA), Internal Revenue Code (IRC)
- Federal tax withholding: Form W-4 guidelines
- FICA taxes: Social Security (6.2%) and Medicare (1.45%)
- Federal unemployment tax (FUTA)
- Minimum wage: Federal minimum applies where state minimum is lower
""",
            Jurisdiction.US_CALIFORNIA: """
CALIFORNIA JURISDICTION:
- Reference: California Labor Code, Wage Orders
- State minimum wage: Higher than federal minimum
- California State Disability Insurance (SDI)
- Paid Family Leave (PFL)
- Overtime: 8 hours/day or 40 hours/week
- Meal and rest break requirements
- Final paycheck timing rules
""",
            Jurisdiction.US_NEW_YORK: """
NEW YORK JURISDICTION:
- Reference: New York Labor Law
- State minimum wage: Tiered by region and employer size
- Paid Family Leave (PFL)
- Spread of hours pay for certain shifts
- Overtime: 40 hours/week
- Wage notice requirements
""",
            Jurisdiction.UK: """
UK JURISDICTION:
- Reference: Employment Rights Act 1996, Income Tax (Earnings and Pensions) Act 2003
- National Insurance contributions
- PAYE (Pay As You Earn) system
- National Minimum Wage/Living Wage
- Statutory Sick Pay (SSP)
- Auto-enrolment pension requirements
""",
            Jurisdiction.CANADA: """
CANADA JURISDICTION:
- Reference: Canada Labour Code, Income Tax Act
- CPP (Canada Pension Plan) contributions
- EI (Employment Insurance) premiums
- Federal and provincial income tax
- Employment Standards legislation varies by province
- Statutory holidays and vacation entitlements
"""
        }
        return contexts.get(jurisdiction, "")
    
    def _get_privacy_constraints(self, role: UserRole) -> str:
        """Get privacy constraints based on role"""
        base_constraints = """
PRIVACY & DATA PROTECTION:
- Never include full Social Security Numbers, bank account numbers, or tax IDs
- Mask sensitive data: XXX-XX-1234, XXXX-XXXX-XXXX-1234
- Do not share employee addresses, phone numbers, or personal emails
- Salary information should only be discussed with authorized personnel
- Maintain audit trail of all data access
"""
        
        role_specific = {
            UserRole.EMPLOYEE: "- Only discuss your own payroll information",
            UserRole.HR: "- Access employee data only for legitimate HR purposes",
            UserRole.FINANCE: "- Handle financial data with highest security standards"
        }
        
        return base_constraints + role_specific.get(role, "")
    
    def validate_query_permissions(self, user_context: UserContext, query: str) -> Dict[str, Any]:
        """Validate if query is within user's role permissions"""
        query_lower = query.lower()
        permissions = self.role_permissions.get(user_context.role, {})
        
        # Check for attempts to access other employees' data
        if user_context.role == UserRole.EMPLOYEE:
            employee_patterns = [
                r"another employee",
                r"other employee",
                r"my coworker",
                r"my colleague",
                r"employee\s+\d+",
                r"john\s+doe",
                r"salary of"
            ]
            
            for pattern in employee_patterns:
                if re.search(pattern, query_lower):
                    return {
                        "allowed": False,
                        "reason": "Employees cannot access other employees' payroll information",
                        "suggestion": "Please contact HR for any inquiries about other employees"
                    }
        
        # Check for data modification attempts
        if not permissions.get("can_modify_data", False):
            modify_patterns = [
                r"change\s+salary",
                r"update\s+pay",
                r"modify\s+deduction",
                r"adjust\s+payroll",
                r"correct\s+my\s+pay"
            ]
            
            for pattern in modify_patterns:
                if re.search(pattern, query_lower):
                    return {
                        "allowed": False,
                        "reason": "Your role does not have permission to modify payroll data",
                        "suggestion": "Please contact HR or Payroll department for payroll changes"
                    }
        
        return {"allowed": True}
