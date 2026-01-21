import uuid
import hmac
import hashlib
from decimal import Decimal
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404, render
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from loans.models import Repayment, ApprovedLoans
from payments.models import EsewaPayment, Payment
from loans.utils import update_credit_score

User = settings.AUTH_USER_MODEL


class EsewaPaymentView(View):
    """Initiate eSewa payment"""
    
    def get(self, request):
        # Handle direct access - check if there's session data
        repayment_ids = request.session.get('selected_repayments', [])
        total_amount = request.session.get('selected_amount')
        
        if not repayment_ids:
            messages.error(request, "No repayments selected. Please select repayments first.")
            return redirect("loans:repayment_list")
        
        # Get total amount or calculate from repayments
        if total_amount:
            amount = Decimal(total_amount)
        else:
            repayments = Repayment.objects.filter(
                id__in=repayment_ids,
                loan__application__applicant=request.user
            )
            amount = sum(r.amount_due for r in repayments)
        
        # Generate transaction UUID
        transaction_uuid = str(uuid.uuid4())
        
        # Create eSewa payment record
        esewa_payment = EsewaPayment.objects.create(
            user=request.user,
            amount=amount,
            product_code="EPAYTEST",  # Use your eSewa merchant code
            transaction_uuid=transaction_uuid,
            status="PENDING"
        )
        
        # Store payment info in session
        request.session['esewa_payment_id'] = esewa_payment.id
        request.session['repayment_ids'] = repayment_ids
        
        # eSewa payment URL and parameters
        esewa_url = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
        
        secret_key = "8gBm/:&EnhH.1/q"  # Correct test secret key from credentials
        amount_str = str(int(amount))  # Convert to integer for eSewa compatibility
        string_to_sign = f"amount={amount_str},total_amount={amount_str},transaction_uuid={transaction_uuid},product_code=EPAYTEST"
        signature = hmac.new(
            secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Prepare context for eSewa form
        context = {
            'esewa_url': esewa_url,
            'amount': amount,
            'transaction_uuid': transaction_uuid,
            'product_code': "EPAYTEST",
            'signature': signature,
            'success_url': request.build_absolute_uri(reverse('payments:esewa-success')),
            'failure_url': request.build_absolute_uri(reverse('payments:esewa-failure')),
        }
        
        return render(request, 'payments/esewa_form.html', context)


class EsewaSuccessView(View):
    """Handle eSewa success callback"""
    
    def get(self, request):
        transaction_uuid = request.GET.get('transaction_uuid')
        product_code = request.GET.get('product_code')
        total_amount = request.GET.get('total_amount')
        ref_id = request.GET.get('ref_id')
        
        if not all([transaction_uuid, product_code, total_amount, ref_id]):
            messages.error(request, "Invalid eSewa response.")
            return redirect("loans:repayment_list")
        
        # Get eSewa payment record
        try:
            esewa_payment = EsewaPayment.objects.get(
                transaction_uuid=transaction_uuid,
                user=request.user
            )
        except EsewaPayment.DoesNotExist:
            messages.error(request, "Payment record not found.")
            return redirect("loans:repayment_list")
        
        # Verify payment with eSewa API (for production)
        # For now, we'll consider it successful
        esewa_payment.status = "SUCCESS"
        esewa_payment.ref_id = ref_id
        esewa_payment.save()
        
        # Process repayments
        repayment_ids = request.session.get('repayment_ids', [])
        repayments = Repayment.objects.filter(
            id__in=repayment_ids,
            loan__application__applicant=request.user
        ).order_by("due_date")
        
        payment_amount = Decimal(total_amount)
        
        for repayment in repayments:
            if payment_amount <= 0:
                break
            
            remaining = repayment.remaining_amount()
            if remaining <= 0:
                continue
            
            # Calculate payment for this repayment
            payment_for_this = min(payment_amount, remaining)
            
            # Update repayment
            if repayment.amount_paid is None:
                repayment.amount_paid = 0
            
            repayment.amount_paid += payment_for_this
            repayment.paid_date = timezone.now().date()
            
            # Update status
            if repayment.amount_paid >= repayment.amount_due:
                repayment.status = "paid" if repayment.paid_date <= repayment.due_date else "late"
            else:
                repayment.status = "partial"
            
            repayment.save(update_fields=["amount_paid", "paid_date", "status"])
            
            # Create payment record
            Payment.objects.create(
                repayment=repayment,
                amount=payment_for_this,
                method="esewa",
                reference=ref_id
            )
            
            # Update credit score
            update_credit_score(request.user, repayment)
            
            # Reduce payment amount
            payment_amount -= payment_for_this
        
        # Clear session
        if 'esewa_payment_id' in request.session:
            del request.session['esewa_payment_id']
        if 'repayment_ids' in request.session:
            del request.session['repayment_ids']
        if 'selected_repayments' in request.session:
            del request.session['selected_repayments']
        if 'selected_amount' in request.session:
            del request.session['selected_amount']
        
        messages.success(request, f"Payment of Rs. {total_amount} successful via eSewa!")
        return redirect("loans:repayment_list")


class EsewaFailureView(View):
    """Handle eSewa failure callback"""
    
    def get(self, request):
        transaction_uuid = request.GET.get('transaction_uuid')
        product_code = request.GET.get('product_code')
        total_amount = request.GET.get('total_amount')
        
        # Update eSewa payment status
        try:
            esewa_payment = EsewaPayment.objects.get(
                transaction_uuid=transaction_uuid,
                user=request.user
            )
            esewa_payment.status = "FAILURE"
            esewa_payment.save()
        except EsewaPayment.DoesNotExist:
            pass
        
        # Clear session
        if 'esewa_payment_id' in request.session:
            del request.session['esewa_payment_id']
        if 'repayment_ids' in request.session:
            del request.session['repayment_ids']
        
        messages.error(request, "eSewa payment failed. Please try again.")
        return redirect("loans:repayment_list")


class PaymentMethodView(View):
    """Handle other payment methods (demo mode)"""
    
    def post(self, request):
        repayment_ids = request.session.get('selected_repayments', [])
        total_amount = request.session.get('selected_amount')
        payment_method = request.POST.get("payment_method")
        
        if not repayment_ids:
            messages.error(request, "No repayments selected.")
            return redirect("loans:repayment_list")
        
        if payment_method == "esewa":
            # Redirect to eSewa payment
            return redirect("payments:esewa-pay")
        
        # Process other payment methods as demo
        repayments = Repayment.objects.filter(
            id__in=repayment_ids,
            loan__application__applicant=request.user
        ).order_by("due_date")
        
        if total_amount:
            payment_amount = Decimal(total_amount)
        else:
            payment_amount = sum(r.amount_due for r in repayments)
        
        for repayment in repayments:
            if payment_amount <= 0:
                break
            
            remaining = repayment.remaining_amount()
            if remaining <= 0:
                continue
            
            # Calculate payment for this repayment
            payment_for_this = min(payment_amount, remaining)
            
            # Update repayment
            if repayment.amount_paid is None:
                repayment.amount_paid = 0
            
            repayment.amount_paid += payment_for_this
            repayment.paid_date = timezone.now().date()
            
            # Update status
            if repayment.amount_paid >= repayment.amount_due:
                repayment.status = "paid" if repayment.paid_date <= repayment.due_date else "late"
            else:
                repayment.status = "partial"
            
            repayment.save(update_fields=["amount_paid", "paid_date", "status"])
            
            # Create payment record
            Payment.objects.create(
                repayment=repayment,
                amount=payment_for_this,
                method=payment_method,
                reference=f"DEMO_{uuid.uuid4().hex[:8]}"
            )
            
            # Update credit score
            update_credit_score(request.user, repayment)
            
            # Reduce payment amount
            payment_amount -= payment_for_this
        
        # Clear session
        if 'selected_repayments' in request.session:
            del request.session['selected_repayments']
        if 'selected_amount' in request.session:
            del request.session['selected_amount']
        
        messages.success(request, f"Payment successful via {payment_method} (Demo mode)!")
        return redirect("loans:repayment_list")