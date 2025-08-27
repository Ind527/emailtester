import streamlit as st
import pandas as pd
from utils.email_validator import EmailValidator
import time

def show_bulk_validation():
    st.header("Bulk Email Validation")
    st.markdown("Validate multiple email addresses at once using CSV upload or direct paste.")
    
    # Input method selection
    input_method = st.radio(
        "Choose input method:",
        ["Upload CSV File", "Paste Email Addresses"],
        horizontal=True
    )
    
    emails_to_validate = []
    
    if input_method == "Upload CSV File":
        # File upload section
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="Your CSV file should contain a column with email addresses"
        )
        
        if uploaded_file is not None:
            try:
                # Read CSV file
                df = pd.read_csv(uploaded_file)
                
                st.subheader("Data Preview")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Column selection
                st.subheader("Select Email Column")
                email_column = st.selectbox(
                    "Which column contains the email addresses?",
                    df.columns,
                    index=0 if 'email' not in [col.lower() for col in df.columns] 
                    else [col.lower() for col in df.columns].index('email')
                )
                
                # Preview selected emails
                if email_column:
                    emails_to_validate = df[email_column].dropna().unique().tolist()
                    st.info(f"Found {len(emails_to_validate)} unique email addresses to validate")
                    
                    with st.expander("Preview email addresses", expanded=False):
                        st.write(emails_to_validate[:20])  # Show first 20
                        if len(emails_to_validate) > 20:
                            st.write(f"... and {len(emails_to_validate) - 20} more")
            
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
                st.info("Make sure your CSV file is properly formatted and contains email addresses")
    
    elif input_method == "Paste Email Addresses":
        # Direct paste section
        st.subheader("Paste Email Addresses")
        
        email_text = st.text_area(
            "Enter email addresses (one per line):",
            height=200,
            placeholder="user1@example.com\nuser2@domain.com\nuser3@test.org\n...",
            help="Enter one email address per line"
        )
        
        if email_text:
            # Parse pasted emails
            raw_emails = [email.strip() for email in email_text.split('\n') if email.strip()]
            emails_to_validate = list(set(raw_emails))  # Remove duplicates
            
            st.info(f"Found {len(emails_to_validate)} unique email addresses to validate")
            
            with st.expander("Preview email addresses", expanded=False):
                st.write(emails_to_validate[:20])  # Show first 20
                if len(emails_to_validate) > 20:
                    st.write(f"... and {len(emails_to_validate) - 20} more")
    
    # Validation settings (common for both methods)
    if emails_to_validate:
        st.subheader("Validation Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            skip_smtp = st.checkbox(
                "Skip SMTP verification (faster)",
                value=False,
                help="SMTP verification is more accurate but slower"
            )
        
        with col2:
            batch_size = st.slider(
                "Batch size",
                min_value=10,
                max_value=100,
                value=50,
                help="Number of emails to validate at once"
            )
        
        # Start validation
        if st.button("Start Validation", type="primary"):
            if emails_to_validate:
                validate_emails(emails_to_validate, skip_smtp, batch_size)
            else:
                st.error("No valid email addresses found")

def validate_emails(emails, skip_smtp, batch_size):
    """Validate a list of emails with progress tracking"""
    
    validator = EmailValidator()
    
    # Initialize progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Results containers
    results_container = st.container()
    
    all_results = []
    total_emails = len(emails)
    
    # Process in batches
    for i in range(0, total_emails, batch_size):
        batch = emails[i:i + batch_size]
        batch_results = []
        
        for j, email in enumerate(batch):
            current_index = i + j + 1
            status_text.text(f"Validating email {current_index}/{total_emails}: {email}")
            
            # Validate email
            result = validator.validate_single_email(email)
            
            # Skip SMTP if requested
            if skip_smtp:
                result['smtp_valid'] = None
                # Recalculate confidence without SMTP
                confidence = 0
                if result['syntax_valid']: confidence += 35
                if result['domain_valid']: confidence += 35
                if result['mx_valid']: confidence += 30
                result['confidence'] = confidence
                result['is_valid'] = confidence >= 70
            
            batch_results.append(result)
            all_results.append(result)
            
            # Update progress
            progress = current_index / total_emails
            progress_bar.progress(progress)
            
            # Small delay to prevent overwhelming servers
            time.sleep(0.1)
        
        # Show intermediate results
        if len(all_results) % 50 == 0 or len(all_results) == total_emails:
            show_validation_results(all_results, results_container)
    
    # Final results
    status_text.success(f"Validation completed! Processed {len(all_results)} emails.")
    show_validation_results(all_results, results_container, final=True)

def show_validation_results(results, container, final=False):
    """Display validation results"""
    
    with container:
        if final:
            st.subheader("Final Validation Results")
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        valid_count = results_df['is_valid'].sum()
        invalid_count = len(results_df) - valid_count
        avg_confidence = results_df['confidence'].mean()
        syntax_valid = results_df['syntax_valid'].sum()
        
        col1.metric("Valid Emails", valid_count, f"{valid_count/len(results_df)*100:.1f}%")
        col2.metric("Invalid Emails", invalid_count, f"{invalid_count/len(results_df)*100:.1f}%")
        col3.metric("Avg Confidence", f"{avg_confidence:.1f}%")
        col4.metric("Syntax Valid", syntax_valid, f"{syntax_valid/len(results_df)*100:.1f}%")
        
        # Filter options
        if final:
            st.subheader("Filter Results")
            filter_option = st.selectbox(
                "Show emails:",
                ["All emails", "Valid emails only", "Invalid emails only", "High confidence (>80%)", "Low confidence (<50%)"]
            )
            
            if filter_option == "Valid emails only":
                display_df = results_df[results_df['is_valid'] == True]
            elif filter_option == "Invalid emails only":
                display_df = results_df[results_df['is_valid'] == False]
            elif filter_option == "High confidence (>80%)":
                display_df = results_df[results_df['confidence'] > 80]
            elif filter_option == "Low confidence (<50%)":
                display_df = results_df[results_df['confidence'] < 50]
            else:
                display_df = results_df
            
            # Sort by confidence
            if 'confidence' in display_df.columns:
                display_df = display_df.sort_values('confidence', ascending=False)
        else:
            display_df = results_df
        
        # Display results table
        st.dataframe(
            display_df[['email', 'is_valid', 'confidence', 'syntax_valid', 'domain_valid', 'mx_valid', 'smtp_valid']],
            use_container_width=True
        )
        
        if final:
            # Export options
            st.subheader("Export Results")
            
            col1, col2 = st.columns(2)
            
            # Only export valid emails (remove invalid ones)
            valid_emails_df = results_df[results_df['is_valid'] == True]
            
            if not valid_emails_df.empty:
                # Create simple CSV with only valid emails
                valid_emails_series = valid_emails_df['email']
                valid_csv = valid_emails_series.to_csv(index=False, header=True)
                
                st.download_button(
                    label="Download Valid Emails (CSV)",
                    data=valid_csv,
                    file_name=f"valid_emails_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                st.info(f"{len(valid_emails_df)} valid emails ready for download (invalid emails excluded)")
            else:
                st.info("No valid emails found to export")

if __name__ == "__main__":
    show_bulk_validation()
