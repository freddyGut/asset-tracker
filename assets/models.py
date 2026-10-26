from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    name = models.CharField("name", max_length=100, unique=True)
    description = models.TextField("description", blank=True)

    class Meta:
        verbose_name = "category"
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField("name", max_length=100)
    description = models.TextField("description", blank=True)
    parent = models.ForeignKey(
        "self",
        verbose_name="parent location",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )

    class Meta:
        verbose_name = "location"
        verbose_name_plural = "locations"
        ordering = ["name"]

    def __str__(self):
        return self.full_path

    @property
    def full_path(self):
        """Ex: 'Milan HQ > Building A > Floor 2 > Room 204'."""
        parts = [self.name]
        node = self.parent
        while node is not None:
            parts.append(node.name)
            node = node.parent
        return " > ".join(reversed(parts))

    def clean(self):
        # Prevents loops in the hierarchy (a location cannot be
        # a parent of itself or of its ancestor).
        node = self.parent
        while node is not None:
            if node.pk == self.pk:
                raise ValidationError(
                    "A location cannot be contained within itself."
                )
            node = node.parent


class Asset(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        IN_USE = "in_use", "In Use"
        MAINTENANCE = "maintenance", "In Maintenance"
        RETIRED = "retired", "Retired"

    tag = models.CharField(
        "asset tag",
        max_length=20,
        unique=True,
        null=True, #value assigned after registering the asset in the database
        blank=True,
        editable=False,
    )
    name = models.CharField("name", max_length=200)
    description = models.TextField("description", blank=True)
    category = models.ForeignKey(
        Category,
        verbose_name="category",
        on_delete=models.PROTECT, #does not delete the corresponding category record
        related_name="assets",
    )
    location = models.ForeignKey(
        Location,
        verbose_name="location",
        on_delete=models.PROTECT,
        related_name="assets",
    )
    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    serial_number = models.CharField("serial number", max_length=100, blank=True)
    purchase_date = models.DateField("purchase date", null=True, blank=True)
    purchase_price = models.DecimalField(
        "purchase price",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="assigned to",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_assets", #ex: jonathan.assigned_assets.all()
    )
    notes = models.TextField("notes", blank=True)
    created_at = models.DateTimeField("created at", auto_now_add=True)
    updated_at = models.DateTimeField("updated at", auto_now=True) #timestamp updates each time we make a change to the record

    class Meta:
        verbose_name = "asset"
        verbose_name_plural = "assets"
        ordering = ["-created_at"] # descending

    def __str__(self):
        return f"{self.tag or '—'} · {self.name}"

    def save(self, *args, **kwargs):
        #asset exists only as an object in RAM, not as a record in the database
        #therefore, pk always evaluates none, and "creating" reminds us of this property  
        creating = self.pk is None 
        #field self.pk now changes with the pk assigned by the DBMS
        super().save(*args, **kwargs)
        #field self.tag is still empty. both conditions are true!
        if creating and not self.tag:
            self.tag = f"AST-{self.pk:06d}"
            #saves time
            super().save(update_fields=["tag"])


class AssetHistory(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        MOVED = "moved", "Moved"
        STATUS_CHANGED = "status_changed", "Status Changed"
        ASSIGNED = "assigned", "Assigned"
        UPDATED = "updated", "Updated"

    asset = models.ForeignKey(
        Asset,
        verbose_name="asset",
        on_delete=models.CASCADE,
        related_name="history",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="executed by",
        null=True,
        on_delete=models.SET_NULL,
        related_name="asset_events",
    )
    event_type = models.CharField(
        "event type", max_length=20, choices=EventType.choices
    )
    #for computational reasons: O(1) (ex: if I have to fetch the old value)
    #using a few extra bytes of memory for saving a lot of CPU operations
    old_value = models.CharField("old value", max_length=255, blank=True)
    new_value = models.CharField("new value", max_length=255, blank=True)
    timestamp = models.DateTimeField("timestamp", auto_now_add=True)

    class Meta:
        verbose_name = "asset history event"
        verbose_name_plural = "asset history events"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.asset} · {self.get_event_type_display()} · {self.timestamp:%d/%m/%Y %H:%M}"

