"""
Payroll AI Copilot - Main Application Entry Point
Context-aware, role-based AI assistant for payroll queries
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.prompt_architecture import PromptArchitecture, UserContext, UserRole, Jurisdiction
from core.safety_privacy import SafetyPrivacyManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PayrollQuery:
    user_id: str
    role: str
    jurisdiction: str
    query: str
    context: Optional[Dict[str, Any]] = None

class PayrollAICopilot:
    def __init__(self):
        """Initialize Payroll AI Copilot with all components"""
        self.prompt_architecture = PromptArchitecture()
        self.safety_manager = SafetyPrivacyManager()
        
        logger.info("Payroll AI Copilot initialized successfully")
    
    def process_query(self, payroll_query: PayrollQuery) -> Dict[str, Any]:
        """
        Process a payroll query through complete pipeline
        
        Args:
            payroll_query: The user's payroll query with context
            
        Returns:
            Dict containing response and metadata
        """
        try:
            # Step 1: Create user context
            user_context = self._create_user_context(payroll_query)
            
            # Step 2: Sanitize input
            sanitized_query = self.safety_manager.sanitize_query(payroll_query.query)
            
            # Step 3: Validate permissions
            permission_check = self.prompt_architecture.validate_query_permissions(
                user_context, sanitized_query
            )
            
            if not permission_check["allowed"]:
                return self._create_permission_denied_response(permission_check)
            
            # Step 4: Check for privacy violations
            privacy_violations = self.safety_manager.detect_privacy_violations(
                sanitized_query, user_context.__dict__
            )
            
            if privacy_violations:
                return self._handle_privacy_violations(privacy_violations)
            
            # Step 5: Build contextual prompt
            contextual_prompt = self.prompt_architecture.build_contextual_prompt(
                user_context, sanitized_query
            )
            
            # Step 6: Generate response (simulated for demo)
            ai_response = self._generate_ai_response(contextual_prompt, user_context)
            
            # Step 7: Apply privacy filters and redaction
            filtered_response, redaction_log = self.safety_manager.redact_pii(
                ai_response, user_context.role.value
            )
            
            # Step 8: Create audit log
            audit_log = self.safety_manager.create_audit_log(
                user_context.__dict__,
                sanitized_query,
                filtered_response,
                redaction_log
            )
            
            # Step 9: Apply final privacy filters
            final_response = self.safety_manager.apply_privacy_filters(
                filtered_response, user_context.__dict__
            )
            
            return {
                "success": True,
                "response": final_response,
                "metadata": {
                    "user_role": user_context.role.value,
                    "jurisdiction": user_context.jurisdiction.value,
                    "redactions_applied": len(redaction_log),
                    "query_processed_at": audit_log["timestamp"]
                },
                "audit_log": audit_log
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return self._create_error_response(str(e))
    
    def _create_user_context(self, payroll_query: PayrollQuery) -> UserContext:
        """Create UserContext from payroll query"""
        role_map = {
            "employee": UserRole.EMPLOYEE,
            "hr": UserRole.HR,
            "finance": UserRole.FINANCE
        }
        
        jurisdiction_map = {
            "us_federal": Jurisdiction.US_FEDERAL,
            "us_california": Jurisdiction.US_CALIFORNIA,
            "us_new_york": Jurisdiction.US_NEW_YORK,
            "uk": Jurisdiction.UK,
            "canada": Jurisdiction.CANADA
        }
        
        role = role_map.get(payroll_query.role.lower(), UserRole.EMPLOYEE)
        jurisdiction = jurisdiction_map.get(
            payroll_query.jurisdiction.lower(), Jurisdiction.US_FEDERAL
        )
        
        # Determine access level based on role
        access_levels = {
            UserRole.EMPLOYEE: 1,
            UserRole.HR: 2,
            UserRole.FINANCE: 3
        }
        
        return UserContext(
            role=role,
            jurisdiction=jurisdiction,
            employee_id=payroll_query.user_id,
            access_level=access_levels[role]
        )
    
    def _generate_ai_response(self, prompt: str, user_context: UserContext) -> str:
        """
        Generate AI response based on contextual prompt
        In a real implementation, this would call an AI model API
        """
        # For demo purposes, we'll use predefined responses based on query type
        query_lower = prompt.lower()
        
        # Determine query type and generate appropriate response
        if "overtime" in query_lower:
            return self._get_overtime_response(user_context)
        elif "tax" in query_lower or "withholding" in query_lower:
            return self._get_tax_response(user_context)
        elif "deduction" in query_lower:
            return self._get_deduction_response(user_context)
        elif "benefit" in query_lower or "401k" in query_lower:
            return self._get_benefit_response(user_context)
        elif "error" in query_lower or "mistake" in query_lower:
            return self._get_error_response(user_context)
        elif "policy" in query_lower:
            return self._get_policy_response(user_context)
        else:
            return self._get_general_response(user_context)
    
    def _get_overtime_response(self, user_context: UserContext) -> str:
        """Generate overtime-related response"""
        if user_context.jurisdiction == Jurisdiction.US_CALIFORNIA:
            return """
Based on California labor laws, here's how overtime is calculated:

