from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.ForeignKey(User)
    oauth_token = models.CharField(max_length=200)
    oauth_secret = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=10)

class SentArticle(models.Model):
    user = models.ForeignKey(User)
    article_number = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
