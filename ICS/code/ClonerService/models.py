from django.db import models

class loginInfo(models.Model):
    username = models.TextField()
    password = models.TextField()
    totp_key = models.TextField()
    cookie = models.TextField()

# Create your models here.
class User(models.Model):
    username = models.TextField()
    # lastcollected = models.TimeField(auto)
    # images = models.ImageField(upload_to=get_avatar_full_path,blank=)
