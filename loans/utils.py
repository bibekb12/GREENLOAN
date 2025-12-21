from loans.models import CreditScore, Repayment
from loans.models import Repayment
from django.utils import timezone
from datetime import timedelta

def update_credit_score(user, repayment):
        credit, _ = CreditScore.objects.get_or_create(user=user)

        if repayment.status == "paid" and not repayment.is_late():
            credit.score += 10
        elif repayment.status == "paid" and repayment.is_late():
            credit.score -= 15
        elif repayment.status == "pending":
            credit.score -= 30

        credit.score = max(300, min(900, credit.score))
        credit.save()

def close_loan_if_completed(loan):
    if not loan.repayments.filter(status="pending").exists():
        loan.status = "closed"
        loan.save()

        credit, _ = CreditScore.objects.get_or_create(user=loan.user)
        credit.score = min(900, credit.score + 20)
        credit.save()



def create_repayments(approved_loan):
    """
    Generate monthly repayment schedule for an approved loan.
    """
    monthly_amount = approved_loan.principle / approved_loan.tenure_months
    today = timezone.now().date()

    for i in range(1, approved_loan.tenure_months + 1):
        due_date = today + timedelta(days=30*i)
        Repayment.objects.create(
            loan=approved_loan,
            due_date=due_date,
            amount_due=monthly_amount,
            status="pending"
        )
