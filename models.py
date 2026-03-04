from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    """Admin user model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Alert preferences and settings
    telegram_alerts = db.Column(db.Boolean, default=True)
    email_alerts = db.Column(db.Boolean, default=False)
    
    # Comprehensive notification preferences (JSON column for detailed settings)
    notification_preferences = db.Column(db.JSON, default=lambda: {
        'runners': True,
        'hits': True,
        'scoring': True,
        'inning_change': False,
        'home_runs': True,
        'strikeouts': False,
        'runners_23_no_outs': True,
        'bases_loaded_no_outs': True,
        'runner_3rd_no_outs': True,
        'runners_13_no_outs': True,
        'runners_23_one_out': True,
        'runners_12_no_outs': True,
        'runner_2nd_no_outs': True,
        'bases_loaded_one_out': True,
        'runner_3rd_one_out': True,
        'runners_13_one_out': True,
        'seventh_inning': True,
        'game_start': True,
        'tie_ninth': True,
        'wind_speed': True,
        'wind_shift': True,
        'hot_windy': True,
        'temp_wind': True,
        'power_hitter': True,
        'ai_enhance_alerts': False,
        'ai_summarize_events': False
    })
    
    # User's monitored games (JSON column)
    monitored_games = db.Column(db.JSON, default=list)
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_alert_success_stats(self):
        """Calculate alert success rate statistics for this user"""
        from sqlalchemy import func, and_
        
        # Get total alerts with resolved outcomes
        total_resolved = AlertOutcome.query.filter(
            and_(AlertOutcome.user_id == self.id, AlertOutcome.was_successful.isnot(None))
        ).count()
        
        # Get successful alerts
        successful = AlertOutcome.query.filter(
            and_(AlertOutcome.user_id == self.id, AlertOutcome.was_successful == True)
        ).count()
        
        # Get alerts by type
        alert_type_stats = db.session.query(
            AlertOutcome.alert_type,
            func.count(AlertOutcome.id).label('total'),
            func.sum(func.cast(AlertOutcome.was_successful, db.Integer)).label('successful')
        ).filter(
            and_(AlertOutcome.user_id == self.id, AlertOutcome.was_successful.isnot(None))
        ).group_by(AlertOutcome.alert_type).all()
        
        # Calculate success rate
        success_rate = (successful / total_resolved * 100) if total_resolved > 0 else 0
        
        # Get recent performance (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_total = AlertOutcome.query.filter(
            and_(
                AlertOutcome.user_id == self.id,
                AlertOutcome.was_successful.isnot(None),
                AlertOutcome.created_at >= thirty_days_ago
            )
        ).count()
        
        recent_successful = AlertOutcome.query.filter(
            and_(
                AlertOutcome.user_id == self.id,
                AlertOutcome.was_successful == True,
                AlertOutcome.created_at >= thirty_days_ago
            )
        ).count()
        
        recent_success_rate = (recent_successful / recent_total * 100) if recent_total > 0 else 0
        
        return {
            'total_alerts': total_resolved,
            'successful_alerts': successful,
            'success_rate': round(success_rate, 1),
            'recent_total': recent_total,
            'recent_successful': recent_successful,
            'recent_success_rate': round(recent_success_rate, 1),
            'alert_type_breakdown': [
                {
                    'type': stat.alert_type,
                    'total': stat.total,
                    'successful': stat.successful or 0,
                    'rate': round(((stat.successful or 0) / stat.total * 100), 1) if stat.total > 0 else 0
                } for stat in alert_type_stats
            ]
        }
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserPermission(db.Model):
    """Track user-specific permissions for fine-grained access control"""
    __tablename__ = 'user_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_key = db.Column(db.String(100), nullable=False)
    permission_value = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='permissions')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('user_id', 'permission_key', name='unique_user_permission'),)
    
    def __repr__(self):
        return f'<UserPermission {self.user_id}:{self.permission_key}={self.permission_value}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'permission_key': self.permission_key,
            'permission_value': self.permission_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AlertLog(db.Model):
    """Log of all alerts sent to track admin activity"""
    __tablename__ = 'alert_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_to_telegram = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationship
    user = db.relationship('User', backref='alert_logs')
    
    def __repr__(self):
        return f'<AlertLog {self.alert_type} at {self.created_at}>'


class MonitoringSession(db.Model):
    """Track monitoring sessions for admin oversight"""
    __tablename__ = 'monitoring_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    games_monitored = db.Column(db.JSON)
    alerts_sent = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    user = db.relationship('User', backref='monitoring_sessions')
    
    def __repr__(self):
        return f'<MonitoringSession {self.id} by User {self.user_id}>'


class AlertOutcome(db.Model):
    """Track alert outcomes to measure success rate"""
    __tablename__ = 'alert_outcomes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    game_id = db.Column(db.Integer, nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    alert_message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Outcome tracking
    was_successful = db.Column(db.Boolean, default=None)  # None = pending, True/False = resolved
    outcome_verified_at = db.Column(db.DateTime)
    scoring_occurred = db.Column(db.Boolean, default=False)
    runs_scored = db.Column(db.Integer, default=0)
    
    # Alert context
    inning = db.Column(db.String(10))
    home_team = db.Column(db.String(50))
    away_team = db.Column(db.String(50))
    situation = db.Column(db.String(200))  # Base runners, outs, etc.
    
    # Relationship
    user = db.relationship('User', backref='alert_outcomes')
    
    def __repr__(self):
        return f'<AlertOutcome {self.alert_type} - Success: {self.was_successful}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'alert_message': self.alert_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'was_successful': self.was_successful,
            'scoring_occurred': self.scoring_occurred,
            'runs_scored': self.runs_scored,
            'inning': self.inning,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'situation': self.situation
        }