from django.db import models

class Wine(models.Model):
    name = models.CharField(max_length=200)
    #producer = models.CharField(max_length=200, blank=True, null=True)
    region = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    vintage = models.PositiveIntegerField(blank=True, null=True)
    grape_varieties = models.CharField(max_length=255, blank=True, null=True)
    wine_type = models.CharField(
        max_length=50,
        choices=[
            ("red", "Red"),
            ("white", "White"),
            ("rosé", "Rosé"),
            ("sparkling", "Sparkling"),
        ],
        blank=True,
        null=True,
    )

    notes = models.TextField(blank=True)   

    def __str__(self):
        return f"{self.name} ({self.vintage})" if self.vintage else self.name


class Stores(models.Model): 
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name