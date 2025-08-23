import streamlit as st
import pandas as pd
from utils.email_sender import EmailSender, EmailTemplate
from datetime import datetime, timedelta
import time

def show_bulk_sender():
    st.header("📤 Bulk Email Sender")
    st.markdown("Send personalized emails to multiple recipients with scheduling options.")
    
    # Check email configuration
    if 'email_credentials' not in st.session_state or not st.session_state.email_credentials:
        st.warning("⚠️ Please configure your email credentials in the main page sidebar first.")
        return
    
    # Test email connection
    test_connection()
    
    # Email composition interface
    compose_email_interface()

def test_connection():
    """Test email connection"""
    st.subheader("🔌 Email Connection Status")
    
    if st.button("Test Email Connection"):
        sender = EmailSender(st.session_state.email_credentials)
        result = sender.test_connection()
        
        if result['success']:
            st.success("✅ Email connection successful!")
        else:
            st.error(f"❌ Connection failed: {result['error']}")

def compose_email_interface():
    """Main email composition interface"""
    
    # Recipient management
    st.subheader("👥 Manage Recipients")
    
    recipient_tabs = st.tabs(["Manual Entry", "Upload CSV", "From Validation Results"])
    
    recipients = []
    
    with recipient_tabs[0]:
        recipients_text = st.text_area(
            "Enter email addresses (one per line):",
            height=150,
            placeholder="recipient1@example.com\nrecipient2@example.com\nrecipient3@example.com"
        )
        
        if recipients_text:
            recipients = [email.strip() for email in recipients_text.split('\n') if email.strip()]
            st.info(f"📧 {len(recipients)} recipients entered")
    
    with recipient_tabs[1]:
        uploaded_file = st.file_uploader("Upload CSV with recipients", type=['csv'])
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head(), use_container_width=True)
                
                email_column = st.selectbox("Select email column:", df.columns)
                
                if email_column:
                    recipients = df[email_column].dropna().tolist()
                    st.info(f"📧 {len(recipients)} recipients loaded from CSV")
            
            except Exception as e:
                st.error(f"Error reading CSV: {str(e)}")
    
    with recipient_tabs[2]:
        if 'validated_emails' in st.session_state and not st.session_state.validated_emails.empty:
            valid_emails = st.session_state.validated_emails[
                st.session_state.validated_emails['is_valid'] == True
            ]
            
            if not valid_emails.empty:
                use_validated = st.checkbox("Use validated email addresses")
                
                if use_validated:
                    recipients = valid_emails['email'].tolist()
                    st.success(f"✅ Using {len(recipients)} validated email addresses")
            else:
                st.info("No validated emails available. Run email validation first.")
        else:
            st.info("No validated emails available. Run email validation first.")
    
    if not recipients:
        st.warning("📭 No recipients selected. Please add some email addresses.")
        return
    
    # Email content composition
    st.subheader("✍️ Compose Email")
    
    # Template selection
    template_option = st.selectbox(
        "Choose email template:",
        ["Custom Message", "Welcome Email", "Newsletter", "Notification"]
    )
    
    # Subject line
    subject = st.text_input("Subject Line:", placeholder="Enter your email subject")
    
    # Message composition based on template
    if template_option == "Custom Message":
        compose_custom_message()
    elif template_option == "Welcome Email":
        compose_welcome_email(subject)
    elif template_option == "Newsletter":
        compose_newsletter(subject)
    elif template_option == "Notification":
        compose_notification(subject)
    
    # Get composed message from session state
    message = st.session_state.get('composed_message', '')
    is_html = st.session_state.get('message_is_html', False)
    
    # Preview section
    if message:
        with st.expander("📋 Email Preview", expanded=False):
            if is_html:
                st.markdown("**HTML Preview:**")
                st.markdown(message, unsafe_allow_html=True)
            else:
                st.markdown("**Text Preview:**")
                st.text(message)
    
    # Sending options
    st.subheader("📅 Sending Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        send_option = st.radio(
            "When to send:",
            ["Send Immediately", "Schedule for Later"]
        )
    
    with col2:
        schedule_datetime = None
        if send_option == "Schedule for Later":
            schedule_date = st.date_input(
                "Schedule Date:",
                value=datetime.now() + timedelta(hours=1),
                min_value=datetime.now()
            )
            schedule_time = st.time_input(
                "Schedule Time:",
                value=(datetime.now() + timedelta(hours=1)).time()
            )
            schedule_datetime = datetime.combine(schedule_date, schedule_time)
    
    # Advanced options
    with st.expander("⚙️ Advanced Options", expanded=False):
        delay_between_emails = st.slider(
            "Delay between emails (seconds):",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Add delay to avoid being flagged as spam"
        )
        
        test_mode = st.checkbox(
            "Test mode (send only to first 3 recipients)",
            help="Use this to test your email before sending to all recipients"
        )
    
    # Send button
    if st.button("🚀 Send Emails", type="primary", disabled=not (recipients and subject and message)):
        if send_option == "Schedule for Later":
            scheduled_dt = schedule_datetime
        else:
            scheduled_dt = None
        
        send_emails(
            recipients, subject, message, is_html,
            send_option, scheduled_dt,
            delay_between_emails, test_mode
        )

