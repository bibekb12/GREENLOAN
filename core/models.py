from django.db import models


class SitePage(models.Model):
    allowed_income_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Maximum loan amount as % of applicant monthly income",
        default=50,
    )
