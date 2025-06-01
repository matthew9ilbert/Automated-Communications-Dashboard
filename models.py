from datetime import datetime
from app import db
from sqlalchemy import Text, DateTime, String, Integer, Boolean, Index

class Message(db.Model):
    """Model for storing incoming messages"""
    __tablename__ = 'message'
    
    id = db.Column(Integer, primary_key=True)
    sender = db.Column(String(255), nullable=False, index=True)
    content = db.Column(Text, nullable=False)
    source = db.Column(String(50), nullable=False, index=True)  # 'text', 'email', 'teams', 'notes'
    priority = db.Column(String(20), default='Low', index=True)  # 'High', 'Medium', 'Low'
    processed = db.Column(Boolean, default=False, index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_message_priority_processed', 'priority', 'processed'),
        Index('idx_message_created_priority', 'created_at', 'priority'),
    )
    
    def __repr__(self):
        return f'<Message {self.id}: {self.sender} - {self.priority}>'
        
    def to_dict(self):
        """Convert message to dictionary for API responses"""
        return {
            'id': self.id,
            'sender': self.sender,
            'content': self.content,
            'source': self.source,
            'priority': self.priority,
            'processed': self.processed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    """Model for managing tasks"""
    __tablename__ = 'task'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(255), nullable=False, index=True)
    description = db.Column(Text)
    facility = db.Column(String(100), nullable=False, index=True)
    priority = db.Column(String(20), default='Medium', index=True)
    status = db.Column(String(50), default='Not Started', index=True)  # 'Not Started', 'In Progress', 'Completed'
    assigned_to = db.Column(String(100), index=True)
    due_date = db.Column(DateTime, index=True)
    created_at = db.Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_id = db.Column(Integer, db.ForeignKey('message.id', ondelete='SET NULL'))
    
    # Relationships
    source_message = db.relationship('Message', backref='created_tasks', foreign_keys=[message_id])
    
    # Add indexes for better query performance
    __table_args__ = (
        Index('idx_task_status_facility', 'status', 'facility'),
        Index('idx_task_priority_status', 'priority', 'status'),
        Index('idx_task_assigned_status', 'assigned_to', 'status'),
    )
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title} - {self.status}>'
        
    def to_dict(self):
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
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(255), nullable=False)
    description = db.Column(Text)
    start_time = db.Column(DateTime, nullable=False)
    end_time = db.Column(DateTime, nullable=False)
    location = db.Column(String(255))
    facility = db.Column(String(100))
    google_event_id = db.Column(String(255))
    outlook_event_id = db.Column(String(255))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    message_id = db.Column(Integer, db.ForeignKey('message.id'))
    
    def __repr__(self):
        return f'<CalendarEvent {self.id}: {self.title}>'

class StaffMember(db.Model):
    """Model for staff members"""
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(100), nullable=False)
    email = db.Column(String(120))
    phone = db.Column(String(20))
    facilities = db.Column(String(500))  # JSON string of facility assignments
    active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<StaffMember {self.id}: {self.name}>'

class StaffAssignment(db.Model):
    """Model for tracking staff coverage history"""
    id = db.Column(Integer, primary_key=True)
    staff_id = db.Column(Integer, db.ForeignKey('staff_member.id'), nullable=False)
    facility = db.Column(String(100), nullable=False)
    assignment_date = db.Column(DateTime, nullable=False)
    assignment_type = db.Column(String(100))  # 'Coverage', 'Regular', 'Emergency'
    notes = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    staff_member = db.relationship('StaffMember', backref='assignments')
    
    def __repr__(self):
        return f'<StaffAssignment {self.id}: {self.staff_member.name if self.staff_member else "Unknown"} - {self.facility}>'

class Announcement(db.Model):
    """Model for team announcements"""
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(255), nullable=False)
    content = db.Column(Text, nullable=False)
    facilities = db.Column(String(500))  # JSON string of target facilities
    announcement_type = db.Column(String(50), default='General')  # 'Assignment', 'Reminder', 'General'
    active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    expires_at = db.Column(DateTime)
    
    def __repr__(self):
        return f'<Announcement {self.id}: {self.title}>'

class Reminder(db.Model):
    """Model for smart reminders"""
    id = db.Column(Integer, primary_key=True)
    task_id = db.Column(Integer, db.ForeignKey('task.id'))
    event_id = db.Column(Integer, db.ForeignKey('calendar_event.id'))
    reminder_text = db.Column(String(500), nullable=False)
    next_reminder = db.Column(DateTime, nullable=False)
    acknowledged = db.Column(Boolean, default=False)
    reminder_count = db.Column(Integer, default=0)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    task = db.relationship('Task', backref='reminders')
    event = db.relationship('CalendarEvent', backref='reminders')
    
    def __repr__(self):
        return f'<Reminder {self.id}: {"Task" if self.task_id else "Event"} - {"Ack" if self.acknowledged else "Pending"}>'
