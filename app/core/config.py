import os

# App
APP_ENV = os.getenv("APP_ENV", "development")

# Database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://billing_user:billing_pass@localhost:3306/billing",
)

# (Optional) Webhook security (future improvement)
WEBHOOK_SHARED_SECRET = os.getenv("WEBHOOK_SHARED_SECRET", "")
