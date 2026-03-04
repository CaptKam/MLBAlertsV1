# MLB Alert System - Production Deployment Guide

## Architecture Overview

The system now follows the Replit Stability Playbook with:

### Process Separation
- **Web Process** (`main.py`): Handles UI, health checks, and API endpoints
- **Worker Process** (`worker.py`): Dedicated monitoring loop with watchdog pattern
- **Configuration** (`config.py`): Environment-based settings management

### Production Features
- Health check endpoint at `/healthz`
- Structured logging with process IDs and request IDs
- Progressive backoff on failures (1s → 2s → 5s → 10s → 30s → 60s max)
- Crash notifications via Telegram
- Environment separation (dev/prod)
- Resource leak prevention

## Running in Production

### Option 1: Replit Deployments (Recommended)

1. **Create Deployment:**
   - Use Replit Deployments instead of "Always On"
   - Configure health check: `GET /healthz`
   - Set environment: `APP_ENV=production`

2. **Two-Process Setup:**
   ```bash
   # Process 1 (Web Server)
   gunicorn --bind 0.0.0.0:8000 main:app
   
   # Process 2 (Worker)
   python worker.py
   ```

### Option 2: Development Mode

```bash
# Terminal 1: Web Server
python main.py

# Terminal 2: Worker Process  
python worker.py
```

## Environment Variables

### Required Secrets
- `OPENAI_API_KEY`: OpenAI API access
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHAT_ID`: Target chat ID (negative for groups)
- `SESSION_SECRET`: Flask session security

### Optional Secrets
- `API_SPORTS_KEY`: Additional sports data source
- `MYSPORTSFEEDS_API_KEY`: Alternative data provider
- `DATABASE_URL`: PostgreSQL connection

### Configuration
- `APP_ENV`: `development` or `production` (default: development)
- `MONITORING_INTERVAL`: Polling interval in seconds (default: 0.5)
- `MAX_ALERTS_PER_HOUR`: Rate limiting (default: 100)

## Health Monitoring

### Health Check Endpoint
```bash
curl http://localhost:8000/healthz
```

Returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-10T02:30:00Z",
  "monitor_status": "running",
  "recent_alerts": 15,
  "api_status": "ok",
  "config": {
    "environment": "production",
    "secrets_configured": true
  }
}
```

### Monitoring Commands
```bash
# Check worker logs
tail -f worker.log

# Monitor system health
watch -n 5 'curl -s http://localhost:8000/healthz | jq .'

# Check alert rate
curl -s http://localhost:8000/api/alerts | jq '.alerts | length'
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Health check responding at `/healthz`
- [ ] Worker process running with watchdog
- [ ] Telegram notifications tested
- [ ] API connectivity verified
- [ ] Log rotation configured
- [ ] Backup/recovery plan in place

## Troubleshooting

### Worker Not Starting
1. Check environment variables: `python -c "from config import Config; print(Config.validate_required_secrets())"`
2. Test API access: `curl https://statsapi.mlb.com/api/v1/schedule`
3. Verify Telegram: Check bot token and chat ID

### High Memory Usage
- Worker implements connection pooling and resource cleanup
- Monitor with `/healthz` endpoint metrics
- Restart worker if memory exceeds thresholds

### Alert Delivery Issues
- Check Telegram bot permissions in group
- Verify chat ID (use negative values for groups)
- Monitor `/healthz` for API status