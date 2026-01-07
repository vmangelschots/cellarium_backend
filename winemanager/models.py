from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Wine(models.Model):
    name = models.CharField(max_length=200)
    #producer = models.CharField(max_length=200, blank=True, null=True)
    region = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    vintage = models.PositiveIntegerField(blank=True, null=True)
    grape_varieties = models.CharField(max_length=255, blank=True, null=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, blank=True, null=True,help_text="Rating from 0.0 to 5.0",validators=[
        MinValueValidator(0.0),
        MaxValueValidator(5.0),
    ])
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

class Bottle(models.Model):
    wine = models.ForeignKey(Wine, on_delete=models.CASCADE,null=False,blank=False)
    purchase_date = models.DateField(blank=True, null=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    store = models.ForeignKey('Store', on_delete=models.SET_NULL, blank=True, null=True)
    consumed_at = models.DateField(blank=True, null=True)
    def __str__(self):
        return f"{self.wine.name}"
    
class Store(models.Model): 
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name