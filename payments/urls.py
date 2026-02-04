from django.urls import path
from .views import EsewaPaymentView, EsewaSuccessView, EsewaFailureView, PaymentMethodView, KhaltiPaymentView

app_name = 'payments'

urlpatterns = [
    # esewa payment urls
    path('esewa-pay/', EsewaPaymentView.as_view(), name='esewa-pay'),
    path('esewa-success/', EsewaSuccessView.as_view(), name='esewa-success'),
    path('esewa-failure/', EsewaFailureView.as_view(), name='esewa-failure'),
    path('process/', PaymentMethodView.as_view(), name='process'),

    #khalti payment urls
    path('khalti/pay', KhaltiPaymentView.as_view() ,name='khalti-pay')
]
