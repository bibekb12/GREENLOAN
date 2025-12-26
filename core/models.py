from django.db import models
from simple_history.models import HistoricalRecords


class SitePage(models.Model):
    allowed_income_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Maximum loan amount as % of applicant monthly income",
        default=50,
    )

    history = HistoricalRecords()