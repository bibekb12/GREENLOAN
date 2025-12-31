from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import FileResponse
import os

class PdfLinkAPI(APIView):
    def get(self, request):
        pdf_path = "media\BCA_Syllabus-compressed_compre_2024_01_30_18_33_22.pdf"

        if not os.path.exists(pdf_path):
            return Response(
                {"error": "File not found"},
                status=404
            )

        return FileResponse(
            open(pdf_path, 'rb'),
            content_type='application/pdf'
        )
