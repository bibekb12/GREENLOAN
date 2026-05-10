import base64

from django.contrib import messages
from django.contrib.auth import get_user_model, login, update_session_auth_hash
from django.core.files.base import ContentFile
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin

from deepface import DeepFace

from .forms import LiveKYCForm
from .models import KYCVerification

User = get_user_model()


class KYCVerificationView(LoginRequiredMixin, FormView):

    template_name = "kyc/verify.html"
    form_class = LiveKYCForm

    def form_valid(self, form):

        try:

            user = self.request.user

            if not user.passport_photo_url:

                messages.error(
                    self.request,
                    "Passport size photo not found."
                )

                return redirect("kyc:kyc_verify")

            live_capture = form.cleaned_data.get(
                "live_capture"
            )

            if not live_capture:

                messages.error(
                    self.request,
                    "Live capture image missing."
                )

                return redirect("kyc_verify")

            format, imgstr = live_capture.split(
                ";base64,"
            )

            ext = format.split("/")[-1]

            selfie_file = ContentFile(
                base64.b64decode(imgstr),
                name=f"live_selfie.{ext}"
            )

            kyc = KYCVerification.objects.create(
                user=user,
                selfie_image=selfie_file,
                blink_detected=True,
                left_turn_detected=True,
                right_turn_detected=True
            )

            passport_path = (
                user.passport_photo_url.path
            )

            selfie_path = (
                kyc.selfie_image.path
            )

            result = DeepFace.verify(
                img1_path=passport_path,
                img2_path=selfie_path,
                detector_backend="opencv",
                enforce_detection=False
            )

            verified = result.get(
                "verified",
                False
            )

            distance = result.get(
                "distance",
                0
            )

            confidence = round(
                (1 - distance) * 100,
                2
            )

            kyc.verified = verified
            kyc.confidence = confidence
            kyc.save()

            # UPDATE USER KYC STATUS
            if verified:
                user.kyc_status = "verified"
                user.kyc_verified_at = timezone.now()
                # Set verifier to the user performing verification (self verification here)
                user.kyc_verified_by = self.request.user
                user.save()
                
                # Refresh authentication session to prevent logout during redirect
                update_session_auth_hash(self.request, user)
                messages.success(self.request, "KYC Verification Successful!")
            else:
                user.kyc_status = "rejected"
                user.save()
                messages.error(self.request, "Face Verification Failed. Please try again.")

            self.request.session["verified"] = verified
            self.request.session["confidence"] = confidence
            self.request.session["passport_photo"] = user.passport_photo_url.url
            self.request.session["selfie"] = kyc.selfie_image.url
            # Ensure session changes are persisted before redirect
            self.request.session.modified = True
            self.request.session.save()
            return redirect("kyc:kyc_result")

        except Exception as e:

            print(e)

            messages.error(
                self.request,
                str(e)
            )

            return redirect("kyc:kyc_verify")
        
class KYCResultView(
    LoginRequiredMixin,
    View
):

    template_name = "kyc/result.html"

    def get(self, request):

        context = {

            "verified":
            request.session.get(
                "verified"
            ),

            "confidence":
            request.session.get(
                "confidence"
            ),

            "passport_photo":
            request.session.get(
                "passport_photo"
            ),

            "selfie":
            request.session.get(
                "selfie"
            ),

        }

        return render(
            request,
            self.template_name,
            context
        )