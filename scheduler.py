import logging
import time
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from apscheduler.executors.pool import ThreadPoolExecutor
from models import Reminder, Task, CalendarEvent, db
from message_scanner import message_scanner
from config import Config

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for managing scheduled tasks"""
    
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler(
            executors={
                'default': ThreadPoolExecutor(20)
            },
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 60
            }
        )
        
        # Add event listeners
        self.scheduler.add_listener(self._job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        
        # Start the scheduler
        self.scheduler.start()
        
        # Schedule message scanning
        self.scheduler.add_job(
            func=self.scan_messages_job,
            trigger=IntervalTrigger(minutes=Config.SCAN_INTERVAL_MINUTES),
            id='message_scanner',
            name='Scan incoming messages',
            replace_existing=True,
            max_instances=1
        )
        
        # Schedule reminder checking
        self.scheduler.add_job(
            func=self.check_reminders_job,
            trigger=IntervalTrigger(minutes=5),  # Check every 5 minutes
            id='reminder_checker',
            name='Check pending reminders',
            replace_existing=True,
            max_instances=1
        )
        
        logger.info("Scheduler initialized with message scanning and reminder checking")
    
    def _job_listener(self, event):
        """Handle scheduler events"""
        if event.exception:
            logger.error(f'Job {event.job_id} failed: {event.exception}')
            logger.error(f'Traceback: {event.traceback}')
        else:
            logger.debug(f'Job {event.job_id} executed successfully')
    
    def scan_messages_job(self):
        """Scheduled job to scan for new messages"""
        try:
            with self.app.app_context():
                logger.info("Starting scheduled message scan")
                results = message_scanner.scan_incoming_messages()
                
                # Process any identified actions
                for result in results:
                    self.process_message_actions(result)
                
                logger.info(f"Completed message scan, processed {len(results)} messages")
                
        except Exception as e:
            logger.error(f"Error in scheduled message scan: {e}")
            # Attempt recovery
            self._handle_scan_error(e)
    
    def _handle_scan_error(self, error):
        """Handle message scanning errors"""
        try:
            # Log the error
            logger.error(f"Message scanning error: {str(error)}")
            
            # Attempt to recover database connection
            try:
                db.session.rollback()
            except Exception as db_error:
                logger.error(f"Database recovery failed: {str(db_error)}")
            
            # Wait before retrying
            time.sleep(5)
            
        except Exception as recovery_error:
            logger.error(f"Error recovery failed: {str(recovery_error)}")
    
    def process_message_actions(self, processing_result: dict):
        """Process actions identified from message scanning"""
        try:
            message_id = processing_result['message_id']
            actions = processing_result['actions']
            
            for action in actions:
                if action['type'] == 'task':
                    # Create task
                    task = Task(
                        title=action['title'],
                        description=action['description'],
                        facility=action['facility'],
                        priority=action['priority'],
                        message_id=message_id
                    )
                    db.session.add(task)
                    
                    # Create reminder for high priority tasks
                    if action['priority'] == 'High':
                        reminder = Reminder(
                            task=task,
                            reminder_text=f"High priority task: {action['title']}",
                            next_reminder=datetime.now() + timedelta(minutes=30)
                        )
                        db.session.add(reminder)
                
                elif action['type'] == 'event':
                    # Create calendar event
                    event = CalendarEvent(
                        title=action['title'],
                        description=action['description'],
                        start_time=action['start_time'],
                        end_time=action['end_time'],
                        location=action['location'],
                        facility=action.get('facility', 'Bellevue Medical Center'),
                        message_id=message_id
                    )
                    db.session.add(event)
                    
                    # Create reminder 30 minutes before event
                    reminder_time = action['start_time'] - timedelta(minutes=30)
                    if reminder_time > datetime.now():
                        reminder = Reminder(
                            event=event,
                            reminder_text=f"Upcoming event: {action['title']}",
                            next_reminder=reminder_time
                        )
                        db.session.add(reminder)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error processing message actions: {e}")
            db.session.rollback()
            raise
    
    def check_reminders_job(self):
        """Scheduled job to check for pending reminders"""
        try:
            with self.app.app_context():
                now = datetime.now()
                
                # Get pending reminders that are due
                pending_reminders = Reminder.query.filter(
                    Reminder.acknowledged == False,
                    Reminder.next_reminder <= now
                ).all()
                
                for reminder in pending_reminders:
                    try:
                        self.process_reminder(reminder)
                    except Exception as reminder_error:
                        logger.error(f"Error processing reminder {reminder.id}: {reminder_error}")
                        continue
                
                if pending_reminders:
                    logger.info(f"Processed {len(pending_reminders)} pending reminders")
                
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
            # Attempt recovery
            self._handle_reminder_error(e)
    
    def _handle_reminder_error(self, error):
        """Handle reminder checking errors"""
        try:
            # Log the error
            logger.error(f"Reminder checking error: {str(error)}")
            
            # Attempt to recover database connection
            try:
                db.session.rollback()
            except Exception as db_error:
                logger.error(f"Database recovery failed: {str(db_error)}")
            
            # Wait before retrying
            time.sleep(5)
            
        except Exception as recovery_error:
            logger.error(f"Error recovery failed: {str(recovery_error)}")
    
    def process_reminder(self, reminder: Reminder):
        """Process a single reminder"""
        try:
            # Increment reminder count
            reminder.reminder_count += 1
            
            # Set next reminder time (every 30 minutes)
            reminder.next_reminder = datetime.now() + timedelta(minutes=Config.REMINDER_INTERVAL_MINUTES)
            
            # If it's been reminded too many times, reduce frequency
            if reminder.reminder_count > 5:
                reminder.next_reminder = datetime.now() + timedelta(hours=2)
            
            db.session.commit()
            
            # Log the reminder (in a real implementation, this would trigger a notification)
            logger.info(f"Reminder triggered: {reminder.reminder_text}")
            
        except Exception as e:
            logger.error(f"Error processing reminder {reminder.id}: {e}")
            db.session.rollback()
            raise
    
    def shutdown(self):
        """Shutdown the scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("Scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {e}")

def init_scheduler(app):
    """Initialize the scheduler with the Flask app"""
    try:
        scheduler_service = SchedulerService(app)
        
        # Store reference to scheduler in app for cleanup
        app.scheduler_service = scheduler_service
        
        return scheduler_service
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        raise
