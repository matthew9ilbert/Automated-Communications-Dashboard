import logging
from datetime import datetime, timedelta
import os
from flask import render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from models import Message, Task, CalendarEvent, StaffMember, StaffAssignment, Announcement, Reminder, db
from google_services import sheets_service, calendar_service
from microsoft_services import graph_service
from message_scanner import message_scanner
from ai_services import ai_services
from config import Config

logger = logging.getLogger(__name__)

def register_routes(app):
    """Register all application routes"""
    
    @app.route('/')
    def dashboard():
        """Main dashboard view"""
        try:
            # Get recent high priority messages
            high_priority_messages = Message.query.filter_by(priority='High').order_by(Message.created_at.desc()).limit(10).all()
            
            # Get pending tasks
            pending_tasks = Task.query.filter(Task.status.in_(['Not Started', 'In Progress'])).order_by(Task.created_at.desc()).limit(15).all()
            
            # Analyze task dependencies
            task_dependencies = ai_services.analyze_task_dependencies(pending_tasks)
            
            # Get upcoming events
            upcoming_events = CalendarEvent.query.filter(CalendarEvent.start_time >= datetime.now()).order_by(CalendarEvent.start_time).limit(10).all()
            
            # Get recent announcements
            recent_announcements = Announcement.query.filter_by(active=True).order_by(Announcement.created_at.desc()).limit(8).all()
            
            # Get pending reminders
            pending_reminders = Reminder.query.filter_by(acknowledged=False).order_by(Reminder.next_reminder).limit(5).all()
            
            # Calculate statistics
            stats = {
                'total_tasks': Task.query.count(),
                'pending_tasks': Task.query.filter(Task.status.in_(['Not Started', 'In Progress'])).count(),
                'high_priority_messages': Message.query.filter_by(priority='High', processed=False).count(),
                'upcoming_events': CalendarEvent.query.filter(CalendarEvent.start_time >= datetime.now()).count()
            }
            
            return render_template('dashboard.html',
                                 high_priority_messages=high_priority_messages,
                                 pending_tasks=pending_tasks,
                                 task_dependencies=task_dependencies,
                                 upcoming_events=upcoming_events,
                                 recent_announcements=recent_announcements,
                                 pending_reminders=pending_reminders,
                                 stats=stats,
                                 facilities=Config.FACILITIES,
                                 now=datetime.now())
        except SQLAlchemyError as e:
            logger.error(f"Database error loading dashboard: {str(e)}")
            db.session.rollback()
            flash('Database error while loading dashboard data', 'error')
            return render_template('dashboard.html', stats={}, facilities=Config.FACILITIES, now=datetime.now())
        except Exception as e:
            logger.error(f"Error loading dashboard: {str(e)}")
            flash('Error loading dashboard data', 'error')
            return render_template('dashboard.html', stats={}, facilities=Config.FACILITIES, now=datetime.now())
    
    @app.route('/messages')
    def messages():
        """Messages management view"""
        try:
            page = request.args.get('page', 1, type=int)
            priority_filter = request.args.get('priority', '')
            source_filter = request.args.get('source', '')
            
            query = Message.query
            
            if priority_filter:
                query = query.filter_by(priority=priority_filter)
            if source_filter:
                query = query.filter_by(source=source_filter)
            
            messages_paginated = query.order_by(Message.created_at.desc()).paginate(
                page=page, per_page=20, error_out=False
            )
            
            return render_template('messages.html', 
                                 messages=messages_paginated,
                                 priority_filter=priority_filter,
                                 source_filter=source_filter)
        except SQLAlchemyError as e:
            logger.error(f"Database error loading messages: {str(e)}")
            db.session.rollback()
            flash('Database error while loading messages', 'error')
            return render_template('messages.html', messages=None)
        except Exception as e:
            logger.error(f"Error loading messages: {str(e)}")
            flash('Error loading messages', 'error')
            return render_template('messages.html', messages=None)
    
    @app.route('/tasks')
    def tasks():
        """Tasks management view"""
        try:
            facility_filter = request.args.get('facility', '')
            status_filter = request.args.get('status', '')
            priority_filter = request.args.get('priority', '')
            
            query = Task.query
            
            if facility_filter:
                query = query.filter_by(facility=facility_filter)
            if status_filter:
                # Handle comma-separated status values
                if ',' in status_filter:
                    status_list = [s.strip() for s in status_filter.split(',')]
                    query = query.filter(Task.status.in_(status_list))
                else:
                    query = query.filter_by(status=status_filter)
            if priority_filter:
                query = query.filter_by(priority=priority_filter)
            
            tasks = query.order_by(Task.created_at.desc()).all()
            
            return render_template('tasks.html', 
                                 tasks=tasks,
                                 facilities=Config.FACILITIES,
                                 facility_filter=facility_filter,
                                 status_filter=status_filter,
                                 priority_filter=priority_filter)
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            flash('Error loading tasks', 'error')
            return render_template('tasks.html', tasks=[], facilities=Config.FACILITIES)
    
    @app.route('/calendar')
    def calendar():
        """Calendar management view"""
        try:
            events = CalendarEvent.query.order_by(CalendarEvent.start_time).all()
            return render_template('calendar.html', events=events, facilities=Config.FACILITIES)
        except Exception as e:
            logger.error(f"Error loading calendar: {e}")
            flash('Error loading calendar', 'error')
            return render_template('calendar.html', events=[], facilities=Config.FACILITIES)
    
    @app.route('/staff')
    def staff():
        """Staff management view"""
        try:
            staff_members = StaffMember.query.filter_by(active=True).all()
            recent_assignments = StaffAssignment.query.order_by(StaffAssignment.assignment_date.desc()).limit(10).all()
            
            return render_template('staff.html', 
                                 staff_members=staff_members,
                                 recent_assignments=recent_assignments,
                                 facilities=Config.FACILITIES)
        except Exception as e:
            logger.error(f"Error loading staff: {e}")
            flash('Error loading staff data', 'error')
            return render_template('staff.html', staff_members=[], recent_assignments=[], facilities=Config.FACILITIES)
    
    @app.route('/integrations')
    def integrations():
        """Integrations management view"""
        try:
            return render_template('integrations.html', facilities=Config.FACILITIES)
        except Exception as e:
            logger.error(f"Error loading integrations: {e}")
            flash('Error loading integrations page', 'error')
            return render_template('integrations.html', facilities=Config.FACILITIES)
    
    @app.route('/announcements')
    def announcements():
        """Announcements management view"""
        try:
            announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
            return render_template('announcements.html', announcements=announcements, facilities=Config.FACILITIES)
        except Exception as e:
            logger.error(f"Error loading announcements: {e}")
            flash('Error loading announcements', 'error')
            return render_template('announcements.html', announcements=[], facilities=Config.FACILITIES)
    
    # API endpoints for iOS Shortcut integration
    @app.route('/api/log_message', methods=['POST'])
    def log_message():
        """API endpoint to log messages from iOS Shortcut"""
        try:
            # Validate request content type
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
                
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            # Verify token
            if data.get('token') != Config.IOS_SHORTCUT_TOKEN:
                logger.warning(f"Invalid token attempt from {request.remote_addr}")
                return jsonify({'error': 'Invalid token'}), 401
            
            # Validate required fields
            sender = data.get('sender', '').strip()
            content = data.get('message', '').strip()
            source = data.get('source', 'text').strip()
            
            if not content:
                return jsonify({'error': 'Message content required'}), 400
                
            if len(content) > 5000:  # Reasonable limit
                return jsonify({'error': 'Message content too long (max 5000 characters)'}), 400
                
            if not sender:
                sender = 'Unknown'
            elif len(sender) > 255:
                sender = sender[:255]
            
            # Use AI to analyze priority and generate summary
            priority, confidence = ai_services.analyze_message_priority(content)
            summary = ai_services.generate_summary(content)
            
            # Find similar messages
            similar_messages = ai_services.find_similar_messages(content)
            
            # Get suggested actions
            suggested_actions = ai_services.suggest_actions(content)
            
            # Create message record
            message = Message(
                sender=sender,
                content=content,
                source=source,
                priority=priority,
                summary=summary
            )
            db.session.add(message)
            db.session.commit()
            
            # Log to Google Sheets (with error handling)
            try:
                sheets_service.log_message(sender, content, source, priority)
            except Exception as e:
                logger.warning(f"Failed to log to Google Sheets: {e}")
            
            # Process for immediate actions if high priority
            if priority == 'High':
                try:
                    processing_result = message_scanner.process_message(message)
                except Exception as e:
                    logger.error(f"Error processing high priority message: {e}")
            
            logger.info(f"Logged message from {sender} via API (ID: {message.id}, Priority: {priority})")
            
            return jsonify({
                'success': True,
                'message_id': message.id,
                'priority': priority,
                'confidence': confidence,
                'summary': summary,
                'similar_messages': [{'id': msg.id, 'content': msg.content} for msg in similar_messages],
                'suggested_actions': suggested_actions,
                'message': 'Message logged successfully'
            })
            
        except Exception as e:
            logger.error(f"Error logging message via API: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to log message'}), 500
    
    @app.route('/api/analyze_text', methods=['POST'])
    def analyze_text():
        """API endpoint to analyze text content"""
        try:
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            content = data.get('content', '').strip()
            
            if not content:
                return jsonify({'error': 'Content required'}), 400
            
            # Perform AI analysis
            priority, confidence = ai_services.analyze_message_priority(content)
            summary = ai_services.generate_summary(content)
            suggested_actions = ai_services.suggest_actions(content)
            similar_messages = ai_services.find_similar_messages(content)
            
            return jsonify({
                'success': True,
                'analysis': {
                    'priority': priority,
                    'confidence': confidence,
                    'summary': summary,
                    'suggested_actions': suggested_actions,
                    'similar_messages': [
                        {
                            'id': msg.id,
                            'content': msg.content,
                            'created_at': msg.created_at.isoformat()
                        } for msg in similar_messages
                    ]
                }
            })
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return jsonify({'error': 'Failed to analyze text'}), 500
    
    # Form submission handlers
    @app.route('/update_task_status', methods=['POST'])
    def update_task_status():
        """Update task status"""
        try:
            task_id = request.form.get('task_id')
            new_status = request.form.get('status')
            assigned_to = request.form.get('assigned_to', '')
            
            task = Task.query.get_or_404(task_id)
            task.status = new_status
            if assigned_to:
                task.assigned_to = assigned_to
            task.updated_at = datetime.now()
            
            db.session.commit()
            
            flash(f'Task "{task.title}" updated successfully', 'success')
            return redirect(url_for('tasks'))
            
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            flash('Error updating task', 'error')
            return redirect(url_for('tasks'))
    
    @app.route('/create_task', methods=['POST'])
    def create_task():
        """Create a new task"""
        try:
            title = request.form.get('title')
            description = request.form.get('description', '')
            facility = request.form.get('facility')
            priority = request.form.get('priority', 'Medium')
            assigned_to = request.form.get('assigned_to', '')
            
            if not title or not facility:
                flash('Title and facility are required', 'error')
                return redirect(url_for('tasks'))
            
            task = Task(
                title=title,
                description=description,
                facility=facility,
                priority=priority,
                assigned_to=assigned_to
            )
            db.session.add(task)
            db.session.commit()
            
            # Log to Google Sheets
            sheets_service.log_task(title, description, facility, priority, assigned_to)
            
            flash(f'Task "{title}" created successfully', 'success')
            return redirect(url_for('tasks'))
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            flash('Error creating task', 'error')
            return redirect(url_for('tasks'))
    
    @app.route('/acknowledge_reminder', methods=['POST'])
    def acknowledge_reminder():
        """Acknowledge a reminder"""
        try:
            reminder_id = request.form.get('reminder_id')
            reminder = Reminder.query.get_or_404(reminder_id)
            reminder.acknowledged = True
            db.session.commit()
            
            flash('Reminder acknowledged', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            logger.error(f"Error acknowledging reminder: {e}")
            flash('Error acknowledging reminder', 'error')
            return redirect(url_for('dashboard'))
    
    @app.route('/create_announcement', methods=['POST'])
    def create_announcement():
        """Create a new announcement"""
        try:
            title = request.form.get('title')
            content = request.form.get('content')
            facilities = request.form.getlist('facilities')
            announcement_type = request.form.get('type', 'General')
            
            if not title or not content:
                flash('Title and content are required', 'error')
                return redirect(url_for('announcements'))
            
            announcement = Announcement(
                title=title,
                content=content,
                facilities=','.join(facilities) if facilities else '',
                announcement_type=announcement_type
            )
            db.session.add(announcement)
            db.session.commit()
            
            flash(f'Announcement "{title}" created successfully', 'success')
            return redirect(url_for('announcements'))
            
        except Exception as e:
            logger.error(f"Error creating announcement: {e}")
            flash('Error creating announcement', 'error')
            return redirect(url_for('announcements'))
    
    # Apple Integration Endpoints
    @app.route('/api/apple_shortcuts/create_task', methods=['POST'])
    def apple_shortcuts_create_task():
        """API endpoint for Apple Shortcuts to create tasks"""
        try:
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
                
            data = request.get_json()
            if data.get('token') != Config.IOS_SHORTCUT_TOKEN:
                return jsonify({'error': 'Invalid token'}), 401
            
            title = data.get('title', '').strip()
            description = data.get('description', '').strip()
            facility = data.get('facility', Config.FACILITIES[0] if Config.FACILITIES else 'Default')
            priority = data.get('priority', 'Medium')
            due_date = data.get('due_date', '')
            
            if not title:
                return jsonify({'error': 'Task title required'}), 400
            
            task = Task(
                title=title,
                description=description,
                facility=facility,
                priority=priority
            )
            
            if due_date:
                try:
                    task.due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except:
                    pass
            
            db.session.add(task)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'task_id': task.id,
                'message': 'Task created successfully via Apple Shortcuts'
            })
            
        except Exception as e:
            logger.error(f"Error creating task via Apple Shortcuts: {e}")
            return jsonify({'error': 'Failed to create task'}), 500
    
    @app.route('/api/apple_shortcuts/voice_memo', methods=['POST'])
    def apple_shortcuts_voice_memo():
        """Process voice memo from Apple Shortcuts"""
        try:
            data = request.get_json()
            if data.get('token') != Config.IOS_SHORTCUT_TOKEN:
                return jsonify({'error': 'Invalid token'}), 401
            
            transcript = data.get('transcript', '').strip()
            duration = data.get('duration', 0)
            
            if not transcript:
                return jsonify({'error': 'Transcript required'}), 400
            
            # Process as a message
            priority = message_scanner.determine_priority(transcript)
            
            message = Message(
                sender='Voice Memo',
                content=f"Voice memo ({duration}s): {transcript}",
                source='voice_memo',
                priority=priority
            )
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message_id': message.id,
                'priority': priority,
                'suggested_actions': message_scanner.suggest_actions(transcript)
            })
            
        except Exception as e:
            logger.error(f"Error processing voice memo: {e}")
            return jsonify({'error': 'Failed to process voice memo'}), 500
    
    @app.route('/api/apple_shortcuts/calendar_event', methods=['POST'])
    def apple_shortcuts_calendar_event():
        """Create calendar event from Apple Shortcuts"""
        try:
            data = request.get_json()
            if data.get('token') != Config.IOS_SHORTCUT_TOKEN:
                return jsonify({'error': 'Invalid token'}), 401
            
            title = data.get('title', '').strip()
            start_time_str = data.get('start_time', '')
            end_time_str = data.get('end_time', '')
            description = data.get('description', '').strip()
            location = data.get('location', '').strip()
            
            if not title or not start_time_str:
                return jsonify({'error': 'Title and start time required'}), 400
            
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00')) if end_time_str else start_time + timedelta(hours=1)
            except:
                return jsonify({'error': 'Invalid date format'}), 400
            
            event = CalendarEvent(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                location=location,
                facility=Config.FACILITIES[0] if Config.FACILITIES else 'Default'
            )
            db.session.add(event)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'event_id': event.id,
                'message': 'Calendar event created successfully'
            })
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return jsonify({'error': 'Failed to create calendar event'}), 500
    
    @app.route('/api/imessage/incoming', methods=['POST'])
    def imessage_incoming():
        """Process incoming iMessage via Shortcuts"""
        try:
            data = request.get_json()
            if data.get('token') != Config.IOS_SHORTCUT_TOKEN:
                return jsonify({'error': 'Invalid token'}), 401
            
            sender = data.get('sender', 'iMessage Contact')
            text = data.get('text', '').strip()
            
            if not text:
                return jsonify({'error': 'Message text required'}), 400
            
            priority = message_scanner.determine_priority(text)
            
            message = Message(
                sender=sender,
                content=text,
                source='imessage',
                priority=priority
            )
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message_id': message.id,
                'priority': priority
            })
            
        except Exception as e:
            logger.error(f"Error processing iMessage: {e}")
            return jsonify({'error': 'Failed to process iMessage'}), 500
    
    @app.route('/api/voicemail/transcript', methods=['POST'])
    def voicemail_transcript():
        """Process voicemail transcript"""
        try:
            data = request.get_json()
            if data.get('token') != Config.IOS_SHORTCUT_TOKEN:
                return jsonify({'error': 'Invalid token'}), 401
            
            caller = data.get('caller', 'Unknown Caller')
            transcript = data.get('transcript', '').strip()
            duration = data.get('duration', 0)
            confidence = data.get('confidence', 0.0)
            
            if not transcript:
                return jsonify({'error': 'Transcript required'}), 400
            
            priority = message_scanner.determine_priority(transcript)
            
            message = Message(
                sender=f"Voicemail from {caller}",
                content=f"Voicemail ({duration}s, {confidence:.1%} confidence): {transcript}",
                source='voicemail',
                priority=priority
            )
            db.session.add(message)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message_id': message.id,
                'priority': priority
            })
            
        except Exception as e:
            logger.error(f"Error processing voicemail transcript: {e}")
            return jsonify({'error': 'Failed to process voicemail'}), 500
    
    @app.route('/api/microsoft/teams_webhook', methods=['POST'])
    def microsoft_teams_webhook():
        """Webhook for Microsoft Teams messages"""
        try:
            data = request.get_json()
            
            # Process Teams webhook data
            if data.get('type') == 'message':
                text = data.get('text', '').strip()
                sender = data.get('from', {}).get('name', 'Teams User')
                
                if text:
                    priority = message_scanner.determine_priority(text)
                    
                    message = Message(
                        sender=f"Teams: {sender}",
                        content=text,
                        source='teams',
                        priority=priority
                    )
                    db.session.add(message)
                    db.session.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Error processing Teams webhook: {e}")
            return jsonify({'error': 'Failed to process Teams webhook'}), 500
    
    @app.route('/api/google/gmail_webhook', methods=['POST'])
    def google_gmail_webhook():
        """Webhook for Gmail notifications"""
        try:
            data = request.get_json()
            
            # Process Gmail webhook data
            if data.get('message'):
                # In a full implementation, this would fetch the actual email content
                logger.info("Gmail webhook received")
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Error processing Gmail webhook: {e}")
            return jsonify({'error': 'Failed to process Gmail webhook'}), 500
    
    @app.route('/api/integrations/status', methods=['GET'])
    def integrations_status():
        """Get status of all integrations"""
        try:
            from integration_services import (
                apple_shortcuts_service, enhanced_microsoft_service, enhanced_google_service
            )
            
            status = {
                'apple_shortcuts': {
                    'configured': bool(Config.IOS_SHORTCUT_TOKEN),
                    'webhook_urls': apple_shortcuts_service.get_shortcut_instructions()
                },
                'microsoft_graph': {
                    'configured': all([
                        Config.MICROSOFT_CLIENT_ID,
                        Config.MICROSOFT_CLIENT_SECRET,
                        Config.MICROSOFT_TENANT_ID
                    ])
                },
                'google_services': {
                    'configured': bool(os.environ.get('GOOGLE_CREDENTIALS_JSON') or 
                                     (Config.GOOGLE_CREDENTIALS_FILE and os.path.exists(Config.GOOGLE_CREDENTIALS_FILE)))
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'integrations': status
            })
            
        except Exception as e:
            logger.error(f"Error getting integrations status: {e}")
            return jsonify({'error': 'Failed to get integrations status'}), 500
    
    # Additional API endpoints
    @app.route('/api/tasks', methods=['GET'])
    def api_get_tasks():
        """API endpoint to get tasks with filtering"""
        try:
            # Get query parameters
            facility = request.args.get('facility', '')
            status = request.args.get('status', '')
            priority = request.args.get('priority', '')
            limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 items
            
            query = Task.query
            
            if facility:
                query = query.filter_by(facility=facility)
            if status:
                query = query.filter_by(status=status)
            if priority:
                query = query.filter_by(priority=priority)
            
            tasks = query.order_by(Task.created_at.desc()).limit(limit).all()
            
            return jsonify({
                'success': True,
                'tasks': [task.to_dict() for task in tasks],
                'count': len(tasks)
            })
            
        except Exception as e:
            logger.error(f"Error getting tasks via API: {e}")
            return jsonify({'error': 'Failed to get tasks'}), 500
    
    @app.route('/api/tasks/<int:task_id>/status', methods=['PUT'])
    def api_update_task_status(task_id):
        """API endpoint to update task status"""
        try:
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
                
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON data'}), 400
            
            task = Task.query.get_or_404(task_id)
            new_status = data.get('status', '').strip()
            
            valid_statuses = ['Not Started', 'In Progress', 'Completed']
            if new_status not in valid_statuses:
                return jsonify({'error': f'Invalid status. Must be one of: {valid_statuses}'}), 400
            
            old_status = task.status
            task.status = new_status
            task.updated_at = datetime.now()
            
            # Optional: update assigned_to if provided
            if 'assigned_to' in data:
                assigned_to = data['assigned_to'].strip()
                if len(assigned_to) <= 100:  # Validate length
                    task.assigned_to = assigned_to
            
            db.session.commit()
            
            logger.info(f"Task {task_id} status updated from '{old_status}' to '{new_status}' via API")
            
            return jsonify({
                'success': True,
                'task': task.to_dict(),
                'message': 'Task status updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Error updating task status via API: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to update task status'}), 500
    
    @app.route('/api/dashboard/stats', methods=['GET'])
    def api_dashboard_stats():
        """API endpoint to get dashboard statistics"""
        try:
            stats = {
                'total_tasks': Task.query.count(),
                'pending_tasks': Task.query.filter(Task.status.in_(['Not Started', 'In Progress'])).count(),
                'completed_tasks': Task.query.filter_by(status='Completed').count(),
                'high_priority_messages': Message.query.filter_by(priority='High', processed=False).count(),
                'unprocessed_messages': Message.query.filter_by(processed=False).count(),
                'upcoming_events': CalendarEvent.query.filter(CalendarEvent.start_time >= datetime.now()).count(),
                'active_announcements': Announcement.query.filter_by(active=True).count(),
                'pending_reminders': Reminder.query.filter_by(acknowledged=False).count()
            }
            
            return jsonify({
                'success': True,
                'stats': stats,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting dashboard stats via API: {e}")
            return jsonify({'error': 'Failed to get dashboard stats'}), 500

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        # Handle API requests differently
        if request.path.startswith('/api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        # Handle API requests differently
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500