**Daily Overtime:** 1.5x regular rate for hours over 8 in a day
**Weekly Overtime:** 1.5x regular rate for hours over 40 in a week
**Double Time:** 2x regular rate for hours over 12 in a day or over 8 hours on 7th consecutive day

**Example Calculation:**
If you work 45 hours in a week with one 10-hour day:
- Regular pay: 35 hours × regular rate
- Daily overtime: 2 hours × 1.5 × regular rate
- Weekly overtime: 5 hours × 1.5 × regular rate

**Important Notes:**
- Meal breaks are required for shifts over 5 hours
- Rest breaks required for every 4 hours worked
- Your overtime should appear on your next paycheck

*This information is based on California Labor Code. For specific questions about your paycheck, contact Payroll.*
"""
        else:
            return """
Based on federal labor laws (FLSA), overtime is calculated as:

**Weekly Overtime:** 1.5x regular rate for hours over 40 in a workweek

**Example Calculation:**
If you work 45 hours in a week:
- Regular pay: 40 hours × regular rate
- Overtime pay: 5 hours × 1.5 × regular rate

**Important Notes:**
- Some states have additional overtime requirements
- Check your employment agreement for industry-specific rules
- Overtime should be paid in next regular paycheck

*This information is based on federal FLSA requirements. State laws may provide additional protections.*
"""
    
    def _get_tax_response(self, user_context: UserContext) -> str:
        """Generate tax-related response"""
        return """
Regarding your tax question:

**Federal Tax Withholding:**
- Based on your Form W-4 elections
- Social Security tax: 6.2% (up to wage base limit)
- Medicare tax: 1.45% (no wage base limit)
- Additional Medicare: 0.9% on wages over $200,000

**State Taxes:**
- Varies by state of residence
- Some states have no income tax
- Check your state withholding form

**Important Information:**
- Tax laws change periodically
- I cannot provide tax advice - consult a tax professional
- Update your W-4 for life changes (marriage, dependents, etc.)

**For Tax Questions:**
- Personal tax advice: Contact a qualified tax professional
- Withholding changes: Update your Form W-4 with HR
- Tax forms: Available through employee portal

*This information is for educational purposes only and does not constitute tax advice.*
"""
    
    def _get_deduction_response(self, user_context: UserContext) -> str:
        """Generate deduction-related response"""
        return """
Here's an explanation of common payroll deductions:

**Tax Deductions:**
- Federal income tax withholding
- State and local taxes (if applicable)
- Social Security and Medicare taxes

**Benefit Deductions:**
- Health insurance premiums
- Dental/vision insurance
- Retirement contributions (401k, 403b)
- Life insurance

**Other Deductions:**
- Wage garnishments (if applicable)
- Union dues (if applicable)
- Parking/transportation benefits

**Important Notes:**
- Deduction amounts are based on your elections
- Some deductions are pre-tax, reducing taxable income
- Others are post-tax, taken from net pay

**Questions About Deductions:**
- Benefit deductions: Contact HR
- Tax questions: Consult a tax professional
- Calculation questions: Contact Payroll department

*Deduction amounts are calculated based on your elections and legal requirements.*
"""
    
    def _get_benefit_response(self, user_context: UserContext) -> str:
        """Generate benefit-related response"""
        return """
Regarding your benefits inquiry:

**Health Benefits:**
- Medical, dental, and vision coverage
- Premiums deducted from paycheck
- Coverage details in benefit summaries
- Open enrollment for annual changes

**Retirement Benefits:**
- 401(k) or similar retirement plan
- Employer matching contributions
- Pre-tax contributions reduce taxable income
- Investment options and advice available

**Other Benefits:**
- Life insurance
- Disability insurance
- Flexible spending accounts
- Paid time off and holidays

**For Benefit Information:**
- Coverage details: Check benefits portal
- Enrollment changes: Contact HR during open enrollment
- Claims questions: Contact insurance providers directly
- Investment advice: Available through retirement plan provider

*Benefit coverage and costs are subject to plan terms and may change annually.*
"""
    
    def _get_error_response(self, user_context: UserContext) -> str:
        """Generate error resolution response"""
        return """
I understand you're concerned about a payroll error. Here's how to address it:

**Payroll Error Resolution Process:**
1. **Document Issue**: Note the specific error and pay period
2. **Report Immediately**: Contact Payroll department
3. **Investigation**: Payroll will review and verify the error
4. **Correction**: Process corrections in next payroll cycle
5. **Confirmation**: You'll receive confirmation of the correction

**Contact Information:**
- Payroll Department: payroll@company.com / [Phone Number]
- HR Department: hr@company.com / [Phone Number]

**Timeline:**
- Standard corrections: 1-2 pay periods
- Urgent corrections: Contact Payroll immediately

**Your Rights:**
- Employers must pay for all hours worked
- Corrections must include any applicable overtime
- Prompt payment is required by law

*Document everything and follow up to ensure the correction is processed properly.*
"""
    
    def _get_policy_response(self, user_context: UserContext) -> str:
        """Generate policy-related response"""
        return """
Regarding your policy question:

