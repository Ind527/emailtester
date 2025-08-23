# Overview

This is a comprehensive Email Validation & Bulk Sender Tool built with Streamlit. The application provides email validation services, bulk email sending capabilities, and scheduled email management. It features a multi-page interface for single/bulk email validation, personalized bulk email campaigns, and scheduled email delivery with real-time monitoring.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Framework**: Streamlit with multi-page application structure
- **Navigation**: Sidebar-based page selection with expandable configuration sections
- **State Management**: Session state for email credentials and validation results
- **UI Components**: Tabs, expandable sections, file uploaders, and real-time data tables

## Backend Architecture
- **Modular Design**: Utility classes separated by functionality (validation, sending, scheduling)
- **Email Validation**: Multi-step validation process including syntax, domain, MX records, and SMTP verification
- **Email Sending**: SMTP-based email delivery with support for HTML content and attachments
- **Scheduling System**: File-based job persistence with background thread execution

## Core Components

### Email Validation System
- **Syntax Validation**: Uses `email-validator` library for RFC compliance
- **Domain Verification**: DNS resolution and domain existence checks
- **MX Record Validation**: Mail exchanger record verification
- **SMTP Verification**: Optional connection testing to target mail servers
- **Caching**: MX record caching for performance optimization

### Email Delivery System
- **SMTP Integration**: Configurable SMTP servers with SSL/TLS support
- **Template Support**: HTML and plain text email formatting
- **Attachment Handling**: File attachment support via MIME encoding
- **Batch Processing**: Bulk sending with rate limiting and error handling

### Scheduling Engine
- **Job Persistence**: JSON file-based job storage
- **Background Processing**: Threaded scheduler for non-blocking execution
- **Status Tracking**: Real-time job status monitoring (pending, sending, completed, failed)
- **Management Interface**: Job viewing, cancellation, and cleanup capabilities

## Data Flow
1. **Configuration**: Users set SMTP credentials via sidebar interface
2. **Validation**: Email addresses processed through multi-stage validation pipeline
3. **Composition**: Email content created with recipient management and template support
4. **Delivery**: Immediate sending or scheduled execution via background processor
5. **Monitoring**: Real-time status updates and job management through dedicated interface

## Security Considerations
- **Credential Storage**: Session-based credential management (no persistent storage)
- **SSL/TLS**: Secure email transmission protocols
- **Input Validation**: Email address sanitization and validation
- **Error Handling**: Comprehensive error catching and user feedback

# External Dependencies

## Python Libraries
- **streamlit**: Web application framework and UI components
- **pandas**: Data manipulation and CSV processing
- **email-validator**: RFC-compliant email syntax validation
- **dnspython**: DNS resolution for domain and MX record verification
- **smtplib**: Built-in SMTP client for email delivery

## Email Services
- **SMTP Servers**: Configurable support for Gmail, Outlook, and custom SMTP providers
- **Authentication**: Email/password or app-specific password authentication
- **SSL/TLS**: Secure connection protocols for email transmission

## File System
- **CSV Processing**: File upload and parsing for bulk operations
- **Job Persistence**: JSON file storage for scheduled email jobs
- **Attachment Support**: File system access for email attachments

## Network Services
- **DNS Resolution**: Domain validation and MX record lookup
- **SMTP Connectivity**: Real-time email server connection testing
- **Background Processing**: Threaded execution for scheduled operations