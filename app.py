import streamlit as st
import pandas as pd
import os
from utils.email_validator import EmailValidator
from utils.email_sender import EmailSender
import time

# Configure page
st.set_page_config(
    page_title="Email Validation & Bulk Sender",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'email_credentials' not in st.session_state:
    st.session_state.email_credentials = {}
if 'validated_emails' not in st.session_state:
    st.session_state.validated_emails = pd.DataFrame()

def main():
    st.title("📧 Email Validation & Bulk Sender Tool")
    st.markdown("---")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a feature:",
        ["Single Email Validation", "Bulk Email Validation", "Email Sender", "Scheduled Emails"]
    )
    
    # Email credentials sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("📧 Email Configuration")
    
    with st.sidebar.expander("SMTP Settings", expanded=False):
        smtp_server = st.text_input("SMTP Server", value="smtp.gmail.com", key="smtp_server")
        smtp_port = st.number_input("SMTP Port", value=587, key="smtp_port")
        email_address = st.text_input("Your Email Address", key="email_address")
        email_password = st.text_input("Email Password/App Password", type="password", key="email_password")
        
        if st.button("Save Email Configuration"):
            if email_address and email_password:
                st.session_state.email_credentials = {
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'email': email_address,
                    'password': email_password
                }
                st.success("✅ Email configuration saved!")
            else:
                st.error("❌ Please fill in all email fields")
    
    # Main content based on selected page
    if page == "Single Email Validation":
        single_email_validation()
    elif page == "Bulk Email Validation":
        bulk_email_validation()
    elif page == "Email Sender":
        email_sender_page()
    elif page == "Scheduled Emails":
        scheduled_emails_page()

