from celery import Celery

app = Celery("tasks", broker="redis://localhost:6379/0")

@app.task
def send_email_task(email: str, subject: str, body: str):
    # Email sending logic