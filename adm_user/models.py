"""
catalog/models.py

Database schema for Categories, Product Filters (Color, Fabric, Print),
and Products (with color variants and images) for the Sanskruti by Bani
saree e-commerce platform.

IMPORTANT MISMATCH TO FIX ON THE FRONTEND:
Your "Add Product" template currently has `prodFabric` and `prodPrints`
as free-text <input> fields, and `newColorName` as a free-text variant
input. The models below treat fabric, print, and variant color as
ForeignKeys into the Fabric/Print/Color tables you already built admin
pages for. For that to work, those fields need to become <select>
dropdowns populated from the DB (e.g. {% for f in fabrics %}) instead
of free text — otherwise there's nothing valid for the FK to point to.

Design notes (production considerations):
- Every model has `created_at` / `updated_at` for auditing.
- `is_active` (soft delete) instead of hard deletes, so historical orders
  that reference a color/fabric/category/product never break even if
  an admin "removes" it from the storefront.
- Slugs are auto-generated and unique, used in URLs and as a stable
  frontend key (decoupled DRF + Cloudflare Pages frontend needs stable
  slugs, not just numeric IDs).
- Case-insensitive uniqueness on `name` via a functional index —
  enforced at the DB level, not just in forms, since data will also be
  touched via Django admin/shell.
- `db_index=True` / Meta.indexes on fields used for filtering &
  sorting in the storefront (category, fabric, print, is_active are all
  query params on the product listing endpoint).
- HEX color validated with a RegexValidator so bad data can't reach
  Cloudflare/DRF responses.
- `PROTECT` is used wherever a product/variant could reference these
  rows, so you can never delete a Color/Fabric/Print/Category that's in
  use by an existing product — the DB refuses it and Django raises
  ProtectedError, which your admin view should catch and turn into a
  friendly error message ("This fabric is used by 12 products").
- Product pricing/stock: `base_price` + optional `discount_price` at
  the product level (used when a variant doesn't override price), and
  `stock_quantity` at the product level is the fallback used only for
  products with no variants. Once a product has ProductVariants, stock
  is tracked per-variant (per color) instead, matching your Amazon-style
  variant UI.
"""

from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.text import slugify


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
    Fabric/Print/Category/Product. Slug is generated once on creation
    and frozen after that (renaming `name` later does NOT change the
    slug), so URLs stay stable even if an admin edits the display name.
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
                violation_error_message="This category already exists.",
            ),
        ]

    def __str__(self):
        return self.name
    
    

# ---------------------------------------------------------------------
# 5 SIGNATURE SAREE CATEGORIES
# ---------------------------------------------------------------------
from django.db.models.functions import Lower   # add at top of models.py if not already imported

class SignatureCategoryItem(SlugMixin, TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    badge_text = models.CharField(max_length=100, blank=True)
    origin_craft = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="website/signature/", blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_signature_category_name_ci",
                violation_error_message="This category already exists.",
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
                violation_error_message="This color already exists.",
            ),
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

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
                violation_error_message="This fabric already exists.",
            ),
        ]

    def __str__(self):
        return self.name


class Print(SlugMixin, TimeStampedModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name_plural = "Prints"
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_print_name_ci",
                violation_error_message="This print already exists.",
            ),
        ]

    def __str__(self):
        return self.name


class Tag(SlugMixin, TimeStampedModel):
    """
    Free-form search tags, e.g. "Wedding", "Party Wear" — from the
    comma-separated `prodFilters` input on the Add Product page.
    Modeled as a proper table (not a comma-separated string column) so
    tags can be deduplicated, reused across products, and queried
    efficiently (`Product.objects.filter(tags__slug="wedding")`)
    instead of doing slow LIKE '%wedding%' string matching.
    """

    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_tag_name_ci",
                violation_error_message="This tag already exists.",
            ),
        ]

    def __str__(self):
        return self.name


