import logging
from app import app

# Configure production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Auto-sync service temporarily disabled - was causing infinite loop
# TODO: Fix auto_sync_service logic to prevent continuous updates
# try:
#     from auto_sync_service import start_auto_sync
#     start_auto_sync()
#     print("🔄 Auto-sync service started - local will mirror deployed game selections")
# except Exception as e:
#     print(f"⚠️ Auto-sync service could not start: {e}")
#     print("💡 Manual sync available via sync_deployed_games.py")

if __name__ == '__main__':
    # Production mode: debug=False
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