def single_email_validation():
    st.header("🔍 Single Email Validation")
    st.markdown("Validate individual email addresses for syntax, domain, and deliverability.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        email_to_validate = st.text_input("Enter email address to validate:", placeholder="example@domain.com")
        
        if st.button("Validate Email", type="primary"):
            if email_to_validate:
                validator = EmailValidator()
                
                with st.spinner("Validating email..."):
                    result = validator.validate_single_email(email_to_validate)
                
                # Display simple results
                if result['is_valid']:
                    st.success(f"✅ **{email_to_validate}** valid")
                else:
                    st.error(f"❌ **{email_to_validate}** invalid")
            else:
                st.warning("Please enter an email address to validate.")
    
    with col2:
        st.markdown("### Validation Features")
        st.info("""
        **What we check:**
        
        🔤 **Syntax Validation**
        - Email format compliance
        - Special character handling
        
        🌐 **Domain Verification**
        - Domain existence check
        - DNS record validation
        
        📬 **MX Record Check**
        - Mail server availability
        - Priority validation
        
        🔌 **SMTP Verification**
        - Mailbox existence
        - Deliverability test
        """)

def bulk_email_validation():
    st.header("📋 Bulk Email Validation")
    st.markdown("Upload a CSV file to validate multiple email addresses at once.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="CSV should have an 'email' column or emails in the first column"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("### Preview of uploaded data:")
                st.dataframe(df.head(), use_container_width=True)
                
                # Identify email column
                email_columns = [col for col in df.columns if 'email' in col.lower()]
                if email_columns:
                    email_column = email_columns[0]
                else:
                    email_column = df.columns[0]
                
                selected_column = st.selectbox("Select email column:", df.columns, index=list(df.columns).index(email_column))
                
                if st.button("Start Bulk Validation", type="primary"):
                    emails_to_validate = df[selected_column].dropna().tolist()
                    
                    if emails_to_validate:
                        validator = EmailValidator()
                        
                        # Progress tracking
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        results_container = st.empty()
                        
                        results = []
                        
                        for i, email in enumerate(emails_to_validate):
                            status_text.text(f"Validating {i+1}/{len(emails_to_validate)}: {email}")
                            
                            result = validator.validate_single_email(email)
                            result['email'] = email
                            results.append(result)
                            
                            progress_bar.progress((i + 1) / len(emails_to_validate))
                            
                            # Show intermediate results
                            if (i + 1) % 10 == 0 or i == len(emails_to_validate) - 1:
                                temp_df = pd.DataFrame(results)
                                valid_count = temp_df['is_valid'].sum()
                                results_container.metric(
                                    label="Valid Emails Found",
                                    value=f"{valid_count}/{len(temp_df)}",
                                    delta=f"{(valid_count/len(temp_df)*100):.1f}% valid"
                                )
                        
                        # Final results
                        results_df = pd.DataFrame(results)
                        st.session_state.validated_emails = results_df
                        
                        status_text.success(f"✅ Validation complete! Processed {len(results)} emails.")
                        
                        # Summary stats
                        col1_stats, col2_stats, col3_stats = st.columns(3)
                        
                        with col1_stats:
                            valid_count = results_df['is_valid'].sum()
                            st.metric("Valid Emails", valid_count, f"{valid_count/len(results_df)*100:.1f}%")
                        
                        with col2_stats:
                            invalid_count = len(results_df) - valid_count
                            st.metric("Invalid Emails", invalid_count, f"{invalid_count/len(results_df)*100:.1f}%")
                        
                        with col3_stats:
                            avg_confidence = results_df['confidence'].mean()
                            st.metric("Avg Confidence", f"{avg_confidence:.1f}%")
                        
                        # Results table
                        st.markdown("### Validation Results")
                        display_df = results_df[['email', 'is_valid', 'confidence', 'syntax_valid', 'domain_valid', 'mx_valid', 'smtp_valid']]
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Export options
                        csv_data = results_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Full Results (CSV)",
                            data=csv_data,
                            file_name=f"email_validation_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                        
                        # Valid emails only export
                        valid_emails_df = results_df[results_df['is_valid'] == True]
                        if not valid_emails_df.empty:
                            valid_emails_series = valid_emails_df['email']
                            valid_csv = valid_emails_series.to_csv(index=False, header=False)
                            st.download_button(
                                label="📥 Download Valid Emails Only",
                                data=valid_csv,
                                file_name=f"valid_emails_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    
    with col2:
        st.markdown("### CSV Format")
        st.info("""
        **Expected format:**
        
        ```csv
        email
        user1@domain.com
        user2@domain.com
        user3@domain.com
        ```
        
        **Or any CSV with email column**
        """)
        
        # Sample CSV download
        sample_data = pd.DataFrame({
            'email': ['user1@example.com', 'user2@test.com', 'invalid-email', 'user3@domain.co.uk']
        })
        sample_csv = sample_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Sample CSV",
            data=sample_csv,
            file_name="sample_emails.csv",
            mime="text/csv"
        )

def email_sender_page():
    st.header("📤 Email Sender")
    st.markdown("Compose and send emails individually or in bulk.")
    
    if not st.session_state.email_credentials:
        st.warning("⚠️ Please configure your email credentials in the sidebar first.")
        return
    
    # Email composition
    st.subheader("✍️ Compose Email")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Recipients
        recipient_option = st.radio(
            "Select recipients:",
            ["Enter manually", "Use validated emails", "Upload CSV"]
        )
        
        recipients = []
        
        if recipient_option == "Enter manually":
            recipients_text = st.text_area(
                "Recipients (one per line):",
                placeholder="recipient1@domain.com\nrecipient2@domain.com"
            )
            if recipients_text:
                recipients = [email.strip() for email in recipients_text.split('\n') if email.strip()]
        
        elif recipient_option == "Use validated emails" and not st.session_state.validated_emails.empty:
            valid_emails = st.session_state.validated_emails[st.session_state.validated_emails['is_valid'] == True]
            if not valid_emails.empty:
                recipients = valid_emails['email'].tolist()
                st.info(f"Using {len(recipients)} validated email addresses")
            else:
                st.warning("No valid emails found. Please run bulk validation first.")
        
        elif recipient_option == "Upload CSV":
            csv_file = st.file_uploader("Upload CSV with email addresses", type=['csv'], key="sender_csv")
            if csv_file:
                try:
                    df = pd.read_csv(csv_file)
                    email_col = st.selectbox("Select email column:", df.columns)
                    recipients = df[email_col].dropna().tolist()
                    st.info(f"Loaded {len(recipients)} email addresses")
                except Exception as e:
                    st.error(f"Error reading CSV: {str(e)}")
        
        # Email content
        subject = st.text_input("Subject:", placeholder="Enter email subject")
        
        message_format = st.radio("Message format:", ["Plain Text", "HTML"])
        
        if message_format == "Plain Text":
            message = st.text_area("Message:", height=200, placeholder="Enter your message here...")
        else:
            message = st.text_area("HTML Message:", height=200, placeholder="<h1>Your HTML message here...</h1>")
        
        # Send options
        send_option = st.radio("Send option:", ["Send now", "Schedule for later"])
        
        scheduled_time = None
        if send_option == "Schedule for later":
            col_date, col_time = st.columns(2)
            with col_date:
                schedule_date = st.date_input("Date:")
            with col_time:
                schedule_time = st.time_input("Time:")
            
            if schedule_date and schedule_time:
                scheduled_time = pd.Timestamp.combine(schedule_date, schedule_time)
                st.info(f"Email will be sent on: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        st.markdown("### Email Statistics")
        if recipients:
            st.metric("Recipients", len(recipients))
            st.metric("Subject Length", len(subject) if subject else 0)
            st.metric("Message Length", len(message) if message else 0)
        
        st.markdown("### Send Status")
        if 'last_send_status' in st.session_state:
            st.json(st.session_state.last_send_status)
    
    # Send button
    if st.button("Send Emails", type="primary", disabled=not (recipients and subject and message)):
        if recipients and subject and message:
            sender = EmailSender(st.session_state.email_credentials)
            
            if send_option == "Send now":
                with st.spinner("Sending emails..."):
                    results = sender.send_bulk_email(recipients, subject, message, is_html=(message_format == "HTML"))
                
                st.session_state.last_send_status = results
                
                # Show results
                successful = sum(1 for r in results if r['success'])
                failed = len(results) - successful
                
                col1_result, col2_result = st.columns(2)
                with col1_result:
                    st.success(f"✅ Successfully sent: {successful}")
                with col2_result:
                    st.error(f"❌ Failed to send: {failed}")
                
                # Detailed results
                if failed > 0:
                    st.markdown("### Failed Sends")
                    failed_results = [r for r in results if not r['success']]
                    for result in failed_results:
                        st.error(f"❌ {result['recipient']}: {result['error']}")
            
            else:  # Schedule for later
                if scheduled_time:
                    from utils.scheduler import EmailScheduler
                    scheduler = EmailScheduler()
                    
                    # Ensure scheduled_time is not NaT
                    scheduled_timestamp = pd.Timestamp(scheduled_time)
                    if pd.isna(scheduled_timestamp):
                        st.error("Invalid scheduled time")
                        return
                    
                    job_id = scheduler.schedule_email(
                        recipients, subject, message, scheduled_timestamp,
                        st.session_state.email_credentials, is_html=(message_format == "HTML")
                    )
                    
                    st.success(f"✅ Email scheduled successfully! Job ID: {job_id}")
                    st.info(f"Email will be sent on: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.error("Please fill in all required fields.")

def scheduled_emails_page():
    st.header("⏰ Scheduled Emails")
    st.markdown("View and manage your scheduled email jobs.")
    
    from utils.scheduler import EmailScheduler
    scheduler = EmailScheduler()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get scheduled jobs
        jobs = scheduler.get_scheduled_jobs()
        
        if jobs:
            st.subheader("📅 Scheduled Jobs")
            
            for job in jobs:
                with st.expander(f"Job {job['id']} - {job['subject']}", expanded=False):
                    col_info, col_action = st.columns([3, 1])
                    
                    with col_info:
                        st.write(f"**Subject:** {job['subject']}")
                        st.write(f"**Recipients:** {len(job['recipients'])} emails")
                        st.write(f"**Scheduled for:** {job['scheduled_time']}")
                        st.write(f"**Status:** {job['status']}")
                        
                        if job['status'] == 'completed':
                            st.write(f"**Sent at:** {job['sent_time']}")
                            st.write(f"**Success rate:** {job['success_count']}/{job['total_count']}")
                    
                    with col_action:
                        if job['status'] == 'pending':
                            if st.button(f"Cancel Job {job['id']}", key=f"cancel_{job['id']}"):
                                scheduler.cancel_job(job['id'])
                                st.success("Job cancelled!")
                                st.rerun()
        else:
            st.info("📭 No scheduled emails found.")
    
    with col2:
        st.markdown("### Quick Actions")
        
        if st.button("🔄 Refresh Jobs"):
            st.rerun()
        
        if st.button("🧹 Clear Completed Jobs"):
            scheduler.clear_completed_jobs()
            st.success("Completed jobs cleared!")
            st.rerun()
        
        st.markdown("### Job Status Legend")
        st.info("""
        **📅 Pending** - Waiting to be sent
        
        **📤 Sending** - Currently sending
        
        **✅ Completed** - Successfully sent
        
        **❌ Failed** - Send failed
        
        **⏸️ Cancelled** - Job cancelled
        """)

if __name__ == "__main__":
    main()
