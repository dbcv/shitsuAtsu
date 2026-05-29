# app/signals.py
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=instance)
    profile.save()


@receiver(user_logged_in)
def ensure_user_profile_exists(sender, user, request, **kwargs):
    Profile.objects.get_or_create(user=user)
