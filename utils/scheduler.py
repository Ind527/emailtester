import json
import os
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import uuid
import threading
import time
from utils.email_sender import EmailSender

class EmailScheduler:
    def __init__(self):
        self.jobs_file = "scheduled_jobs.json"
        self.jobs = self._load_jobs()
        self.running = False
        self._start_scheduler_thread()
    
    def _load_jobs(self) -> List[Dict]:
        """Load scheduled jobs from file"""
        if os.path.exists(self.jobs_file):
            try:
                with open(self.jobs_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []
    
    def _save_jobs(self):
        """Save jobs to file"""
        with open(self.jobs_file, 'w') as f:
            json.dump(self.jobs, f, indent=2, default=str)
    
    def schedule_email(self, recipients: List[str], subject: str, message: str, 
                      scheduled_time: pd.Timestamp, credentials: Dict, 
                      is_html: bool = False) -> str:
        """
        Schedule an email to be sent at a specific time
        """
        job_id = str(uuid.uuid4())[:8]
        
        job = {
            'id': job_id,
            'recipients': recipients,
            'subject': subject,
            'message': message,
            'scheduled_time': scheduled_time.isoformat(),
            'credentials': credentials,
            'is_html': is_html,
            'status': 'pending',
            'created_time': datetime.now().isoformat(),
            'sent_time': None,
            'success_count': 0,
            'total_count': len(recipients),
            'results': []
        }
        
        self.jobs.append(job)
        self._save_jobs()
        
        return job_id
    
    def get_scheduled_jobs(self) -> List[Dict]:
        """Get all scheduled jobs"""
        # Reload from file to get latest status
        self.jobs = self._load_jobs()
        return self.jobs
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job"""
        for job in self.jobs:
            if job['id'] == job_id and job['status'] == 'pending':
                job['status'] = 'cancelled'
                self._save_jobs()
                return True
        return False
    
    def clear_completed_jobs(self):
        """Remove completed and cancelled jobs"""
        self.jobs = [job for job in self.jobs if job['status'] in ['pending', 'sending']]
        self._save_jobs()
    
    def _start_scheduler_thread(self):
        """Start the background scheduler thread"""
        if not self.running:
            self.running = True
            thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            thread.start()
    
    def _scheduler_loop(self):
        """Main scheduler loop - runs in background thread"""
        while self.running:
            try:
                current_time = datetime.now()
                self.jobs = self._load_jobs()  # Reload from file
                
                for job in self.jobs:
                    if job['status'] == 'pending':
                        scheduled_time = pd.Timestamp(job['scheduled_time']).to_pydatetime()
                        
                        if current_time >= scheduled_time:
                            self._execute_job(job)
                
                # Check every 30 seconds
                time.sleep(30)
                
            except Exception as e:
                print(f"Scheduler error: {str(e)}")
                time.sleep(60)  # Wait longer on error
    
    def _execute_job(self, job: Dict):
        """Execute a scheduled email job"""
        try:
            job['status'] = 'sending'
            self._save_jobs()
            
            # Create email sender
            sender = EmailSender(job['credentials'])
            
            # Send emails
            results = sender.send_bulk_email(
                job['recipients'],
                job['subject'],
                job['message'],
                job['is_html']
            )
            
            # Update job status
            successful_sends = sum(1 for r in results if r['success'])
            
            job['status'] = 'completed'
            job['sent_time'] = datetime.now().isoformat()
            job['success_count'] = successful_sends
            job['results'] = results
            
            self._save_jobs()
            
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
            job['sent_time'] = datetime.now().isoformat()
            self._save_jobs()

# Global scheduler instance
_scheduler_instance = None

def get_scheduler() -> EmailScheduler:
    """Get global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = EmailScheduler()
    return _scheduler_instance
