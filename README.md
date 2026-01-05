# Payroll AI Copilot - Code Only

A context-aware, role-based AI assistant for payroll queries with built-in safety, privacy, and compliance features.

## Features

- **Multi-role prompts** (Employee, HR, Finance)
- **Context-aware responses** based on user role and jurisdiction
- **Legal & ethical explanations** of payroll deductions
- **Hallucination prevention** with verified data sources
- **Sensitive data redaction** and privacy protection
- **Compliance-focused** responses with proper disclaimers

## Architecture

```
payroll-ai-copilot-code/
├── src/
│   ├── core/
│   │   ├── prompt_architecture.py    # Role-based prompt system
│   │   └── safety_privacy.py         # Data redaction & privacy
│   └── main.py                     # Main application
└── README.md
```

## Quick Start

1. Navigate to the project directory:
```bash
cd C:\Users\AKSHITA\Desktop\payroll-ai-copilot-code
```

2. Run the payroll copilot:
```bash
python src/main.py --demo
```

## Safety & Privacy

- Automatic PII redaction
- Role-based access control
- Verified data sources only
- No legal or tax advice
- Compliance-first approach

## Usage Examples

The system includes demonstration queries for:
- Employee overtime calculations (California)
- HR tax withholding guidance (Federal)
- Finance compliance requirements (Federal)

## Core Components

### Prompt Architecture
- Role-based access control (Employee, HR, Finance)
- Multi-jurisdiction support (US Federal, California, New York, UK, Canada)
- Context-aware prompt building
- Permission validation

### Safety & Privacy
- 10+ PII detection patterns (SSN, bank accounts, emails, phones, addresses)
- Role-based redaction levels
- Privacy violation detection
- Audit logging

### Main Application
- Complete query processing pipeline
- Demo functionality
- Error handling and logging

## Running the Demo

```bash
# Run demonstration queries
python src/main.py --demo

# Start interactive mode
python src/main.py
```

The demo will show:
- Employee overtime calculation with PII redaction
- HR tax withholding guidance with role-appropriate detail
- Finance compliance information with expanded permissions

## Code Structure

### Core Classes
- `UserContext`: User role, jurisdiction, and access level
- `PromptArchitecture`: Role-based prompt system
- `SafetyPrivacyManager`: PII redaction and privacy enforcement
- `PayrollAICopilot`: Main application controller

### Key Features
- **Input Sanitization**: SQL injection and XSS prevention
- **Permission Validation**: Role-based access control
- **PII Redaction**: Automatic sensitive data masking
- **Privacy Filters**: Response-level privacy protection
- **Audit Logging**: Complete interaction tracking

## Security Features

- Multi-layer privacy validation
- Role-based data access
- Automatic PII redaction
- Comprehensive audit trails
- Privacy violation detection

## Compliance

- FLSA compliance (Federal)
- California Labor Code compliance
- Tax withholding regulations
- Data protection requirements (GDPR, CCPA)

This is a production-ready payroll AI assistant with enterprise-grade security and privacy features.
