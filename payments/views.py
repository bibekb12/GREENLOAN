import base64
import json
import uuid
import hmac
import hashlib
from decimal import Decimal
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404, render
from django.views.generic import ListView, View
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import requests
from loans.models import Repayment, ApprovedLoans
from payments.models import EsewaPayment, Payment
from loans.utils import update_credit_score

User = settings.AUTH_USER_MODEL

class PaymentMethodView(View):

    """Handle other payment methods (demo mode)"""
    
    def post(self, request):
        repayment_ids = request.session.get('selected_repayments', [])
        total_amount = request.session.get('selected_amount')
        payment_method = request.session.get("payment_method")
        
        if not repayment_ids:
            messages.error(request, "No repayments selected.")
            return redirect("loans:repayment_list")
        
        
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
            
        return redirect("loans:repayment_list")
    

class EsewaPaymentView(ListView):
    """Initiate eSewa payment"""
    
    def get(self, request):
        product_code="EPAYTEST"
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
            product_code=product_code,
            transaction_uuid=transaction_uuid,
            status="PENDING"
        )
        
        # Store payment info in session
        request.session['esewa_payment_id'] = esewa_payment.id
        request.session['repayment_ids'] = repayment_ids
        
        # eSewa payment URL and parameters
        esewa_url = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
        
        secret_key = "8gBm/:&EnhH.1/q" 
        amount_str = str(int(amount))
        signed_field_names = "amount,total_amount,transaction_uuid,product_code"
        string_to_sign = f"amount={amount_str},total_amount={amount_str},transaction_uuid={transaction_uuid},product_code={product_code}"
        hmac_sha256 = hmac.new(
            secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        )
        signature = base64.b64encode(hmac_sha256.digest()).decode("utf-8")
  
        # Prepare context for eSewa form
        context = {
            'esewa_url': esewa_url,
            'amount': amount_str,
            'total_amount': amount_str,
            'transaction_uuid': transaction_uuid,
            'product_code': product_code,
            'signed_field_names': signed_field_names,
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

class KhaltiPaymentView(View):
    """initiate the khalti payment"""
    
    def get(self, request):
        full_name = request.user.get_full_name()
        user_email = request.user.email

        amount = request.session.get("selected_amount")
        purchase_order_id = str(uuid.uuid4())
        repayment_ids = request.session.get("selected_repayments",[])

        if not amount or not repayment_ids:
            messages.error(request, "No repayments selected or amount missing.")
            return redirect("loans:repayment_list")

        url = "https://dev.khalti.com/api/v2/epayment/initiate/"

        payload = json.dumps({
            "return_url": request.build_absolute_uri("/app/repayments/"),
            "website_url":request.build_absolute_uri("/"),
            "amount":int(float(amount)*100),
            "purchase_order_id": purchase_order_id,
            "purchase_order_name": "loan repyament",
            "customer_info":{
                "name": full_name,
                "email": user_email,
                "phone":"9800000001"
            }
        })
        headers = {
            'Authorization':'Key live_secret_key_68791341fdd94846a146f0457ff7b455',
            'Content-Type':'application/json',
        }
        response = requests.post(url, headers=headers, data=payload)

# Debug: print raw response
        print("Khalti response status:", response.status_code)
        print("Khalti response body:", response.text)

        try:
            data = response.json()
        except ValueError:
            messages.error(request, "Failed to initiate Khalti payment. Invalid response.")
            return redirect("loans:repayment_list")

        checkout_url = data.get("payment_url")
        if checkout_url:
            return redirect(checkout_url)
        else:
            messages.error(request, "Khalti payment initiation failed.")
            return redirect("loans:repayment_list")
