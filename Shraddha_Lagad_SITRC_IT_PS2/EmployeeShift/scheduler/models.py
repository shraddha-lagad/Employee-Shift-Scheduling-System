from django.db import models

# Create your models here.
from django.db import models


class Employee(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.name


class Shift(models.Model):
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    overnight = models.BooleanField(default=False)

    employees = models.ManyToManyField(Employee, blank=True)

    def __str__(self):
        return str(self.date)