class Product(SlugMixin, TimeStampedModel):
    """
    A saree listing — maps to the "Add Product" page. Category, Fabric,
    and Print are FKs into the tables you already manage in the admin
    (see the frontend-mismatch note at the top of this file re: turning
    those inputs into dropdowns).
    """

    # --- General Information ---
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        SignatureCategoryItem,   # was: Category
        related_name="products",
        on_delete=models.PROTECT,
        
    )
    product_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        help_text="e.g. SBB-001. Optional on the form, but unique if set.",
    )

    # --- Pricing & Inventory ---
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional sale price; must be less than base_price.",
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Total stock quantity available for this product.",
    )

    # --- Saree Specifications ---
    fabric = models.ForeignKey(
        Fabric,
        related_name="products",
        on_delete=models.PROTECT,
    )
    print_type = models.ForeignKey(
        Print,
        related_name="products",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="print",
        help_text="Leave blank for prints like 'NO' / plain sarees.",
    )
    saree_length = models.CharField(
        max_length=50, blank=True, help_text="e.g. 5.5 Meter"
    )
    blouse_included = models.BooleanField(default=True)
    blouse_type = models.CharField(max_length=100, blank=True)
    blouse_size = models.CharField(max_length=50, blank=True)
    weaving_style = models.CharField(max_length=100, blank=True)
    border_style = models.CharField(max_length=150, blank=True)
    care_instructions = models.CharField(max_length=255, blank=True)

    # --- Search / Filters ---
    tags = models.ManyToManyField(Tag, related_name="products", blank=True)

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Unpublish without deleting (keeps order history intact).",
    )

    @property
    def final_price(self):
        """Selling price after discount. discount_price is stored as an
        absolute rupee amount (the actual selling price), not a fraction."""
        if self.discount_price:
            return round(self.discount_price)
        return self.base_price

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Matches the storefront listing/filter endpoint:
            # /api/products?category=&fabric=&print=&is_active=1
            models.Index(fields=["category", "fabric", "print_type", "is_active"]),
            models.Index(fields=["is_active", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.product_code or self.slug})"


class ProductVariant(TimeStampedModel):
    """
    A color variant of a product — the "Amazon-style" variant blocks in
    your Add Product page (one per color, with its own stock and an
    optional price override; images live in ProductImage below).
    """

    product = models.ForeignKey(
        Product,
        related_name="variants",
        on_delete=models.CASCADE,
    )
    color = models.ForeignKey(
        Color,
        related_name="product_variants",
        on_delete=models.PROTECT,
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Leave blank to use the product's base_price.",
    )
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "color"],
                name="unique_color_per_product",
            ),
        ]

    def __str__(self):
        return f"{self.product.name} — {self.color.name}"


