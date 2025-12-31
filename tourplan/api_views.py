from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse
from django.conf import settings
import os

class PdfLinkAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        file_name = "BCA_Syllabus-compressed_compre_2024_01_30_18_33_22.pdf"
        pdf_path = os.path.join(settings.MEDIA_ROOT, file_name)

        if not os.path.exists(pdf_path):
            return Response(
                {"error": "File not found"},
                status=404
            )

        return FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf',
            as_attachment=False  # True = download, False = view
        )
