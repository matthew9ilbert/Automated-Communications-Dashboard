import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from models import Reminder, Task, CalendarEvent, db
from message_scanner import message_scanner
from config import Config

logger = logging.getLogger(__name__)

class SchedulerService:
    """Service for managing scheduled tasks"""
    
    def __init__(self, app):
        self.app = app
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Schedule message scanning
        self.scheduler.add_job(
            func=self.scan_messages_job,
            trigger=IntervalTrigger(minutes=Config.SCAN_INTERVAL_MINUTES),
            id='message_scanner',
            name='Scan incoming messages',
            replace_existing=True
        )
        
        # Schedule reminder checking
        self.scheduler.add_job(
            func=self.check_reminders_job,
            trigger=IntervalTrigger(minutes=5),  # Check every 5 minutes
            id='reminder_checker',
            name='Check pending reminders',
            replace_existing=True
        )
        
        logger.info("Scheduler initialized with message scanning and reminder checking")
    
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
                    self.process_reminder(reminder)
                
                if pending_reminders:
                    logger.info(f"Processed {len(pending_reminders)} pending reminders")
                
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
    
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
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")

def init_scheduler(app):
    """Initialize the scheduler with the Flask app"""
    scheduler_service = SchedulerService(app)
    
    # Store reference to scheduler in app for cleanup
    app.scheduler_service = scheduler_service
    
    return scheduler_service