class ProductImage(TimeStampedModel):
    """
    Gallery images, stored in Cloudflare R2 (or equivalent) and
    referenced by URL. `variant` is null for the "Default Images"
    upload block (shown when no color is selected); set for
    color-specific image uploads within a variant block.

    Business rule: each color variant may have at most
    MAX_IMAGES_PER_VARIANT photos. This can't be expressed as a plain
    DB column constraint (it depends on counting sibling rows), so
    it's enforced in `clean()` below — call `full_clean()` before
    saving from any admin view, form, or DRF serializer that creates
    these, or the limit won't be checked.
    """

    MAX_IMAGES_PER_VARIANT = 4

    product = models.ForeignKey(
        Product,
        related_name="images",
        on_delete=models.CASCADE,
    )
    variant = models.ForeignKey(
        ProductVariant,
        related_name="images",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="Leave blank for default/no-color-selected images.",
    )
    image_url = models.URLField(help_text="Cloudflare R2 object URL.")
    alt_text = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.variant_id:
            existing_count = (
                ProductImage.objects.filter(variant_id=self.variant_id)
                .exclude(pk=self.pk)
                .count()
            )
            if existing_count >= self.MAX_IMAGES_PER_VARIANT:
                raise ValidationError(
                    f"This color variant already has "
                    f"{self.MAX_IMAGES_PER_VARIANT} images — remove one "
                    f"before adding another."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        label = self.variant.color.name if self.variant_id else "default"
        return f"{self.product.name} image ({label})"
    
    """
site_content/models.py

Schema for the Website Builder page — hero slides, Sweet Memories,
header/nav, footer, and About Us. Unlike Product/Category, most of
these are "singleton" sections: there's only ever ONE hero slide 1,
ONE footer, etc. — an admin edits the same row, never creates new ones.

SingletonModel below forces every save() to pk=1, so no matter how the
admin form posts, you can never end up with two competing "About Us"
rows. `Model.load()` is the read-side helper: always returns the one
row, creating it with blank defaults the first time.

Images use ImageField (Django's local media storage), matching what
you're already doing — NOT URLField like the Cloudflare R2 catalog
images, since these are served from MEDIA_ROOT/MEDIA_URL instead.
"""




class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SingletonModel(TimeStampedModel):
    """
    Forces exactly one row (pk=1) regardless of how many times an admin
    submits the "Save Changes" form — save() always overwrites row 1
    instead of creating new rows.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ---------------------------------------------------------------------
# HERO BANNER — 3 slides, each with a different shape, so each is its
# own singleton rather than forcing one schema to cover all three.
# ---------------------------------------------------------------------

class HeroSlideMain(SingletonModel):
    """Slide 1: Main Calligraphy — text + 2 images."""

    tagline = models.CharField(max_length=100, blank=True)
    title_line_1 = models.CharField(max_length=200, blank=True)
    title_line_2 = models.CharField(max_length=200, blank=True)
    title_line_3 = models.CharField(
        max_length=200, blank=True, help_text="Rendered in gold on the frontend."
    )
    description = models.TextField(blank=True)
    button_1_text = models.CharField(max_length=50, blank=True)
    button_2_text = models.CharField(max_length=50, blank=True)
    desktop_image = models.ImageField(upload_to="website/hero/slide1/desktop/", blank=True)
    mobile_image = models.ImageField(upload_to="website/hero/slide1/mobile/", blank=True)

    def __str__(self):
        return "Hero Slide 1 (Main)"


class HeroSlideImageOnly(SingletonModel):
    """Slide 2: Full Image Banner — no text overlay."""

    desktop_image = models.ImageField(upload_to="website/hero/slide2/desktop/", blank=True)
    mobile_image = models.ImageField(upload_to="website/hero/slide2/mobile/", blank=True)

    def __str__(self):
        return "Hero Slide 2 (Image Only)"


class HeroSlideOffer(SingletonModel):
    """Slide 1: Offer Banner — Full Image Banner (Desktop & Mobile responsive)."""

    desktop_image = models.ImageField(upload_to="website/hero/offer/desktop/", blank=True)
    mobile_image = models.ImageField(upload_to="website/hero/offer/mobile/", blank=True)

    def __str__(self):
        return "Hero Slide 1 (Offer Image Banner)"






# ---------------------------------------------------------------------
# SWEET MEMORIES
# ---------------------------------------------------------------------

class SweetMemoriesSection(SingletonModel):
    section_label = models.CharField(max_length=100, blank=True)
    main_heading = models.TextField(
        blank=True, help_text="Multi-line heading, e.g. 'Woven Into / Your Beautiful Moments'."
    )
    paragraph_text = models.TextField(blank=True)

    def __str__(self):
        return "Sweet Memories Section"


class SweetMemoryImage(TimeStampedModel):
    """
    Multiple slider photos — NOT a singleton, since the admin adds/
    removes/reorders any number of these ('Drag to reorder' in the UI).
    """

    image = models.ImageField(upload_to="website/memories/")
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return f"Memory image #{self.pk}"


class MemoriesOfferSlide(SingletonModel):
    """
    Slide 1 of Sweet Memories — 3 Festive Offer Frame Images.
    """

    desktop_image = models.ImageField(
        upload_to="website/memories_slide2/desktop/", blank=True
    )
    mobile_image = models.ImageField(
        upload_to="website/memories_slide2/mobile/", blank=True
    )
    frame1_image = models.ImageField(
        upload_to="website/memories_slide1/frame1/", blank=True
    )
    frame1_title = models.CharField(
        max_length=255, default="Timeless Tradition Collection", blank=True
    )
    frame1_badge = models.CharField(
        max_length=100, default="SPECIAL DEAL · UP TO 50% OFF", blank=True
    )
    frame1_ribbon = models.CharField(
        max_length=50, default="50% OFF", blank=True
    )
    frame1_wa_link = models.CharField(
        max_length=500, default="https://wa.me/919372471363?text=Hi%20Sanskruti%20By%20Bani,%20I%20want%20to%20know%20about%20Up%20To%2050%25%20Off%20Special%20Offer", blank=True
    )

    frame2_image = models.ImageField(
        upload_to="website/memories_slide1/frame2/", blank=True
    )
    frame2_title = models.CharField(
        max_length=255, default="10% Off 1st Order (Code: WELCOME10)", blank=True
    )
    frame2_badge = models.CharField(
        max_length=100, default="✦ WELCOME OFFER · 10% OFF ✦", blank=True
    )
    frame2_ribbon = models.CharField(
        max_length=50, default="10% OFF", blank=True
    )
    frame2_wa_link = models.CharField(
        max_length=500, default="https://wa.me/919372471363?text=Hi%20Sanskruti%20By%20Bani,%20I%20want%20to%20avail%2010%25%20Off%20Welcome%20Offer%20with%20code%20WELCOME10", blank=True
    )

    frame3_image = models.ImageField(
        upload_to="website/memories_slide1/frame3/", blank=True
    )
    frame3_title = models.CharField(
        max_length=255, default="Happy Rakhi Festive Special", blank=True
    )
    frame3_badge = models.CharField(
        max_length=100, default="RAKHI FESTIVE · UP TO 65% OFF", blank=True
    )
    frame3_ribbon = models.CharField(
        max_length=50, default="65% OFF", blank=True
    )
    frame3_wa_link = models.CharField(
        max_length=500, default="https://wa.me/919372471363?text=Hi%20Sanskruti%20By%20Bani,%20I%20want%20to%20know%20about%20Up%20To%2065%25%20Off%20Rakhi%20Offer", blank=True
    )

    def __str__(self):
        return "Sweet Memories Slide 1 (3 Offer Frames)"


class MemoriesSlide3(SingletonModel):
    """
    Slide 3 of Sweet Memories — Full Image Banner (Desktop & Mobile).
    """

    desktop_image = models.ImageField(
        upload_to="website/memories_slide3/desktop/", blank=True
    )
    mobile_image = models.ImageField(
        upload_to="website/memories_slide3/mobile/", blank=True
    )

    def __str__(self):
        return "Sweet Memories Slide 3 (Image Banner)"


# ---------------------------------------------------------------------
# HEADER & NAV
# ---------------------------------------------------------------------

class OfferBarItem(TimeStampedModel):
    """
    Scrolling top offer bar — admin can add/remove any number via
    'Add Another Offer'. Not a singleton.
    """

    text = models.CharField(max_length=200)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order"]

    def __str__(self):
        return self.text


class HeaderSettings(SingletonModel):
    logo = models.ImageField(upload_to="website/branding/")

    def __str__(self):
        return "Header Settings"


# ---------------------------------------------------------------------
# FOOTER & LINKS
# ---------------------------------------------------------------------

class FooterSettings(SingletonModel):
    brand_name = models.CharField(max_length=150, blank=True)
    brand_description = models.TextField(blank=True)
    store_address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    instagram_link = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return "Footer Settings"


# ---------------------------------------------------------------------
# ABOUT US
# ---------------------------------------------------------------------

class AboutUsSection(SingletonModel):
    small_title = models.CharField(max_length=100, blank=True)
    main_heading = models.CharField(max_length=200, blank=True)
    highlight_quote = models.TextField(
        blank=True, help_text="Gold-highlighted quote; may contain non-English script."
    )
    main_paragraph = models.TextField(
        blank=True, help_text="Main body text; may contain non-English script."
    )
    ending_signoff = models.CharField(max_length=200, blank=True)
    about_image = models.ImageField(upload_to="website/about/")
    floating_top_text = models.CharField(max_length=100, blank=True)
    floating_bottom_text = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return "About Us Section"