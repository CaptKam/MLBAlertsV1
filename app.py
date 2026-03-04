import os
import logging
import secrets
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from mlb_monitor import MLBMonitor

# Set appropriate logging level for production
logging.basicConfig(level=logging.INFO if os.environ.get('ENVIRONMENT') == 'production' else logging.DEBUG)

# Database configuration
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration with PostgreSQL fallback to SQLite
database_url = os.environ.get("DATABASE_URL")

# Check if the database URL is the disabled Neon endpoint, fallback to SQLite
if database_url and "ep-morning-bush-afjx81ml.c-2.us-west-2.aws.neon.tech" in database_url:
    logging.warning("Neon database endpoint detected as potentially disabled, falling back to SQLite")
    database_url = "sqlite:///mlb_monitor.db"
elif not database_url:
    database_url = "sqlite:///mlb_monitor.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

# Configure engine options based on database type
if database_url.startswith("postgresql"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    # SQLite configuration
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
    }

# Flask-Login configuration
app.config["REMEMBER_COOKIE_DURATION"] = 86400 * 30  # 30 days
app.config["SESSION_PROTECTION"] = "strong"

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = 'Please log in to access the MLB monitoring system.'
login_manager.login_message_category = 'warning'

# Import models after db initialization
with app.app_context():
    import models
    db.create_all()

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(int(user_id))

# Initialize MLB monitor
mlb_monitor = MLBMonitor()
# Start monitoring when the app initializes
mlb_monitor.start_monitoring()

@app.route('/')
@login_required
def index():
    """Main page with game selection and alert log - requires authentication"""
    # Check if user is authenticated for admin features
    is_admin = current_user.is_authenticated and current_user.is_admin
    return render_template('index.html', is_admin=is_admin, current_user=current_user)

