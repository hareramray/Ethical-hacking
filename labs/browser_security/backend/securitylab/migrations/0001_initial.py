import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Upload",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("owner", models.CharField(db_index=True, max_length=40)),
                ("name", models.CharField(max_length=160)),
                ("size", models.PositiveIntegerField()),
                ("content_type", models.CharField(max_length=80)),
                ("submitted_content_type", models.CharField(blank=True, max_length=120)),
                ("policy", models.CharField(max_length=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