def compose_custom_message():
    """Custom message composition"""
    message_format = st.radio("Message format:", ["Plain Text", "HTML"])
    
    if message_format == "Plain Text":
        message = st.text_area(
            "Email Message:",
            height=200,
            placeholder="Enter your message here..."
        )
        st.session_state.composed_message = message
        st.session_state.message_is_html = False
    else:
        message = st.text_area(
            "HTML Message:",
            height=200,
            placeholder="<h1>Your HTML message here...</h1>\n<p>You can use HTML tags for formatting.</p>"
        )
        st.session_state.composed_message = message
        st.session_state.message_is_html = True

def compose_welcome_email(subject):
    """Welcome email template"""
    col1, col2 = st.columns(2)
    
    with col1:
        recipient_name = st.text_input("Recipient Name:", placeholder="New User")
    
    with col2:
        company_name = st.text_input("Company Name:", placeholder="Your Company")
    
    if recipient_name and company_name:
        message = EmailTemplate.create_welcome_template(recipient_name, company_name)
        st.session_state.composed_message = message
        st.session_state.message_is_html = True
        
        if not subject:
            st.session_state.default_subject = f"Welcome to {company_name}, {recipient_name}!"

def compose_newsletter(subject):
    """Newsletter template"""
    newsletter_title = st.text_input("Newsletter Title:", placeholder="Monthly Newsletter")
    newsletter_content = st.text_area(
        "Newsletter Content (HTML):",
        height=150,
        placeholder="<p>Your newsletter content here...</p>"
    )
    unsubscribe_link = st.text_input(
        "Unsubscribe Link:",
        placeholder="https://yoursite.com/unsubscribe"
    )
    
    if newsletter_title and newsletter_content:
        message = EmailTemplate.create_newsletter_template(
            newsletter_title, newsletter_content, unsubscribe_link or "#"
        )
        st.session_state.composed_message = message
        st.session_state.message_is_html = True

def compose_notification(subject):
    """Notification template"""
    notification_message = st.text_area(
        "Notification Message:",
        height=100,
        placeholder="Important update or notification..."
    )
    action_url = st.text_input(
        "Action URL (optional):",
        placeholder="https://yoursite.com/action"
    )
    
    if notification_message:
        message = EmailTemplate.create_notification_template(
            subject or "Important Notification",
            notification_message,
            action_url
        )
        st.session_state.composed_message = message
        st.session_state.message_is_html = True

def send_emails(recipients, subject, message, is_html, send_option, 
                schedule_datetime, delay, test_mode):
    """Send or schedule emails"""
    
    # Apply test mode
    if test_mode:
        recipients = recipients[:3]
        st.info(f"🧪 Test mode: Sending to first {len(recipients)} recipients only")
    
    if send_option == "Send Immediately":
        send_immediately(recipients, subject, message, is_html, delay)
    else:
        schedule_emails(recipients, subject, message, is_html, schedule_datetime)

def send_immediately(recipients, subject, message, is_html, delay):
    """Send emails immediately"""
    sender = EmailSender(st.session_state.email_credentials)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Results tracking
    successful_sends = 0
    failed_sends = []
    
    # Send emails
    for i, recipient in enumerate(recipients):
        status_text.text(f"Sending to {recipient} ({i+1}/{len(recipients)})")
        
        result = sender.send_single_email(recipient, subject, message, is_html)
        
        if result['success']:
            successful_sends += 1
        else:
            failed_sends.append(result)
        
        progress_bar.progress((i + 1) / len(recipients))
        
        # Add delay between sends
        if i < len(recipients) - 1:
            time.sleep(delay)
    
    # Show results
    status_text.empty()
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"✅ Successfully sent: {successful_sends}/{len(recipients)}")
    with col2:
        if failed_sends:
            st.error(f"❌ Failed sends: {len(failed_sends)}")
    
    # Show failed sends details
    if failed_sends:
        with st.expander("❌ Failed Sends Details", expanded=False):
            for failed in failed_sends:
                st.error(f"**{failed['recipient']}:** {failed['error']}")

def schedule_emails(recipients, subject, message, is_html, schedule_datetime):
    """Schedule emails for later sending"""
    from utils.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    
    if schedule_datetime:
        # Ensure scheduled_time is not NaT
        scheduled_timestamp = pd.Timestamp(schedule_datetime)
        if pd.isna(scheduled_timestamp):
            st.error("Invalid scheduled time")
            return
        
        job_id = scheduler.schedule_email(
            recipients, subject, message,
            scheduled_timestamp,
            st.session_state.email_credentials,
            is_html
        )
    else:
        st.error("Schedule date/time not provided")
        return
    
    st.success(f"📅 Email scheduled successfully!")
    st.info(f"**Job ID:** {job_id}")
    st.info(f"**Scheduled for:** {schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    st.info(f"**Recipients:** {len(recipients)} emails")

if __name__ == "__main__":
    show_bulk_sender()
