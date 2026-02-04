from django.dispatch import receiver
from loans.signals import loan_approved_signal, loan_reject_signal
from django.core.mail import send_mail
from greenloan import settings

@receiver(loan_approved_signal)
def send_loan_approved_message(sender, loan_type, to_user, **kwargs):
    send_mail(
        subject="Thank You for Connected with GreenLoan.",
        message=f"Hi {to_user.full_name },\n\n Your  {loan_type}   has been approved. \n\nThank you for creating an account with us!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_user.email],
            html_message=f"""
            <p>Hi {to_user.full_name},</p>

                <p>
                    Your <b>{loan_type}</b> loan has been
                    <strong>approved</strong>.
                </p>

                <p>Thank you for choosing <b>GreenLoan</b>.</p>
            """,
        fail_silently=True,
    )

@receiver(loan_reject_signal)  
def send_loan_approved_message(sender, loan_type, to_user, **kwargs):
    send_mail(
        subject="Thank You for Connected with GreenLoan.",
        message=f"Hi {to_user.full_name },\n\n Your  {loan_type}   has been rejected. \n\nThank you for connecting with us!",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to_user.email],
            html_message=f"""
            <p>Hi {to_user.full_name},</p>

                <p>
                    Your <b>{loan_type}</b> loan has been
                    <strong>Rejected</strong>.
                </p>

                <p>Thank you for choosing <b>GreenLoan</b>.</p>
            """,
        fail_silently=True,
    )