import streamlit as st
import pandas as pd
import os
from utils.email_validator import EmailValidator
from utils.email_sender import EmailSender
import time
import base64
from pathlib import Path

# Configure page
st.set_page_config(
    page_title="Email Validation & Bulk Sender",
    page_icon="✉",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_custom_css():
    css_file = Path("static/style.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Load Font Awesome and Poppins
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
    * {
        font-family: 'Poppins', sans-serif !important;
    }
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
        transition: all 0.3s ease;
    }
    .feature-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 2rem 0;
    }
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        min-width: 150px;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #667eea;
    }
    .stat-label {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Load custom JavaScript
def load_custom_js():
    js_file = Path("static/script.js")
    if js_file.exists():
        with open(js_file) as f:
            st.markdown(f"<script>{f.read()}</script>", unsafe_allow_html=True)

# Initialize session state
if 'email_credentials' not in st.session_state:
    st.session_state.email_credentials = {}
if 'validated_emails' not in st.session_state:
    st.session_state.validated_emails = pd.DataFrame()

def main():
    # Load custom styling
    load_custom_css()
    load_custom_js()
    
    # Ultra Modern Hero Header
    st.markdown("""
    <div class="hero-header floating">
        <h1 class="hero-title">
            <i class="fas fa-envelope" style="margin-right: 0.5rem;"></i>EmailPro
        </h1>
        <p class="hero-subtitle">Validate & Send Emails Effortlessly</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Simplified Navigation
    st.sidebar.markdown("""
    <div class="nav-card">
        <h2 class="nav-title"><i class="fas fa-rocket" style="margin-right: 0.5rem;"></i>Menu</h2>
        <p class="nav-subtitle">Choose your tool</p>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.sidebar.selectbox(
        "Select Tool:",
        ["Single Email Validation", "Bulk Email Validation", "Email Discovery", "Email Sender", "Scheduled Emails"],
        format_func=lambda x: {
            "Single Email Validation": "🎯 Single Validator",
            "Bulk Email Validation": "📊 Bulk Validator", 
            "Email Discovery": "🔍 Email Finder",
            "Email Sender": "📤 Email Sender",
            "Scheduled Emails": "⏰ Scheduler"
        }.get(x, x)
    )
    
    # Simplified Email Config
    st.sidebar.markdown("""
    <div class="nav-card">
        <h3 style="color: white; margin: 0; font-size: 1.1rem;"><i class="fas fa-cog" style="margin-right: 0.5rem;"></i>Email Config</h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.sidebar.expander("Pengaturan SMTP", expanded=False):
        smtp_server = st.text_input("Server SMTP", value="smtp.gmail.com", key="smtp_server", help="Masukkan server SMTP provider email Anda", placeholder="smtp.gmail.com")
        smtp_port = st.number_input("Port SMTP", value=587, key="smtp_port", help="Port standar untuk Gmail: 587")
        email_address = st.text_input("Alamat Email Anda", key="email_address", help="Email yang akan digunakan untuk mengirim", placeholder="nama@domain.com")
        email_password = st.text_input("Password/App Password", type="password", key="email_password", help="Gunakan App Password untuk Gmail")
        
        if st.button("Simpan Konfigurasi Email", type="primary"):
            if email_address and email_password:
                st.session_state.email_credentials = {
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port,
                    'email': email_address,
                    'password': email_password
                }
                st.success("Konfigurasi email berhasil disimpan!")
            else:
                st.error("Mohon lengkapi semua field email")
    
    # Main content based on selected page
    if page == "Single Email Validation":
        single_email_validation()
    elif page == "Bulk Email Validation":
        from pages.bulk_validation import show_bulk_validation
        show_bulk_validation()
    elif page == "Email Discovery":
        from pages.email_discovery import show_email_discovery
        show_email_discovery()
    elif page == "Email Sender":
        email_sender_page()
    elif page == "Scheduled Emails":
        scheduled_emails_page()

def single_email_validation():
    st.markdown("""
    <div class="glass-card glowing">
        <h2 style="color: white; margin-top: 0; font-size: 2rem;"><i class="fas fa-search" style="margin-right: 0.5rem;"></i>Email Validator</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Use form to enable Enter key validation
        with st.form("email_validation_form"):
            email_to_validate = st.text_input("Enter email address to validate:", placeholder="example@domain.com")
            submitted = st.form_submit_button("Validate Email", type="primary")
            
            if submitted:
                if email_to_validate:
                    validator = EmailValidator()
                    
                    with st.spinner("Validating email..."):
                        result = validator.validate_single_email(email_to_validate)
                    
                    # Ultra modern results
                    if result['is_valid']:
                        st.markdown(f"""
                        <div class="success-card">
                            <h3 style="margin: 0; display: flex; align-items: center;"><i class="fas fa-check-circle" style="margin-right: 0.5rem;"></i>Valid Email!</h3>
                            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;"><strong>{email_to_validate}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="error-card">
                            <h3 style="margin: 0; display: flex; align-items: center;"><i class="fas fa-times-circle" style="margin-right: 0.5rem;"></i>Invalid Email</h3>
                            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.1rem;"><strong>{email_to_validate}</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="warning-card">
                        <p style="margin: 0; display: flex; align-items: center;"><i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem;"></i>Please enter an email address</p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: white; margin-top: 0; text-align: center;"><i class="fas fa-star" style="margin-right: 0.5rem;"></i>Features</h3>
            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5rem; margin-top: 1rem;">
                <span class="feature-pill"><i class="fas fa-spell-check"></i>Syntax</span>
                <span class="feature-pill"><i class="fas fa-globe"></i>Domain</span>
                <span class="feature-pill"><i class="fas fa-server"></i>MX Record</span>
                <span class="feature-pill"><i class="fas fa-plug"></i>SMTP</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def email_sender_page():
    st.markdown("""
    <div class="glass-card glowing">
        <h2 style="color: white; margin-top: 0; font-size: 2rem;"><i class="fas fa-paper-plane" style="margin-right: 0.5rem;"></i>Email Sender</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.email_credentials:
        st.markdown("""
        <div class="warning-card">
            <h3 style="margin: 0; display: flex; align-items: center;"><i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem;"></i>Setup Required</h3>
            <p style="margin: 0.5rem 0 0 0;">Configure your email credentials in the sidebar first.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Simplified composition header
    st.markdown("""
    <div class="glass-card">
        <h3 style="color: white; margin-top: 0;"><i class="fas fa-edit" style="margin-right: 0.5rem;"></i>Compose</h3>
    </div>
    """, unsafe_allow_html=True)
    
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
        st.markdown("""
        <div class="glass-card">
            <h3 style="color: white; margin-top: 0; text-align: center;"><i class="fas fa-chart-bar" style="margin-right: 0.5rem;"></i>Stats</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if recipients:
            st.markdown(f"""
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{len(recipients)}</div>
                    <div class="stat-label">Recipients</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(subject) if subject else 0}</div>
                    <div class="stat-label">Subject Chars</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(message) if message else 0}</div>
                    <div class="stat-label">Message Chars</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if 'last_send_status' in st.session_state:
            st.markdown("""
            <div class="glass-card">
                <h4 style="color: white; margin-top: 0;">Last Send Status</h4>
            </div>
            """, unsafe_allow_html=True)
            st.json(st.session_state.last_send_status)
    
    # Send button
    if st.button("Send Emails", type="primary", disabled=not (recipients and subject and message)):
        if recipients and subject and message:
            sender = EmailSender(st.session_state.email_credentials)
            
            if send_option == "Send now":
                with st.spinner("Sending emails..."):
                    results = sender.send_bulk_email(recipients, subject, message, is_html=(message_format == "HTML"))
                
                st.session_state.last_send_status = results
                
                # Show results with modern design
                successful = sum(1 for r in results if r['success'])
                failed = len(results) - successful
                
                st.markdown(f"""
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" style="color: #4facfe;">{successful}</div>
                        <div class="stat-label"><i class="fas fa-check" style="margin-right: 0.3rem;"></i>Sent</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" style="color: #fa709a;">{failed}</div>
                        <div class="stat-label"><i class="fas fa-times" style="margin-right: 0.3rem;"></i>Failed</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
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
