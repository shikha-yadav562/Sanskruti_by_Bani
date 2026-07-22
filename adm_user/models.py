"""
catalog/models.py

Database schema for Categories and Product Filters (Color, Fabric, Print)
for the Sanskruti by Bani saree e-commerce platform.

NOTE: Product, ProductColor, and ProductImage are intentionally left out
for now — add them later (as ForeignKey/M2M references to Color, Fabric,
Print, Category below) once the Product model is being built.

Design notes (production considerations):
- Every model has `created_at` / `updated_at` for auditing.
- `is_active` (soft delete) instead of hard deletes, so historical orders
  that reference a color/fabric/category never break even if an admin
  "removes" it from the storefront.
- Slugs are auto-generated and unique, used in URLs and as a stable
  frontend key (decoupled DRF + Cloudflare Pages frontend needs stable
  slugs, not just numeric IDs).
- Case-insensitive uniqueness on `name` (e.g. "Silk" and "silk" should
  not both be creatable) via a functional index — enforced at the DB
  level, not just in forms, since data will also be touched via
  Django admin/shell.
- `db_index=True` / Meta.indexes on fields used for filtering &
  sorting in the storefront (category, color, fabric, print are all
  query params on the product listing endpoint).
- HEX color validated with a RegexValidator so bad data can't reach
  Cloudflare/DRF responses.
- Category is self-referential (parent/child) to support
  Saree > Silk Sarees > Kanjivaram style nested categories, with
  `on_delete=PROTECT` for parent so deleting a parent category is a
  deliberate, explicit action (reassign children first) rather than
  an accidental cascade that wipes out a whole tree.
- `PROTECT` (not CASCADE) is used wherever a product could reference
  these rows, so you can never delete a Color/Fabric/Print/Category
  that's in use by an existing product/order — the DB refuses it and
  Django raises ProtectedError, which your admin view should catch
  and turn into a friendly error message.
"""

import re

from django.core.validators import RegexValidator
from django.db import models
from django.utils.text import slugify
from django.db.models.functions import Lower


HEX_COLOR_VALIDATOR = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
    message="Enter a valid hex color code, e.g. #C0392B or #FFF.",
)


class TimeStampedModel(models.Model):
    """Abstract base: created_at/updated_at for every table."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SlugMixin:
    """
    Shared save() logic: auto-generate a unique slug from `name` if one
    isn't set. Mixed into models the same way — DRY across Color/
    Fabric/Print/Category.
    """

    slug_source_field = "name"

    def _generate_unique_slug(self):
        base_slug = slugify(getattr(self, self.slug_source_field))
        slug = base_slug
        ModelClass = self.__class__
        counter = 1
        qs = ModelClass.objects.exclude(pk=self.pk)
        while qs.filter(slug=slug).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)


class Category(SlugMixin, TimeStampedModel):
    """
    Product category, e.g. Saree > Silk Sarees > Kanjivaram.
    Self-referential to support nested categories shown in the
    storefront navigation and admin sidebar.
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_category_name_ci",
            ),
        ]

    def __str__(self):
        return self.name


class Color(SlugMixin, TimeStampedModel):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=70, unique=True, blank=True)
    hex_code = models.CharField(
        max_length=7,
        validators=[HEX_COLOR_VALIDATOR],
        help_text="e.g. #C0392B",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_color_name_ci",
            ),
        ]

    def __str__(self):
        return self.name


class Fabric(SlugMixin, TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_fabric_name_ci",
            ),
        ]

    def __str__(self):
        return self.name


class Print(SlugMixin, TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_print_name_ci",
            ),
        ]

    def __str__(self):
        return self.name


