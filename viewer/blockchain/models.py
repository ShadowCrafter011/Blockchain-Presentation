from django.db import models

class Block(models.Model):
  int_id = models.CharField(max_length=100)
  nonce = models.IntegerField()
  hash = models.CharField(max_length=1000)
  previous_hash = models.CharField(max_length=1000)
  transactions = models.CharField(max_length=50000)