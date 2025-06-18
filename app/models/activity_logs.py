# Use shared architecture ActivityLog model
from shared_architecture.db.models.activity_log import ActivityLog as SharedActivityLog

# Use the shared ActivityLog model
ActivityLog = SharedActivityLog