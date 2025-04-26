from fastapi_mail import FastMail, MessageSchema

async def send_password_reset_email(email: str, reset_link: str):
    message = MessageSchema(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Click the link to reset your password: {reset_link}",
        subtype="html"
    )
    fast_mail = FastMail(config)
    await fast_mail.send_message(message)