@app.route('/api/games')
@login_required
def get_games():
    """Get list of active MLB games for today - requires authentication"""
    try:
        games = mlb_monitor.get_todays_games()
        
        # Log game count only (reduce verbosity)
        logging.debug(f"📋 Retrieved {len(games)} games for today")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            for game in games:
                logging.debug(f"   🎯 ID: {game.get('id')} - {game.get('away_team', 'Away')} @ {game.get('home_team', 'Home')} - Status: {game.get('status', 'Unknown')}")
        
        return jsonify({"success": True, "games": games})
    except Exception as e:
        logging.error(f"Error fetching games: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/monitor', methods=['POST'])
@login_required
def update_monitored_games():
    """Update which games to monitor and notification preferences - requires authentication"""
    try:
        data = request.get_json()
        game_ids = data.get('game_ids', [])
        notification_preferences = data.get('notification_preferences', None)
        
        # Save user-specific settings to database
        if notification_preferences:
            current_user.notification_preferences = notification_preferences
        current_user.monitored_games = game_ids
        db.session.commit()
        
        # Update the MLB monitor with user's settings
        mlb_monitor.set_monitored_games(game_ids, notification_preferences)
        
        # Build response message
        enabled_types = []
        if notification_preferences:
            enabled_types = [k.replace('_', ' ').title() for k, v in notification_preferences.items() if v]
        
        message = f"Monitoring {len(game_ids)} games"
        if enabled_types:
            message += f" for: {', '.join(enabled_types)}"
        
        logging.debug(f"Settings updated for user {current_user.username}: {len(game_ids)} games, {len(enabled_types)} alert types")
        
        return jsonify({"success": True, "message": message})
    except Exception as e:
        logging.error(f"Error updating monitored games: {str(e)[:100]}")  # Limit error length
        return jsonify({"success": False, "error": "Failed to update monitoring settings"}), 500

@app.route('/api/alerts')
@login_required
def get_alerts():
    """Get recent alerts - requires authentication"""
    try:
        alerts = mlb_monitor.get_alerts()
        return jsonify({"success": True, "alerts": alerts})
    except Exception as e:
        logging.error(f"Error fetching alerts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alerts/clear', methods=['POST'])
@login_required
def clear_alerts():
    """Clear all current alerts"""
    try:
        if mlb_monitor:
            cleared_count = mlb_monitor.clear_alerts()
            logging.info(f"User {current_user.username} cleared {cleared_count} alerts")
            return jsonify({
                "success": True, 
                "message": f"Cleared {cleared_count} alerts",
                "cleared_count": cleared_count
            })
        else:
            return jsonify({"success": False, "error": "Monitor not initialized"}), 500
    except Exception as e:
        logging.error(f"Error clearing alerts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alert-success-stats')
@login_required  
def get_alert_success_stats():
    """Get alert success rate statistics for the current user"""
    try:
        stats = current_user.get_alert_success_stats()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        logging.error(f"Error fetching success stats: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/track-alert-outcome', methods=['POST'])
@login_required
def track_alert_outcome():
    """Track the outcome of an alert for success rate calculation"""
    try:
        data = request.get_json()
        
        # Create new alert outcome record
        outcome = models.AlertOutcome()
        outcome.user_id = current_user.id
        outcome.game_id = data.get('game_id')
        outcome.alert_type = data.get('alert_type')
        outcome.alert_message = data.get('message')
        outcome.inning = data.get('inning')
        outcome.home_team = data.get('home_team')
        outcome.away_team = data.get('away_team')
        outcome.situation = data.get('situation')
        
        db.session.add(outcome)
        db.session.commit()
        
        return jsonify({"success": True, "outcome_id": outcome.id})
    except Exception as e:
        logging.error(f"Error tracking alert outcome: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update-alert-outcome/<int:outcome_id>', methods=['POST'])
@login_required
def update_alert_outcome(outcome_id):
    """Update alert outcome with success/failure result"""
    try:
        data = request.get_json()
        
        outcome = models.AlertOutcome.query.filter_by(
            id=outcome_id, 
            user_id=current_user.id
        ).first()
        
        if not outcome:
            return jsonify({"success": False, "error": "Outcome not found"}), 404
            
        outcome.was_successful = data.get('was_successful')
        outcome.scoring_occurred = data.get('scoring_occurred', False)
        outcome.runs_scored = data.get('runs_scored', 0)
        from datetime import datetime
        outcome.outcome_verified_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Error updating alert outcome: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/user/settings')
@login_required
def get_user_settings():
    """Get user's notification preferences and monitored games"""
    try:
        settings = {
            'notification_preferences': current_user.notification_preferences or {},
            'monitored_games': current_user.monitored_games or [],
            'telegram_alerts': current_user.telegram_alerts,
            'email_alerts': current_user.email_alerts
        }
        return jsonify({"success": True, "settings": settings})
    except Exception as e:
        logging.error(f"Error fetching user settings: {str(e)[:100]}")
        return jsonify({"success": False, "error": "Failed to fetch user settings"}), 500

@app.route('/api/user/settings', methods=['POST'])
@login_required  
def save_user_settings():
    """Save user's notification preferences"""
    try:
        data = request.get_json()
        
        if 'notification_preferences' in data:
            current_user.notification_preferences = data['notification_preferences']
        if 'monitored_games' in data:
            current_user.monitored_games = data['monitored_games']
        if 'telegram_alerts' in data:
            current_user.telegram_alerts = data['telegram_alerts']
        if 'email_alerts' in data:
            current_user.email_alerts = data['email_alerts']
            
        db.session.commit()
        
        logging.debug(f"Settings saved for user {current_user.username}")
        return jsonify({"success": True, "message": "Settings saved successfully"})
    except Exception as e:
        logging.error(f"Error saving user settings: {str(e)[:100]}")
        return jsonify({"success": False, "error": "Failed to save settings"}), 500


@app.route('/healthz')
def health_check():
    """Production health check endpoint"""
    try:
        from config import Config
        from datetime import datetime
        
        # Check if monitor is running
        monitor_status = "running" if hasattr(mlb_monitor, 'is_monitoring_active') and mlb_monitor.is_monitoring_active() else "stopped"
        
        # Check recent alerts (system health indicator)
        recent_alerts = len(mlb_monitor.alerts) if hasattr(mlb_monitor, 'alerts') else 0
        
        # Check API connectivity
        api_status = "ok"
        try:
            from datetime import date
            import requests
            test_date = date.today().strftime('%Y-%m-%d')
            response = requests.get(f"https://statsapi.mlb.com/api/v1/schedule?date={test_date}&sportId=1", timeout=5)
            if response.status_code != 200:
                api_status = "degraded"
        except Exception:
            api_status = "error"
        
        config_summary = Config.get_config_summary()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "monitor_status": monitor_status,
            "recent_alerts": recent_alerts,
            "api_status": api_status,
            "config": config_summary
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api/status')
@login_required
def get_status():
    """Get monitoring status - requires authentication"""
    try:
        status = mlb_monitor.get_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logging.error(f"Error fetching status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/telegram/test', methods=['POST'])
@login_required
def test_telegram():
    """Send a test Telegram message - requires authentication"""
    try:
        success = mlb_monitor.send_telegram_test()
        if success:
            return jsonify({"success": True, "message": "Test message sent to Telegram!"})
        else:
            return jsonify({"success": False, "error": "Failed to send test message"}), 500
    except Exception as e:
        logging.error(f"Error sending Telegram test: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/telegram/status')
@login_required
def get_telegram_status():
    """Get Telegram notifier status - requires authentication"""
    try:
        status = mlb_monitor.get_telegram_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        logging.error(f"Error fetching Telegram status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/monitor/stop', methods=['POST'])
@login_required
def stop_monitoring():
    """Stop monitoring and clear persistent settings - requires authentication"""
    try:
        success = mlb_monitor.stop_monitoring_with_clear()
        if success:
            return jsonify({"success": True, "message": "Monitoring stopped and settings cleared"})
        else:
            return jsonify({"success": False, "error": "Failed to stop monitoring"}), 500
    except Exception as e:
        logging.error(f"Error stopping monitoring: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/alerts/recent')
def get_recent_alerts():
    """Get recent alerts with optional limit"""
    try:
        limit = request.args.get('limit', default=10, type=int)
        alerts = mlb_monitor.get_recent_alerts(limit)
        return jsonify({"success": True, "alerts": alerts})
    except Exception as e:
        logging.error(f"Error fetching recent alerts: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/settings/status')
def get_settings_status():
    """Get persistent settings status"""
    try:
        status = mlb_monitor.get_persistent_settings_status()
        return jsonify({"success": True, "settings": status})
    except Exception as e:
        logging.error(f"Error fetching settings status: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/settings/auto-monitoring', methods=['POST'])
def toggle_auto_monitoring():
    """Toggle auto-monitoring restoration"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', True)
        success = mlb_monitor.persistent_settings.set_auto_monitoring_enabled(enabled)
        
        if success:
            status_text = "enabled" if enabled else "disabled"
            return jsonify({"success": True, "message": f"Auto-monitoring restoration {status_text}"})
        else:
            return jsonify({"success": False, "error": "Failed to update auto-monitoring setting"}), 500
    except Exception as e:
        logging.error(f"Error toggling auto-monitoring: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ai/test')
def test_ai_features():
    """Test OpenAI integration features"""
    try:
        # Check if OpenAI is available
        if not mlb_monitor.openai_helper.is_available():
            return jsonify({
                "success": False,
                "error": "OpenAI integration not available. Please check your API key."
            }), 500
        
        # Test game situation analysis
        test_game_data = {
            'away_team': 'Yankees',
            'home_team': 'Red Sox',
            'away_score': 3,
            'home_score': 2,
            'inning': 7,
            'inning_state': 'Top',
            'base_runners': ['2B', '3B'],
            'outs': 1
        }
        
        ai_analysis = mlb_monitor.openai_helper.analyze_game_situation(test_game_data)
        
        # Test scoring probability
        scoring_prediction = mlb_monitor.openai_helper.predict_scoring_probability(test_game_data)
        
        return jsonify({
            "success": True,
            "message": "OpenAI integration is working!",
            "test_results": {
                "game_analysis": ai_analysis,
                "scoring_prediction": scoring_prediction,
                "features_available": [
                    "AI Game Analysis",
                    "Enhanced Alert Messages",
                    "Scoring Probability Predictions",
                    "Game Event Summaries"
                ]
            }
        })
    except Exception as e:
        logging.error(f"Error testing AI features: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = bool(request.form.get('remember', False))
        
        user = models.User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            
            # Update last login
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log admin login in monitoring session - ensure only one active session per user
            if user.is_admin:
                # End any existing active sessions for this user
                existing_sessions = models.MonitoringSession.query.filter_by(
                    user_id=user.id,
                    is_active=True
                ).all()
                
                for session in existing_sessions:
                    session.is_active = False
                    session.ended_at = datetime.utcnow()
                
                # Create new monitoring session
                monitoring_session = models.MonitoringSession()
                monitoring_session.user_id = user.id
                monitoring_session.games_monitored = []
                monitoring_session.is_active = True
                db.session.add(monitoring_session)
                db.session.commit()
            
            flash(f'Successfully logged in as {user.username}. You can now access the MLB monitoring system.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout current user"""
    # End any active monitoring sessions
    if current_user.is_admin:
        from datetime import datetime
        active_sessions = models.MonitoringSession.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        for session in active_sessions:
            session.is_active = False
            session.ended_at = datetime.utcnow()
        
        db.session.commit()
    
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    """Admin access - redirect to dashboard"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with monitoring controls and statistics"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    # Get monitoring statistics
    total_alerts = models.AlertLog.query.count()
    recent_alerts = models.AlertLog.query.order_by(models.AlertLog.created_at.desc()).limit(10).all()
    active_sessions = models.MonitoringSession.query.filter_by(is_active=True).all()
    all_users = models.User.query.all()
    
    return render_template('admin_dashboard.html',
                         total_alerts=total_alerts,
                         recent_alerts=recent_alerts,
                         active_sessions=active_sessions,
                         all_users=all_users)

@app.route('/admin/permissions')
@login_required
def admin_permissions():
    """Admin permissions management page"""
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('index'))
    
    # Get all users for permission management
    all_users = models.User.query.all()
    
    return render_template('admin_permissions.html', all_users=all_users)

@app.route('/admin/create-user', methods=['POST'])
@login_required
def create_admin_user():
    """Create a new admin user"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Admin access required"}), 403
    
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    is_admin = data.get('is_admin', False)
    
    # Check if user exists
    if models.User.query.filter_by(username=username).first():
        return jsonify({"success": False, "error": "Username already exists"}), 400
    
    if models.User.query.filter_by(email=email).first():
        return jsonify({"success": False, "error": "Email already exists"}), 400
    
    # Create new user
    new_user = models.User()
    new_user.username = username
    new_user.email = email
    new_user.is_admin = is_admin
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"success": True, "message": f"User {username} created successfully"})

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password page"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('change_password.html')
        
        # Validate new password
        if not new_password or len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'danger')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('change_password.html')
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('change_password.html')

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password_api():
    """API endpoint for changing password"""
    try:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            return jsonify({"success": False, "error": "Current password is incorrect"}), 400
        
        # Validate new password
        if not new_password or len(new_password) < 6:
            return jsonify({"success": False, "error": "New password must be at least 6 characters long"}), 400
        
        if new_password != confirm_password:
            return jsonify({"success": False, "error": "New passwords do not match"}), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Password changed successfully!"})
        
    except Exception as e:
        logging.error(f"Error changing password: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/stats')
@login_required
def get_admin_stats():
    """Get admin statistics for the dashboard"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Admin access required"}), 403
    
    from datetime import datetime, timedelta
    
    # Get statistics
    stats = {
        "total_alerts": models.AlertLog.query.count(),
        "alerts_today": models.AlertLog.query.filter(
            models.AlertLog.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count(),
        "active_sessions": models.MonitoringSession.query.filter_by(is_active=True).count(),
        "total_users": models.User.query.count(),
        "admin_users": models.User.query.filter_by(is_admin=True).count()
    }
    
    return jsonify({"success": True, "stats": stats})

@app.route('/api/admin/save-permissions', methods=['POST'])
@login_required
def save_user_permissions():
    """Save user permission changes"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Admin access required"}), 403
    
    try:
        data = request.get_json()
        permissions = data.get('permissions', {})
        
        # Process each user's permission changes
        for user_id, user_permissions in permissions.items():
            user = models.User.query.get(int(user_id))
            if not user:
                continue
                
            # Update or create permissions
            for perm_key, perm_value in user_permissions.items():
                # Check if permission already exists
                existing_perm = models.UserPermission.query.filter_by(
                    user_id=user.id, 
                    permission_key=perm_key
                ).first()
                
                if existing_perm:
                    existing_perm.permission_value = perm_value
                    from datetime import datetime
                    existing_perm.updated_at = datetime.utcnow()
                else:
                    new_perm = models.UserPermission()
                    new_perm.user_id = user.id
                    new_perm.permission_key = perm_key
                    new_perm.permission_value = perm_value
                    db.session.add(new_perm)
        
        db.session.commit()
        return jsonify({"success": True, "message": "Permissions saved successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/toggle-admin-status', methods=['POST'])
@login_required
def toggle_admin_status():
    """Toggle user admin status"""
    if not current_user.is_admin:
        return jsonify({"success": False, "error": "Admin access required"}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        make_admin = data.get('make_admin', False)
        
        user = models.User.query.get(int(user_id))
        if not user:
            return jsonify({"success": False, "error": "User not found"}), 404
            
        user.is_admin = make_admin
        db.session.commit()
        
        action = "granted" if make_admin else "revoked"
        return jsonify({"success": True, "message": f"Admin access {action} for {user.username}"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Create default admin user if none exists
    with app.app_context():
        if not models.User.query.filter_by(username='admin').first():
            admin = models.User()
            admin.username = 'admin'
            admin.email = 'admin@mlbalerts.com'
            admin.is_admin = True
            admin.set_password('admin123')  # Change this password immediately!
            db.session.add(admin)
            db.session.commit()
            logging.info("Default admin user created: username='admin', password='admin123'")
    
    # Start the monitoring in a separate thread
    mlb_monitor.start_monitoring()
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
