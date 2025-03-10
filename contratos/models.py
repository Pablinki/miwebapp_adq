from django.db import models
#import requests
#import pandas as pd
# Create your models here.

class Contrato(models.Model):
    contrato = models.CharField(max_length=100, unique=True)
    proveedor = models.CharField(max_length=255, default="Proveedor Desconocido")
    descripcion = models.TextField(default="Sin descripción")
    importe_total = models.DecimalField(max_digits=15, decimal_places=2,default=0.00)
    fecha_contrato = models.DateField(null=True, blank=True)
    inicio_vigencia = models.DateField(null=True, blank=True)
    fin_vigencia = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.contrato
