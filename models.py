from datetime import datetime
from app import db
from sqlalchemy import Text, DateTime, String, Integer, Boolean, Index, SmallInteger, JSON, CheckConstraint
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Message(db.Model):
    """Model for storing incoming messages"""
    __tablename__ = 'message'
    
    id = db.Column(Integer, primary_key=True)
    sender = db.Column(String(100), nullable=False, index=True)
    content = db.Column(Text, nullable=False)
    summary = db.Column(Text)
    source = db.Column(String(20), nullable=False, index=True)
    priority = db.Column(String(10), default='Low', index=True)
    processed = db.Column(Boolean, default=False, index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_message_priority_processed', 'priority', 'processed'),
        Index('idx_message_created_priority', 'created_at', 'priority'),
        CheckConstraint("priority IN ('High', 'Medium', 'Low')"),
        CheckConstraint("source IN ('text', 'email', 'teams', 'notes', 'api', 'voice_memo', 'voicemail', 'imessage')")
    )
    
    def __repr__(self) -> str:
        return f'<Message {self.id}: {self.sender} - {self.priority}>'
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for API responses"""
        return {
            'id': self.id,
            'sender': self.sender,
            'content': self.content,
            'summary': self.summary,
            'source': self.source,
            'priority': self.priority,
            'processed': self.processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Task(db.Model):
    """Model for managing tasks"""
    __tablename__ = 'task'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(100), nullable=False, index=True)
    description = db.Column(Text)
    facility = db.Column(String(50), nullable=False, index=True)
    priority = db.Column(String(10), default='Medium', index=True)
    status = db.Column(String(20), default='Not Started', index=True)
    assigned_to = db.Column(String(50), index=True)
    due_date = db.Column(DateTime, index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_id = db.Column(Integer, db.ForeignKey('message.id', ondelete='SET NULL'))
    
    # Relationships
    source_message = db.relationship('Message', backref='created_tasks', foreign_keys=[message_id])
    
    __table_args__ = (
        Index('idx_task_status_facility', 'status', 'facility'),
        Index('idx_task_priority_status', 'priority', 'status'),
        Index('idx_task_assigned_status', 'assigned_to', 'status'),
        CheckConstraint("priority IN ('High', 'Medium', 'Low')"),
        CheckConstraint("status IN ('Not Started', 'In Progress', 'Completed', 'Cancelled')")
    )
    
    def __repr__(self) -> str:
        return f'<Task {self.id}: {self.title} - {self.status}>'
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'facility': self.facility,
            'priority': self.priority,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CalendarEvent(db.Model):
    """Model for calendar events"""
    __tablename__ = 'calendar_event'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(100), nullable=False)
    description = db.Column(Text)
    start_time = db.Column(DateTime, nullable=False, index=True)
    end_time = db.Column(DateTime, nullable=False, index=True)
    location = db.Column(String(100))
    facility = db.Column(String(50))
    google_event_id = db.Column(String(100))
    outlook_event_id = db.Column(String(100))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    message_id = db.Column(Integer, db.ForeignKey('message.id'))
    
    def __repr__(self) -> str:
        return f'<CalendarEvent {self.id}: {self.title}>'

class StaffMember(db.Model):
    """Model for staff members"""
    __tablename__ = 'staff_member'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    email = db.Column(String(100))
    phone = db.Column(String(20))
    facilities = db.Column(JSON)
    active = db.Column(Boolean, default=True, index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self) -> str:
        return f'<StaffMember {self.id}: {self.name}>'

class StaffAssignment(db.Model):
    """Model for tracking staff coverage history"""
    __tablename__ = 'staff_assignment'
    
    id = db.Column(Integer, primary_key=True)
    staff_id = db.Column(Integer, db.ForeignKey('staff_member.id'), nullable=False)
    facility = db.Column(String(50), nullable=False)
    assignment_date = db.Column(DateTime, nullable=False, index=True)
    assignment_type = db.Column(String(20))
    notes = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    staff_member = db.relationship('StaffMember', backref='assignments')
    
    __table_args__ = (
        CheckConstraint("assignment_type IN ('Coverage', 'Regular', 'Emergency')"),
    )
    
    def __repr__(self) -> str:
        return f'<StaffAssignment {self.id}: {self.staff_member.name if self.staff_member else "Unknown"} - {self.facility}>'

class Announcement(db.Model):
    """Model for team announcements"""
    __tablename__ = 'announcement'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(100), nullable=False)
    content = db.Column(Text, nullable=False)
    facilities = db.Column(JSON)
    announcement_type = db.Column(String(20), default='General')
    active = db.Column(Boolean, default=True, index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    expires_at = db.Column(DateTime, index=True)
    
    __table_args__ = (
        CheckConstraint("announcement_type IN ('Assignment', 'Reminder', 'General', 'Emergency')"),
    )
    
    def __repr__(self) -> str:
        return f'<Announcement {self.id}: {self.title}>'

class Reminder(db.Model):
    """Model for smart reminders"""
    __tablename__ = 'reminder'
    
    id = db.Column(Integer, primary_key=True)
    task_id = db.Column(Integer, db.ForeignKey('task.id'))
    event_id = db.Column(Integer, db.ForeignKey('calendar_event.id'))
    reminder_text = db.Column(String(200), nullable=False)
    next_reminder = db.Column(DateTime, nullable=False, index=True)
    acknowledged = db.Column(Boolean, default=False, index=True)
    reminder_count = db.Column(SmallInteger, default=0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = db.relationship('Task', backref='reminders')
    event = db.relationship('CalendarEvent', backref='reminders')
    
    def __repr__(self) -> str:
        return f'<Reminder {self.id}: {"Task" if self.task_id else "Event"} - {"Ack" if self.acknowledged else "Pending"}>'
