from django.db import models
from uuid import uuid4


class Court(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=200)
    jurisdiction = models.CharField(max_length=100)
    address = models.TextField()
    contact_info = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Courtroom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    court = models.ForeignKey(
        Court, on_delete=models.CASCADE, related_name="courtrooms"
    )
    name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField()
    video_platform_config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
