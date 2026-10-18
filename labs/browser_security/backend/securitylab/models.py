import uuid
from django.db import models


class Upload(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.CharField(max_length=40, db_index=True)
    name = models.CharField(max_length=160)
    size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=80)
    submitted_content_type = models.CharField(max_length=120, blank=True)
    policy = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