**Company Policies:**
- Complete policies available in employee handbook
- Policies may be updated periodically
- Some policies vary by location or department

**Common Policy Areas:**
- Payroll processing schedules
- Time off and leave policies
- Expense reimbursement procedures
- Remote work policies
- Code of conduct

**For Policy Clarifications:**
- HR Department: Primary contact for policy questions
- Manager: For department-specific policies
- Legal Department: For compliance-related questions

**Important:**
- Policies are subject to change
- Always refer to the most current version
- When in doubt, ask HR for clarification

*This summary is for reference only. The official employee handbook contains complete policy details.*
"""
    
    def _get_general_response(self, user_context: UserContext) -> str:
        """Generate general payroll response"""
        return """
Thank you for your payroll question.

**General Payroll Information:**
- Paychecks are issued on [schedule]
- Paystubs available through employee portal
- Direct deposit preferred payment method
- Tax forms available by January 31

**Common Resources:**
- Employee Portal: [portal.company.com]
- HR Department: hr@company.com / [Phone]
- Payroll Department: payroll@company.com / [Phone]

**For Specific Questions:**
- Paycheck issues: Contact Payroll
- Benefits questions: Contact HR
- Tax questions: Consult tax professional

**Need More Help?**
- Check the employee handbook for policies
- Review your paystub for detailed information
- Schedule appointment with HR for complex issues

*This information is for general guidance and does not constitute legal or financial advice.*
"""
    
    def _create_permission_denied_response(self, permission_check: Dict) -> Dict[str, Any]:
        """Create response for permission denied scenarios"""
        return {
            "success": False,
            "error": "PERMISSION_DENIED",
            "message": permission_check["reason"],
            "suggestion": permission_check.get("suggestion", "Please contact HR if you believe this is an error"),
            "response": f"I'm sorry, but {permission_check['reason']}. {permission_check.get('suggestion', '')}"
        }
    
    def _handle_privacy_violations(self, violations: list) -> Dict[str, Any]:
        """Handle privacy violation scenarios"""
        critical_violations = [v for v in violations if v["severity"] == "critical"]
        
        if critical_violations:
            return {
                "success": False,
                "error": "PRIVACY_VIOLATION",
                "message": "Query contains potentially harmful content",
                "response": "I'm sorry, but I cannot process this request due to privacy and security concerns. Please contact HR or Payroll directly for assistance."
            }
        
        return {
            "success": False,
            "error": "PRIVACY_CONCERN",
            "message": "Query contains sensitive content",
            "response": "I'm sorry, but I cannot provide that information. Please contact HR or Payroll for assistance with this request."
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "success": False,
            "error": "SYSTEM_ERROR",
            "message": "An error occurred while processing your request",
            "response": "I'm sorry, but I encountered an error while processing your request. Please try again later or contact the Payroll department for immediate assistance.",
            "technical_details": error_message
        }
    
    def run_demo_queries(self) -> None:
        """Run demonstration queries to showcase functionality"""
        print("=" * 80)
        print("PAYROLL AI COPILOT DEMO")
        print("=" * 80)
        
        demo_queries = [
            {
                "user_id": "EMP001",
                "role": "employee",
                "jurisdiction": "us_california",
                "query": "I worked 45 hours last week. How should my overtime be calculated?"
            },
            {
                "user_id": "HR001",
                "role": "hr",
                "jurisdiction": "us_federal",
                "query": "An employee wants to change their tax withholding. What forms do they need?"
            },
            {
                "user_id": "FIN001",
                "role": "finance",
                "jurisdiction": "us_federal",
                "query": "What are the key compliance requirements for quarterly payroll tax filing?"
            }
        ]
        
        for i, query_data in enumerate(demo_queries, 1):
            print(f"\n--- Demo Query {i} ---")
            print(f"User: {query_data['user_id']} ({query_data['role']})")
            print(f"Jurisdiction: {query_data['jurisdiction']}")
            print(f"Query: {query_data['query']}")
            print("\nProcessing...")
            
            payroll_query = PayrollQuery(**query_data)
            result = self.process_query(payroll_query)
            
            if result["success"]:
                print(f"\nResponse:")
                print(result["response"])
                print(f"\nMetadata:")
                for key, value in result["metadata"].items():
                    print(f"  {key}: {value}")
            else:
                print(f"\nError: {result['error']}")
                print(f"Message: {result['message']}")
            
            print("\n" + "-" * 60)

def main():
    """Main entry point for application"""
    print("Payroll AI Copilot")
    print("Context-aware, role-based payroll assistance")
    print("\nInitializing...")
    
    # Initialize copilot
    copilot = PayrollAICopilot()
    
    # Check if running demo or interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        copilot.run_demo_queries()
    else:
        print("\nPayroll AI Copilot is ready!")
        print("Run with --demo flag to see demonstration queries")
        print("\nAvailable features:")
        print("- Role-based access control (Employee, HR, Finance)")
        print("- Multi-jurisdiction support (US Federal, California, New York, UK, Canada)")
        print("- PII redaction and privacy protection")
        print("- Compliance checking and validation")
        print("- Comprehensive audit logging")

if __name__ == "__main__":
    main()
