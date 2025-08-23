import streamlit as st
import pandas as pd
from utils.scheduler import get_scheduler
from datetime import datetime
import json

def show_scheduled_emails():
    st.header("⏰ Scheduled Email Management")
    st.markdown("View, manage, and monitor your scheduled email campaigns.")
    
    scheduler = get_scheduler()
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col2:
        if st.button("🧹 Clear Completed"):
            scheduler.clear_completed_jobs()
            st.success("Completed jobs cleared!")
            st.rerun()
    
    # Get all scheduled jobs
    jobs = scheduler.get_scheduled_jobs()
    
    if not jobs:
        st.info("📭 No scheduled emails found.")
        
        # Quick scheduling section
        st.subheader("⚡ Quick Schedule")
        st.markdown("Go to the **Email Sender** page to create new scheduled emails.")
        
        return
    
    # Statistics overview
    show_job_statistics(jobs)
    
    # Jobs management interface
    st.subheader("📋 Scheduled Jobs")
    
    # Filter options
    status_filter = st.selectbox(
        "Filter by status:",
        ["All", "Pending", "Sending", "Completed", "Failed", "Cancelled"]
    )
    
    filtered_jobs = jobs
    if status_filter != "All":
        filtered_jobs = [job for job in jobs if job['status'].lower() == status_filter.lower()]
    
    if not filtered_jobs:
        st.info(f"No jobs with status '{status_filter}' found.")
        return
    
    # Display jobs
    for job in filtered_jobs:
        display_job_card(job, scheduler)

def show_job_statistics(jobs):
    """Display job statistics overview"""
    st.subheader("📊 Overview")
    
    # Calculate statistics
    total_jobs = len(jobs)
    pending_jobs = sum(1 for job in jobs if job['status'] == 'pending')
    completed_jobs = sum(1 for job in jobs if job['status'] == 'completed')
    failed_jobs = sum(1 for job in jobs if job['status'] == 'failed')
    cancelled_jobs = sum(1 for job in jobs if job['status'] == 'cancelled')
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📧 Total Jobs", total_jobs)
    
    with col2:
        st.metric("⏳ Pending", pending_jobs)
    
    with col3:
        st.metric("✅ Completed", completed_jobs)
    
    with col4:
        st.metric("❌ Failed", failed_jobs)
    
    with col5:
        st.metric("⏸️ Cancelled", cancelled_jobs)
    
    # Success rate
    if completed_jobs > 0:
        total_emails_sent = sum(job.get('success_count', 0) for job in jobs if job['status'] == 'completed')
        total_emails_attempted = sum(job.get('total_count', 0) for job in jobs if job['status'] == 'completed')
        
        if total_emails_attempted > 0:
            success_rate = (total_emails_sent / total_emails_attempted) * 100
            st.metric("📈 Overall Success Rate", f"{success_rate:.1f}%")

def display_job_card(job, scheduler):
    """Display individual job card"""
    
    # Status emoji mapping
    status_emojis = {
        'pending': '⏳',
        'sending': '📤',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '⏸️'
    }
    
    status_emoji = status_emojis.get(job['status'], '❓')
    
    # Job card container
    with st.container():
        # Header
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {status_emoji} {job['subject']}")
            st.caption(f"Job ID: {job['id']}")
        
        with col2:
            st.markdown(f"**Status:** {job['status'].title()}")
        
        with col3:
            if job['status'] == 'pending':
                if st.button(f"❌ Cancel", key=f"cancel_{job['id']}"):
                    if scheduler.cancel_job(job['id']):
                        st.success("Job cancelled!")
                        st.rerun()
                    else:
                        st.error("Failed to cancel job")
        
        # Job details
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Recipients:** {job['total_count']}")
            st.write(f"**Created:** {format_datetime(job['created_time'])}")
        
        with col2:
            st.write(f"**Scheduled for:** {format_datetime(job['scheduled_time'])}")
            if job.get('sent_time'):
                st.write(f"**Sent at:** {format_datetime(job['sent_time'])}")
        
        with col3:
            if job['status'] == 'completed':
                st.write(f"**Success rate:** {job.get('success_count', 0)}/{job['total_count']}")
                success_rate = (job.get('success_count', 0) / job['total_count']) * 100
                st.progress(success_rate / 100)
            elif job['status'] == 'failed':
                st.write(f"**Error:** {job.get('error', 'Unknown error')}")
        
        # Expandable details
        with st.expander(f"📋 Details for Job {job['id']}", expanded=False):
            
            # Email content preview
            st.markdown("**Email Preview:**")
            if job.get('is_html', False):
                # For HTML, show raw HTML (could be improved with HTML renderer)
                with st.container():
                    st.code(job['message'][:500] + "..." if len(job['message']) > 500 else job['message'], language='html')
            else:
                st.text(job['message'][:300] + "..." if len(job['message']) > 300 else job['message'])
            
            # Recipients list
            st.markdown("**Recipients:**")
            recipients_text = "\n".join(job['recipients'][:10])
            if len(job['recipients']) > 10:
                recipients_text += f"\n... and {len(job['recipients']) - 10} more"
            st.text(recipients_text)
            
            # Results details (if completed)
            if job['status'] == 'completed' and job.get('results'):
                st.markdown("**Sending Results:**")
                
                # Convert results to DataFrame for better display
                results_df = pd.DataFrame(job['results'])
                
                # Summary
                success_count = results_df['success'].sum()
                total_count = len(results_df)
                
                st.write(f"✅ Successful: {success_count}/{total_count}")
                
                # Show failed sends
                failed_results = results_df[results_df['success'] == False]
                if not failed_results.empty:
                    st.write("❌ **Failed sends:**")
                    for _, failed in failed_results.iterrows():
                        st.write(f"  - {failed['recipient']}: {failed.get('error', 'Unknown error')}")
            
            # Raw job data (for debugging)
            if st.checkbox(f"Show raw data for job {job['id']}", key=f"raw_{job['id']}"):
                st.json(job)
        
        st.markdown("---")

def format_datetime(datetime_str):
    """Format datetime string for display"""
    if not datetime_str:
        return "Not set"
    
    try:
        dt = pd.Timestamp(datetime_str)
        # Check if timestamp is valid
        if pd.isna(dt) or str(dt) == 'NaT':
            return "Not set"
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(datetime_str) if datetime_str else "Not set"

def show_job_logs():
    """Show detailed logs for job execution"""
    st.subheader("📜 Job Execution Logs")
    
    # This could be expanded to show more detailed logs
    # For now, we'll just show basic information
    
    if st.button("📥 Download Job History"):
        scheduler = get_scheduler()
        jobs = scheduler.get_scheduled_jobs()
        
        # Convert to DataFrame
        df = pd.DataFrame(jobs)
        
        if not df.empty:
            # Select relevant columns
            export_columns = ['id', 'subject', 'total_count', 'status', 
                            'scheduled_time', 'sent_time', 'success_count']
            
            export_df = df[export_columns]
            csv_data = export_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"scheduled_jobs_history_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No job history to export")

if __name__ == "__main__":
    show_scheduled_emails()
