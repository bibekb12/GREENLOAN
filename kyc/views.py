from django.views.generic.edit import FormView
from django.shortcuts import render
from django.urls import reverse_lazy
from deepface import DeepFace

from .forms import KYCVerificationForm
from .models import KYCVerification


class KYCVerificationView(FormView):
    template_name = 'kyc/verify.html'
    form_class = KYCVerificationForm
    success_url = reverse_lazy('kyc_verify')

    def form_valid(self, form):

        try:
            obj = form.save()

            citizenship_path = obj.citizenship.path
            selfie_path = obj.selfie.path

            result = DeepFace.verify(
                img1_path=citizenship_path,
                img2_path=selfie_path,
                detector_backend='opencv',
                enforce_detection=False
            )

            verified = result.get('verified', False)

            distance = result.get('distance', 0)

            confidence = round((1 - distance) * 100, 2)

            obj.verified = verified
            obj.confidence = confidence
            obj.save()

            context = {
                'obj': obj,
                'verified': verified,
                'confidence': confidence
            }

            return render(self.request, 'kyc/result.html', context)

        except Exception as e:

            context = {
                'form': form,
                'error': str(e)
            }

            return render(self.request, self.template_name, context)