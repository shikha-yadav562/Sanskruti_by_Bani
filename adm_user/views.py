
import json
import uuid
import csv
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.core.validators import get_available_image_extensions

from django.db import models, IntegrityError, transaction
from django.db.models import ProtectedError, Q, Case, When, Prefetch

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods

from .models import Category, Color, Fabric, Print, Tag, Product, ProductVariant, ProductImage, HeroSlideMain, HeroSlideImageOnly, HeroSlideOffer, SweetMemoriesSection, SweetMemoryImage, MemoriesOfferSlide, MemoriesSlide3, OfferBarItem, HeaderSettings, FooterSettings, AboutUsSection,SignatureCategoryItem
from decimal import Decimal, InvalidOperation

from PIL import Image, UnidentifiedImageError
from user.models import ProductReview
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


FORM_TEMPLATE = "adm_user/products.html"


# ============================================================
# PRODUCTION IMAGE VALIDATION
# ============================================================

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}

# Product/signature images
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

# Website builder images
MAX_IMAGE_SIZE_MB = 25
MAX_BUILDER_IMAGE_SIZE = MAX_IMAGE_SIZE_MB * 1024 * 1024

# Maximum decoded image dimensions
MAX_IMAGE_WIDTH = 8000
MAX_IMAGE_HEIGHT = 8000

# Maximum decoded pixels
MAX_IMAGE_PIXELS = 40_000_000  # 40 megapixels

MAX_MEMORY_IMAGES = 20

# ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
# MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
# ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}

# # WEBSITE BUILDER
# MAX_IMAGE_SIZE_MB = 25  
# MAX_MEMORY_IMAGES = 20  

def dashboard(request):
    return render(request, 'adm_user/dashboard.html')


# Views For CATEGORY
def categories(request):
    context = {
        "signature_categories": SignatureCategoryItem.objects.all(),
    }
    return render(request, 'adm_user/categories.html', context)


# @require_http_methods(["GET", "POST"])
# def category_list_create(request):
#     if request.method == "GET":
#         categories = Category.objects.filter(is_active=True).order_by("created_at")
#         data = [{"id": c.id, "name": c.name, "slug": c.slug} for c in categories]
#         return JsonResponse({"categories": data})

#     # POST — create a new category
#     try:
#         payload = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid request."}, status=400)

#     name = (payload.get("name") or "").strip()
#     if not name:
#         return JsonResponse({"error": "Category name is required."}, status=400)

#     category = Category(name=name)
#     try:
#         category.full_clean()
#         with transaction.atomic():
#             category.save()
#     except ValidationError as e:
#         return JsonResponse({"error": " ".join(e.messages)}, status=400)
#     except IntegrityError:
#         return JsonResponse({"error": "This category already exists."}, status=409)

#     return JsonResponse(
#         {"id": category.id, "name": category.name, "slug": category.slug}, status=201
#     )

# @require_http_methods(["PUT"])
# def category_update(request, pk):
#     try:
#         category = Category.objects.get(pk=pk, is_active=True)
#     except Category.DoesNotExist:
#         return JsonResponse({"error": "Category not found."}, status=404)

#     try:
#         payload = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid request."}, status=400)

#     name = (payload.get("name") or "").strip()
#     if not name:
#         return JsonResponse({"error": "Category name is required."}, status=400)

#     if name != category.name:
#         category.name = name
#         category.slug = ""  # forces the mixin to regenerate it on save()

#     try:
#         category.full_clean()
#         with transaction.atomic():
#             category.save()
#     except ValidationError as e:
#         return JsonResponse({"error": " ".join(e.messages)}, status=400)
#     except IntegrityError:
#         return JsonResponse({"error": "Another category already has this name."}, status=409)

#     return JsonResponse({"id": category.id, "name": category.name, "slug": category.slug})

# @require_http_methods(["DELETE"])
# def category_delete(request, pk):
#     try:
#         category = Category.objects.get(pk=pk)
#     except Category.DoesNotExist:
#         return JsonResponse({"error": "Category not found."}, status=404)

#     try:
#         category.delete()
#     except IntegrityError:
#         return JsonResponse(
#             {"error": "This category is linked to existing products and can't be deleted."},
#             status=409,
#         )
#     return JsonResponse({"deleted": True})


# ----------------- Views for FILTERS -----------------
def filters(request):
    return render(request, 'adm_user/filters.html')


# ==========================================
# COLORS
# ==========================================
 
# @staff_member_required
@require_http_methods(["GET", "POST"])
def color_list_create(request):
    if request.method == "GET":
        data = list(
            Color.objects.filter(is_active=True).order_by("created_at").values("id", "name", "hex_code", "slug")
    )
        return JsonResponse({"colors": data})
    
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    hex_code = (payload.get("hex_code") or "").strip()
    if not name:
        return JsonResponse({"error": "Color name is required."}, status=400)

    color = Color(name=name, hex_code=hex_code)
    try:
        color.full_clean()
        with transaction.atomic():
            color.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "This color already exists."}, status=409)

    return JsonResponse(
        {"id": color.id, "name": color.name, "hex_code": color.hex_code, "slug": color.slug}, status=201
    )


@require_http_methods(["PUT"])
def color_update(request, pk):
    try:
        color = Color.objects.get(pk=pk, is_active=True)
    except Color.DoesNotExist:
        return JsonResponse({"error": "Color not found."}, status=404)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    hex_code = (payload.get("hex_code") or "").strip()
    if not name:
        return JsonResponse({"error": "Color name is required."}, status=400)

    if name != color.name:
        color.name = name
        color.slug = ""  # forces the mixin to regenerate it on save()
    if "hex_code" in payload:
        color.hex_code = (payload.get("hex_code") or "").strip()

    try:
        color.full_clean()
        with transaction.atomic():
            color.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "Another color already has this name."}, status=409)

    return JsonResponse({"id": color.id, "name": color.name, "hex_code": color.hex_code, "slug": color.slug})


@require_http_methods(["DELETE"])
def color_delete(request, pk):
    try:
        color = Color.objects.get(pk=pk, is_active=True)
    except Color.DoesNotExist:
        return JsonResponse({"error": "Color not found."}, status=404)

    try:
        color.delete()
    except ProtectedError:
        return JsonResponse(
            {"error": "This color is linked to existing products and can't be deleted."},
            status=409,
        )
    return JsonResponse({"deleted": True})

# ==========================================
# FABRICS
# ==========================================
 
@require_http_methods(["GET", "POST"])
def fabric_list_create(request):
    if request.method == "GET":
        fabrics = list(
            Fabric.objects.filter(is_active=True).order_by("created_at").values("id", "name", "slug")
        )
        return JsonResponse({"fabrics": fabrics})

    # POST — create a new fabric
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Fabric name is required."}, status=400)

    fabric = Fabric(name=name)
    try:
        fabric.full_clean()
        with transaction.atomic():
            fabric.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "This fabric already exists."}, status=409)

    return JsonResponse({"id": fabric.id, "name": fabric.name, "slug": fabric.slug}, status=201)


@require_http_methods(["PUT"])
def fabric_update(request, pk):
    try:
        fabric = Fabric.objects.get(pk=pk, is_active=True)
    except Fabric.DoesNotExist:
        return JsonResponse({"error": "Fabric not found."}, status=404)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Fabric name is required."}, status=400)

    if name != fabric.name:
        fabric.name = name
        fabric.slug = ""  # forces the mixin to regenerate it on save()

    try:
        fabric.full_clean()
        with transaction.atomic():
            fabric.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "Another fabric already has this name."}, status=409)

    return JsonResponse({"id": fabric.id, "name": fabric.name, "slug": fabric.slug})


@require_http_methods(["DELETE"])
def fabric_delete(request, pk):
    try:
        fabric = Fabric.objects.get(pk=pk, is_active=True)
    except Fabric.DoesNotExist:
        return JsonResponse({"error": "Fabric not found."}, status=404)

    try:
        fabric.delete()
    except ProtectedError:
        return JsonResponse(
            {"error": "This fabric is linked to existing products and can't be deleted."},
            status=409,
        )
    return JsonResponse({"deleted": True})
 
# ==========================================
# PRINTS
# ==========================================

@require_http_methods(["GET", "POST"])
def print_list_create(request):
    if request.method == "GET":
        data = list(
            Print.objects.filter(is_active=True).order_by("created_at").values("id", "name", "slug")
        )
        return JsonResponse({"prints": data})

    # POST — create a new print
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Print name is required."}, status=400)

    print_obj = Print(name=name)
    try:
        print_obj.full_clean()
        with transaction.atomic():
            print_obj.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "This print already exists."}, status=409)

    return JsonResponse({"id": print_obj.id, "name": print_obj.name, "slug": print_obj.slug}, status=201)


@require_http_methods(["PUT"])
def print_update(request, pk):
    try:
        print_obj = Print.objects.get(pk=pk, is_active=True)
    except Print.DoesNotExist:
        return JsonResponse({"error": "Print not found."}, status=404)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Print name is required."}, status=400)

    if name != print_obj.name:
        print_obj.name = name
        print_obj.slug = ""  # forces the mixin to regenerate it on save()

    try:
        print_obj.full_clean()
        with transaction.atomic():
            print_obj.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "Another print already has this name."}, status=409)

    return JsonResponse({"id": print_obj.id, "name": print_obj.name, "slug": print_obj.slug})


@require_http_methods(["DELETE"])
def print_delete(request, pk):
    try:
        print_obj = Print.objects.get(pk=pk, is_active=True)
    except Print.DoesNotExist:
        return JsonResponse({"error": "Print not found."}, status=404)

    try:
        print_obj.delete()
    except ProtectedError:
        return JsonResponse(
            {"error": "This print is linked to existing products and can't be deleted."},
            status=409,
        )
    return JsonResponse({"deleted": True})


# ==========================================
# TAGS
# ==========================================

@require_http_methods(["GET", "POST"])
def tag_list_create(request):
    if request.method == "GET":
        data = list(
            Tag.objects.filter().order_by("created_at").values("id", "name", "slug")
        )
        return JsonResponse({"tags": data})

    # POST — create a new tag
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Tag name is required."}, status=400)

    tag = Tag(name=name)
    try:
        tag.full_clean()
        with transaction.atomic():
            tag.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "This tag already exists."}, status=409)

    return JsonResponse({"id": tag.id, "name": tag.name, "slug": tag.slug}, status=201)


@require_http_methods(["PUT"])
def tag_update(request, pk):
    try:
        tag = Tag.objects.get(pk=pk)
    except Tag.DoesNotExist:
        return JsonResponse({"error": "Tag not found."}, status=404)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Tag name is required."}, status=400)

    if name != tag.name:
        tag.name = name
        tag.slug = ""  # forces the mixin to regenerate it on save()

    try:
        tag.full_clean()
        with transaction.atomic():
            tag.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "Another tag already has this name."}, status=409)

    return JsonResponse({"id": tag.id, "name": tag.name, "slug": tag.slug})


@require_http_methods(["DELETE"])
def tag_delete(request, pk):
    try:
        tag = Tag.objects.get(pk=pk)
    except Tag.DoesNotExist:
        return JsonResponse({"error": "Tag not found."}, status=404)

    try:
        tag.delete()
    except ProtectedError:
        return JsonResponse(
            {"error": "This tag is linked to existing products and can't be deleted."},
            status=409,
        )
    return JsonResponse({"deleted": True})

# ==========================================
# PRODUCTS
# ==========================================

def _delete_stored_image(image_url):
    """Delete the actual file from storage, given the full URL saved on ProductImage."""
    if not image_url:
        return
    relative_path = urlparse(image_url).path  # e.g. "/media/products/abc123_photo.jpeg"
    if relative_path.startswith(settings.MEDIA_URL):
        relative_path = relative_path[len(settings.MEDIA_URL):] 
    default_storage.delete(relative_path)

@require_http_methods(["POST"])
def product_image_delete(request, image_id):
    image = get_object_or_404(ProductImage, pk=image_id)
    _delete_stored_image(image.image_url)
    image.delete()
    return JsonResponse({"ok": True, "id": image.id})

@require_http_methods(["POST"])
def product_variant_delete(request, variant_id):
    variant = get_object_or_404(ProductVariant, pk=variant_id)
    variant.is_active = False
    variant.save(update_fields=["is_active"])
    for url in variant.images.values_list("image_url", flat=True):
        _delete_stored_image(url)
    variant.images.all().delete()
    return JsonResponse({"ok": True, "id": variant.id})

@require_http_methods(["GET"])
def products(request):
    qs = (
        Product.objects.filter(is_active=True)
        .select_related("category", "fabric")
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.filter(variant__isnull=True).order_by("display_order"),
                to_attr="default_images",
            )
        )
        .order_by("-created_at")
    )

    category_id = request.GET.get("category", "").strip()
    stock = request.GET.get("stock", "").strip()
    search = request.GET.get("search", "").strip()

    if category_id:
        qs = qs.filter(category_id=category_id)
    if stock == "out":
        qs = qs.filter(stock_quantity=0)
    elif stock == "low":
        qs = qs.filter(stock_quantity__gt=0, stock_quantity__lt=5)
    elif stock == "in":
        qs = qs.filter(stock_quantity__gte=5)
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(product_code__icontains=search))

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    querydict = request.GET.copy()
    querydict.pop("page", None)
    base_qs = querydict.urlencode()

    context = {
        "products": page_obj,
        "page_obj": page_obj,
        "selected_category": category_id,
        "selected_stock": stock,
        "search_query": search,
        "base_qs": base_qs,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "adm_user/product_table.html", context)

    context.update(_product_form_context())
    return render(request, FORM_TEMPLATE, context)

def _validate_image(file_obj, max_size=MAX_IMAGE_SIZE):
    """
    Production-safe image validation.

    Validates:
    - declared MIME type
    - file size
    - actual image contents
    - actual image format
    - image dimensions
    - total decoded pixels

    Does NOT write anything to storage.
    """

    if not file_obj:
        raise ValueError("No image file was provided.")

    # --------------------------------------------------------
    # 1. MIME type
    # --------------------------------------------------------
    content_type = (getattr(file_obj, "content_type", "") or "").lower()

    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(
            "Only JPEG, PNG, or WEBP images are allowed."
        )

    # --------------------------------------------------------
    # 2. File size
    # --------------------------------------------------------
    if file_obj.size > max_size:
        max_mb = max_size / (1024 * 1024)

        raise ValueError(
            f"Image files must be under {max_mb:g}MB."
        )

    # --------------------------------------------------------
    # 3. Verify actual image contents
    # --------------------------------------------------------
    try:
        file_obj.seek(0)

        image = Image.open(file_obj)

        # Force Pillow to verify the image structure.
        image.verify()

        file_obj.seek(0)

        # Re-open because verify() invalidates the image object.
        image = Image.open(file_obj)

        actual_format = image.format

        # ----------------------------------------------------
        # 4. Verify actual format
        # ----------------------------------------------------
        if actual_format not in ALLOWED_IMAGE_FORMATS:
            raise ValueError(
                "Only JPEG, PNG, or WEBP images are allowed."
            )

        # ----------------------------------------------------
        # 5. Dimension validation
        # ----------------------------------------------------
        width, height = image.size

        if width <= 0 or height <= 0:
            raise ValueError("Image dimensions are invalid.")

        if width > MAX_IMAGE_WIDTH:
            raise ValueError(
                f"Image width cannot exceed {MAX_IMAGE_WIDTH}px."
            )

        if height > MAX_IMAGE_HEIGHT:
            raise ValueError(
                f"Image height cannot exceed {MAX_IMAGE_HEIGHT}px."
            )

        # ----------------------------------------------------
        # 6. Pixel-count protection
        # ----------------------------------------------------
        total_pixels = width * height

        if total_pixels > MAX_IMAGE_PIXELS:
            raise ValueError(
                "Image resolution is too large. "
                "Please upload a smaller image."
            )

    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ValueError(
            "The uploaded file is not a valid JPEG, PNG, or WEBP image."
        )

    finally:
        file_obj.seek(0)
        



def _store_image(file_obj, request=None):
    safe_name = get_valid_filename(file_obj.name)
    path = default_storage.save(f"products/{uuid.uuid4().hex}_{safe_name}", file_obj)
    url = default_storage.url(path)
    if request is not None and url.startswith("/"):
        url = request.build_absolute_uri(url)
    return url

def _cleanup_files(paths):
    for path in paths:
        if not path:
            continue
        try:
            default_storage.delete(path)
        except Exception:
            logger.exception(
                "Failed to clean up uploaded file: %s",
                path,
            )


def _product_form_context(product=None):
    context = {
        "categories": SignatureCategoryItem.objects.filter(is_active=True),
        "fabrics": Fabric.objects.filter(is_active=True),
        "prints": Print.objects.filter(is_active=True),
        "colors": Color.objects.filter(is_active=True),
        "tags": Tag.objects.all(),
    }
    if product is not None and product.pk:
        context["product_tag_ids"] = set(
            product.tags.values_list("id", flat=True)
        )
        context["existing_variant_color_ids"] = set(
            product.variants.filter(is_active=True).values_list("color_id", flat=True)
        )
    return context

def _parse_bool(value):
    return str(value).strip().lower() in ("yes", "true", "1", "on")

def _get_selected_tags(request):
    tag_ids = [tid for tid in request.POST.getlist("tags") if tid]
    return Tag.objects.filter(id__in=tag_ids)

def _save_product_fields(product, request):
    post = request.POST
    product.name = post.get("name", "").strip()
    if not product.name:
        raise ValueError("Product name is required.")
    product.description = post.get("description", "").strip()
    product.product_code = post.get("product_code", "").strip() or None

    category_id = post.get("category")
    if not category_id:
        raise ValueError("Category is required.")
    try:
        product.category = SignatureCategoryItem.objects.get(pk=category_id, is_active=True)
    except (SignatureCategoryItem.DoesNotExist, ValueError, TypeError):
        raise ValueError("Selected category is invalid or no longer active.")

    fabric_id = post.get("fabric")
    if not fabric_id:
        raise ValueError("Fabric is required.")
    try:
        product.fabric = Fabric.objects.get(pk=fabric_id, is_active=True)
    except (Fabric.DoesNotExist, ValueError, TypeError):
        raise ValueError("Selected fabric is invalid or no longer active.")

    print_id = post.get("print_type")
    if print_id:
        try:
            product.print_type = Print.objects.get(pk=print_id, is_active=True)
        except (Print.DoesNotExist, ValueError, TypeError):
            raise ValueError("Selected print type is invalid or no longer active.")
    else:
        product.print_type = None

    try:
        base_price = Decimal(post.get("base_price") or "0")
        discount_price_raw = post.get("discount_price")
        discount_price = Decimal(discount_price_raw) if discount_price_raw else None
        stock_quantity = int(post.get("stock_quantity") or 0)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("Price and stock fields must be valid numbers.")

    if discount_price is not None and discount_price >= base_price:
        raise ValueError("Discount price must be less than the base price.")

    product.base_price = base_price
    product.discount_price = discount_price
    product.stock_quantity = stock_quantity

    product.saree_length = post.get("saree_length", "").strip()
    product.blouse_included = _parse_bool(post.get("blouse_included", "Yes"))
    product.blouse_type = post.get("blouse_type", "").strip()
    product.blouse_size = post.get("blouse_size", "").strip()
    product.weaving_style = post.get("weaving_style", "").strip()
    product.border_style = post.get("border_style", "").strip()
    product.care_instructions = post.get("care_instructions", "").strip()

def _save_variants_and_images(product, request):
    color_ids = request.POST.getlist("variant_color_id")
    prices = request.POST.getlist("variant_price")
    default_image_files = request.FILES.getlist("default_images")

    requested_color_ids = [cid for cid in color_ids if cid]
    colors_by_id = {
        str(c.id): c
        for c in Color.objects.filter(id__in=requested_color_ids, is_active=True)
    }

    # ---- PHASE 1: validate everything, write nothing to storage yet ----
    planned_variants = []  # (color, price, [image_files])
    for color_id, price in zip(color_ids, prices):
        if not color_id:
            continue
        color = colors_by_id.get(color_id)
        if color is None:
            raise ValueError("Invalid or inactive color selected.")

        try:
            variant_price = Decimal(price) if price else None
        except InvalidOperation:
            raise ValueError(f"Invalid price for variant color {color.name}.")

        image_files = request.FILES.getlist(f"variant_images_{color_id}")
        for f in image_files:
            _validate_image(f)

        planned_variants.append((color, variant_price, image_files))

    for f in default_image_files:
        _validate_image(f)

    # ---- PHASE 2: everything validated — safe to save DB rows + write files ----
    kept_variant_ids = []
    for color, variant_price, image_files in planned_variants:
        variant, _ = ProductVariant.objects.get_or_create(product=product, color=color)
        variant.price = variant_price
        variant.is_active = True
        variant.full_clean()
        variant.save()

        kept_variant_ids.append(variant.id)

        next_order = variant.images.count()
        for image_file in image_files:
            url = _store_image(image_file, request)
            ProductImage.objects.create(
                product=product,
                variant=variant,
                image_url=url,
                display_order=next_order,
            )
            next_order += 1

    dropped_variants = product.variants.exclude(id__in=kept_variant_ids)
    for variant in dropped_variants:
        for url in variant.images.values_list("image_url", flat=True):
            _delete_stored_image(url)
        variant.images.all().delete()
    dropped_variants.update(is_active=False)

    next_order = product.images.filter(variant__isnull=True).count()
    for image_file in default_image_files:
        url = _store_image(image_file, request)
        ProductImage.objects.create(
            product=product,
            variant=None,
            image_url=url,
            display_order=next_order,
        )
        next_order += 1

def _handle_save_errors(request, exc, product=None):
    if isinstance(exc, IntegrityError):
        messages.error(
            request,
            "Couldn't save that product — check the product code isn't already "
            "used, and that the same color wasn't added twice.",
        )
    else:
        messages.error(request, str(exc))
    context = _product_form_context(product)   # was: _product_form_context()
    if product is not None:
        context["product"] = product
    return render(request, FORM_TEMPLATE, context)

@require_http_methods(["GET"])
def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category", "fabric", "print_type").prefetch_related(
            "tags",
            "variants__color",
            "variants__images",
            "images",
        ),
        slug=slug,
        is_active=True,
    )
    context = {
        "product": product,
        "default_images": product.images.filter(variant__isnull=True),
        "variants": product.variants.filter(is_active=True),
    }
    return render(request, "adm_user/product_detail.html", context)


@require_http_methods(["GET", "POST"])
def product_create(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                product = Product()
                _save_product_fields(product, request)
                product.save()
                product.tags.set(_get_selected_tags(request))
                _save_variants_and_images(product, request)
        except (IntegrityError, ValueError, ValidationError) as exc:
            return _handle_save_errors(request, exc, product=product)

        messages.success(request, f'"{product.name}" was added to the catalog.')
        return redirect("adm_user:products")

    return render(request, FORM_TEMPLATE, _product_form_context())

@require_http_methods(["GET", "POST"])
def product_update(request, slug):
    product = get_object_or_404(Product, slug=slug)

    if request.method == "POST":
        try:
            with transaction.atomic():
                _save_product_fields(product, request)
                product.save()
                product.tags.set(_get_selected_tags(request))
                _save_variants_and_images(product, request)
        except (IntegrityError, ValueError, ValidationError) as exc:
            return _handle_save_errors(request, exc, product=product)

        messages.success(request, f'"{product.name}" was updated.')
        return redirect("adm_user:products")

    context = _product_form_context(product)   # was: _product_form_context() + separate line
    context["product"] = product
    return render(request, FORM_TEMPLATE, context)


@require_http_methods(["POST"])
def product_delete(request, slug):
    product = get_object_or_404(Product, slug=slug)
    product_id = product.id
    product_name = product.name
    image_urls = list(ProductImage.objects.filter(product=product).values_list("image_url", flat=True))

    try:
        with transaction.atomic():
            product.delete()
    except ProtectedError:
        error = "This product can't be deleted because it's linked to existing orders."
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": error}, status=409)
        messages.error(request, error)
        return redirect("adm_user:products")

    for url in image_urls:
        _delete_stored_image(url)

    messages.success(request, f'"{product_name}" was permanently deleted.')
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "id": product_id})
    return redirect("adm_user:products")


# ==========================================
# EXPORT
# ==========================================

def _csv_safe(value):
    value = str(value)
    if value and value[0] in ("=", "+", "-", "@"):
        return "'" + value
    return value

@require_http_methods(["GET"])
def products_export(request):
    """
    Exports the product catalog as a CSV file.
    Honours the same filters as the on-page table (category, stock, search)
    when they're passed as query params, e.g. ?category=3&stock=low&search=silk
    """

    qs = Product.objects.filter(is_active=True).select_related("category", "fabric", "print_type")

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)

    stock = request.GET.get("stock")
    if stock == "out":
        qs = qs.filter(stock_quantity=0)
    elif stock == "low":
        qs = qs.filter(stock_quantity__gt=0, stock_quantity__lt=5)
    elif stock == "in":
        qs = qs.filter(stock_quantity__gte=5)

    search = request.GET.get("search")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(product_code__icontains=search))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="products_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Name", "Product Code", "Category", "Fabric", "Print Type",
        "Base Price", "Discount Price", "Stock Quantity", "Stock Status", "Active",
    ])
    for p in qs:
        if p.stock_quantity == 0:
            stock_status = "Out of Stock"
        elif p.stock_quantity < 5:
            stock_status = "Low Stock"
        else:
            stock_status = "In Stock"

        writer.writerow([
            _csv_safe(p.name),
            _csv_safe(p.product_code or ""),
            p.category.name if p.category else "",
            p.fabric.name if p.fabric else "",
            p.print_type.name if p.print_type else "",
            p.base_price,
            p.discount_price if p.discount_price is not None else "",
            p.stock_quantity,
            stock_status,
            "Yes" if p.is_active else "No",
        ])

    return response

# ==========================================
# STOCK UPDATE
# ==========================================

@require_http_methods(["POST"])
def product_stock_update(request, slug):
    """
    Inline stock edit from the products list.
    Body: {"stock_quantity": 12}
    """
    product = get_object_or_404(Product, slug=slug)

    try:
        payload = json.loads(request.body)
        raw_stock = payload.get("stock_quantity")
        new_stock = int(raw_stock)
        if float(raw_stock) != new_stock:
            raise ValueError("Stock quantity must be a whole number.")
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Enter a valid stock quantity."}, status=400)

    if new_stock < 0:
        return JsonResponse({"ok": False, "error": "Stock can't be negative."}, status=400)

    product.stock_quantity = new_stock
    try:
        product.full_clean(
            validate_unique=False, 
            exclude=[ f.name for f in product._meta.fields if f.name != "stock_quantity"]
        )
        product.save(update_fields=["stock_quantity"])
    except ValidationError as e:
        return JsonResponse({"ok": False, "error": " ".join(e.messages)}, status=400)

    if new_stock == 0:
        stock_status = "out"
    elif new_stock < 5:
        stock_status = "low"
    else:
        stock_status = "in"

    return JsonResponse({
        "ok": True,
        "id": product.id,
        "stock_quantity": product.stock_quantity,
        "stock_status": stock_status,
    })


# ==========================================
# WEBSITE BUILDER
# ==========================================
 
 
def _validate_image_file(f):
    """
    Website Builder image validation.

    Uses the common image validator but allows the
    Website Builder's larger 25MB upload limit.
    """
    try:
        _validate_image(
            f,
            max_size=MAX_BUILDER_IMAGE_SIZE
        )
    except ValueError as e:
        raise ValidationError(str(e))
 
# ---------------------------------------------------------------------
# PAGE LOAD
# ---------------------------------------------------------------------
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
def website_builder(request):
    
    context = {
        "hero_main": HeroSlideMain.load(),
        "hero_image_only": HeroSlideImageOnly.load(),
        "hero_offer": HeroSlideOffer.load(),
        "memories": SweetMemoriesSection.load(),
        "memory_images": SweetMemoryImage.objects.all(),
        "memories_offer_slide": MemoriesOfferSlide.load(),
        "memories_slide3": MemoriesSlide3.load(),
        "offer_items": OfferBarItem.objects.all(),
        "header": HeaderSettings.load(),
        "footer": FooterSettings.load(),
        "about": AboutUsSection.load(),
        "signature_categories": SignatureCategoryItem.objects.all(),
    }
    return render(request, "adm_user/website_builder.html", context)
 
 
# ---------------------------------------------------------------------
# ALL SECTION SAVES
# ---------------------------------------------------------------------
 
def _save_singleton_text_fields(instance, data, fields):
    changed_fields = [field for field in fields if field in data]
    for field in changed_fields:
        setattr(instance, field, data[field])

    instance.full_clean(exclude=[f.name for f in instance._meta.fields if isinstance(f, models.ImageField)])
    instance.save(update_fields=changed_fields or None)


def _save_singleton_image(instance, files, field_name, cleanup_files):
    f = files.get(field_name)

    if not f:
        return

    _validate_image_file(f)

    old_file = getattr(instance, field_name)
    old_file_name = old_file.name if old_file else None

    setattr(instance, field_name, f)

    try:
        instance.full_clean(
            exclude=[
                field.name
                for field in instance._meta.fields
                if isinstance(field, models.ImageField)
            ]
        )

        instance.save(update_fields=[field_name])

        new_file_name = getattr(instance, field_name).name

        # Track the new file so the OUTER transaction can clean it up
        # if a later operation causes the transaction to roll back.
        if new_file_name and new_file_name != old_file_name:
            cleanup_files.append(new_file_name)

        # Old file should only be removed after the DB transaction commits.
        if old_file_name and old_file_name != new_file_name:
            transaction.on_commit(
                lambda old_name=old_file_name:
                    default_storage.delete(old_name)
            )

    except Exception:
        new_file = getattr(instance, field_name)

        if new_file and new_file.name != old_file_name:
            try:
                default_storage.delete(new_file.name)
            except Exception:
                logger.exception(
                    "Failed to clean up image after save failure: %s",
                    new_file.name,
                )

        setattr(instance, field_name, old_file)
        raise

# ==========================================
# WEBSITE BUILDER - HERO BANNER
# ==========================================

# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented

@require_http_methods(["POST"])
def save_hero_main(request):
    cleanup_files = []

    try:
        with transaction.atomic():
            hero = HeroSlideMain.load()

            _save_singleton_text_fields(
                hero,
                request.POST,
                [
                    "tagline", "title_line_1", "title_line_2", "title_line_3",
                    "description", "button_1_text", "button_2_text",
                ],
            )

            _save_singleton_image(
                hero,
                request.FILES,
                "desktop_image",
                cleanup_files,
            )

            _save_singleton_image(
                hero,
                request.FILES,
                "mobile_image",
                cleanup_files,
            )

    except ValidationError as e:
        _cleanup_files(cleanup_files)
        return JsonResponse({"error": " ".join(e.messages)}, status=400)

    except Exception:
        _cleanup_files(cleanup_files)
        logger.exception("Error saving Main Hero Slide")
        return JsonResponse(
            {"error": "Something went wrong saving the Main Hero Slide."},
            status=500,
        )

    return JsonResponse({"saved": True})
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_hero_image_only(request):
    cleanup_files = []

    try:
        with transaction.atomic():
            hero = HeroSlideImageOnly.load()

            _save_singleton_image(
                hero,
                request.FILES,
                "desktop_image",
                cleanup_files,
            )

            _save_singleton_image(
                hero,
                request.FILES,
                "mobile_image",
                cleanup_files,
            )

    except ValidationError as e:
        _cleanup_files(cleanup_files)

        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        _cleanup_files(cleanup_files)

        logger.exception("Error saving Hero Image Only")

        return JsonResponse(
            {
                "error": (
                    "Something went wrong saving the "
                    "Hero Image Only section."
                )
            },
            status=500,
        )

    return JsonResponse({"saved": True})
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_hero_offer(request):
    cleanup_files = []

    try:
        with transaction.atomic():
            hero = HeroSlideOffer.load()

            _save_singleton_image(
                hero,
                request.FILES,
                "desktop_image",
                cleanup_files,
            )

            _save_singleton_image(
                hero,
                request.FILES,
                "mobile_image",
                cleanup_files,
            )

    except ValidationError as e:
        _cleanup_files(cleanup_files)
        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        _cleanup_files(cleanup_files)
        logger.exception("Error saving Hero Offer Banner")
        return JsonResponse(
            {"error": "Something went wrong saving the Hero Offer Banner."},
            status=500,
        )

    return JsonResponse({"saved": True})
 

# ==========================================
# WEBSITE BUILDER - SWEET MEMORIES
# ==========================================

# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_memories_section(request):
    try:
        with transaction.atomic():
            section = SweetMemoriesSection.load()

            _save_singleton_text_fields(
                section,
                request.POST,
                ["section_label", "main_heading", "paragraph_text"],
            )

    except ValidationError as e:
        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        logger.exception("Error saving Sweet Memories section")
        return JsonResponse(
            {
                "error": "Something went wrong saving Sweet Memories section."
            },
            status=500,
        )

    return JsonResponse({"saved": True})
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_memories_offer_slide(request):
    cleanup_files = []

    try:
        with transaction.atomic():
            slide = MemoriesOfferSlide.load()

            _save_singleton_text_fields(
                slide,
                request.POST,
                [
                    "frame1_title",
                    "frame1_badge",
                    "frame1_ribbon",
                    "frame1_wa_link",
                    "frame2_title",
                    "frame2_badge",
                    "frame2_ribbon",
                    "frame2_wa_link",
                    "frame3_title",
                    "frame3_badge",
                    "frame3_ribbon",
                    "frame3_wa_link",
                ],
            )

            _save_singleton_image(
                slide,
                request.FILES,
                "desktop_image",
                cleanup_files,
            )

            _save_singleton_image(
                slide,
                request.FILES,
                "mobile_image",
                cleanup_files,
            )

            _save_singleton_image(
                slide,
                request.FILES,
                "frame1_image",
                cleanup_files,
            )

            _save_singleton_image(
                slide,
                request.FILES,
                "frame2_image",
                cleanup_files,
            )

            _save_singleton_image(
                slide,
                request.FILES,
                "frame3_image",
                cleanup_files,
            )

    except ValidationError as e:
        _cleanup_files(cleanup_files)

        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        _cleanup_files(cleanup_files)

        logger.exception("Error saving Memories Offer Slide")

        return JsonResponse(
            {
                "error": (
                    "Something went wrong saving the "
                    "Memories Offer Slide."
                )
            },
            status=500,
        )

    return JsonResponse({"saved": True})


@require_http_methods(["POST"])
def save_memories_slide3(request):
    cleanup_files = []

    try:
        with transaction.atomic():
            slide = MemoriesSlide3.load()

            _save_singleton_image(
                slide,
                request.FILES,
                "desktop_image",
                cleanup_files,
            )

            _save_singleton_image(
                slide,
                request.FILES,
                "mobile_image",
                cleanup_files,
            )

    except ValidationError as e:
        _cleanup_files(cleanup_files)
        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        _cleanup_files(cleanup_files)
        logger.exception("Error saving Memories Slide 3")
        return JsonResponse(
            {"error": "Something went wrong saving Memories Slide 3."},
            status=500,
        )

    return JsonResponse({"saved": True})


# ---------------------------------------------------------------------
# SWEET MEMORIES GALLERY (dynamic list — "Add Photos" / drag to reorder)
# ---------------------------------------------------------------------
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["GET", "POST"])
def memory_images(request):
    if request.method == "GET":
        images = SweetMemoryImage.objects.order_by("display_order", "id")

        return JsonResponse({
            "images": [
                {
                    "id": image.id,
                    "url": image.image.url,
                    "display_order": image.display_order,
                }
                for image in images
            ]
        })

    uploaded = request.FILES.getlist("images")

    if not uploaded:
        return JsonResponse(
            {"error": "No images provided."},
            status=400,
        )

    if len(uploaded) > MAX_MEMORY_IMAGES:
        return JsonResponse(
            {
                "error": (
                    f"You can upload a maximum of "
                    f"{MAX_MEMORY_IMAGES} images at once."
                )
            },
            status=400,
        )

    cleanup_files = []
    created = []

    try:
        with transaction.atomic():

            # Lock existing gallery rows while calculating the next position.
            existing_images = list(
                SweetMemoryImage.objects
                .select_for_update()
                .order_by("display_order", "id")
            )

            current_count = len(existing_images)

            if current_count + len(uploaded) > MAX_MEMORY_IMAGES:
                return JsonResponse(
                    {
                        "error": (
                            f"Maximum {MAX_MEMORY_IMAGES} "
                            f"memory images allowed."
                        )
                    },
                    status=400,
                )

            # Don't use COUNT() as display_order.
            # Deleted images can leave gaps.
            if existing_images:
                next_order = max(
                    image.display_order
                    for image in existing_images
                ) + 1
            else:
                next_order = 0

            # Validate ALL files before saving any of them.
            for f in uploaded:
                _validate_image_file(f)

            # Everything passed validation.
            for f in uploaded:
                img = SweetMemoryImage(
                    image=f,
                    display_order=next_order,
                )

                img.full_clean()
                img.save()

                # Track the actual storage path so we can
                # delete it if the outer transaction fails.
                if img.image and img.image.name:
                    cleanup_files.append(img.image.name)

                created.append({
                    "id": img.id,
                    "url": img.image.url,
                    "display_order": img.display_order,
                })

                next_order += 1

    except ValidationError as e:
        _cleanup_files(cleanup_files)

        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        _cleanup_files(cleanup_files)

        logger.exception("Error uploading Sweet Memories gallery images")

        return JsonResponse(
            {
                "error": (
                    "Something went wrong while uploading "
                    "the gallery images."
                )
            },
            status=500,
        )

    return JsonResponse(
        {"created": created},
        status=201,
    )
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["DELETE"])
def memory_image_delete(request, pk):
    image = get_object_or_404(SweetMemoryImage, pk=pk)

    image_name = image.image.name if image.image else None

    try:
        with transaction.atomic():
            image.delete()

            if image_name:
                transaction.on_commit(
                    lambda name=image_name: default_storage.delete(name)
                )

    except Exception:
        logger.exception(
            "Error deleting Sweet Memories gallery image: %s",
            pk,
        )
        return JsonResponse(
            {
                "error": "Something went wrong deleting the gallery image."
            },
            status=500,
        )

    return JsonResponse({"deleted": True})
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented


@require_http_methods(["POST"])
def memory_images_reorder(request):
    """
    Body: {"order": [id1, id2, id3, ...]} — the new left-to-right order
    from the "Drag to reorder" UI.
    """
    try:
        payload = json.loads(request.body)
        ordered_ids = payload["order"]
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Invalid request."}, status=400)

    if not isinstance(ordered_ids, list) or not ordered_ids:
        return JsonResponse({"error": "Invalid request."}, status=400)

    case = Case(
        *[When(pk=image_id, then=position) for position, image_id in enumerate(ordered_ids)]
    )

    with transaction.atomic():
        updated = SweetMemoryImage.objects.filter(pk__in=ordered_ids).update(display_order=case)

    if updated != len(ordered_ids):
        return JsonResponse({"error": "Some images could not be found."}, status=400)

    return JsonResponse({"reordered": True})

 

# ==========================================
# WEBSITE BUILDER - HEADER AND NAV
# ==========================================

# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_header_settings(request):
    cleanup_files = []

    try:
        with transaction.atomic():
            header = HeaderSettings.load()

            _save_singleton_image(
                header,
                request.FILES,
                "logo",
                cleanup_files,
            )

    except ValidationError as e:
        _cleanup_files(cleanup_files)
        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        _cleanup_files(cleanup_files)
        logger.exception("Error saving Header Settings")
        return JsonResponse(
            {"error": "Something went wrong saving the Header Settings."},
            status=500,
        )

    return JsonResponse({"saved": True})
# OFFER BAR ITEMS (dynamic list — "Add Another Offer")

# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["GET", "POST"])
def offer_items(request):
    if request.method == "GET":
        items = OfferBarItem.objects.all().order_by("display_order")
        return JsonResponse({
            "items": [
                {
                    "id": i.id,
                    "text": i.text,
                    "display_order": i.display_order
                }
                for i in items
            ]
        })

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    text = (payload.get("text") or "").strip()
    item_id = payload.get("id")

    if not text:
        return JsonResponse({"error": "Offer text is required."}, status=400)

    if item_id is not None and not isinstance(item_id, int):
        return JsonResponse({"error": "Invalid item id."}, status=400)

    # UPDATE
    if item_id:
        try:
            item = OfferBarItem.objects.get(id=item_id)
        except OfferBarItem.DoesNotExist:
            return JsonResponse({"error": "Item not found."}, status=404)

        item.text = text
        update_fields = ["text"]

    # CREATE
    else:
        last_order = (
            OfferBarItem.objects.order_by("-display_order")
            .values_list("display_order", flat=True)
            .first()
            or 0
        )

        item = OfferBarItem(
            text=text,
            display_order=last_order + 1
        )
        update_fields = None

    try:
        with transaction.atomic():
            item.full_clean()
            item.save(update_fields=update_fields)
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)

    return JsonResponse({
        "id": item.id,
        "text": item.text
    })

# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["DELETE"])
def offer_item_delete(request, pk):
    item = get_object_or_404(OfferBarItem, pk=pk)
    item.delete()
    return JsonResponse({"deleted": True})
 
 
# ==========================================
# WEBSITE BUILDER - FOOTER
# ==========================================

# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_footer_settings(request):
    try:
        with transaction.atomic():
            footer = FooterSettings.load()

            _save_singleton_text_fields(
                footer,
                request.POST,
                [
                    "brand_name",
                    "brand_description",
                    "store_address",
                    "phone_number",
                    "email",
                    "instagram_link",
                    "whatsapp_number",
                ],
            )

    except ValidationError as e:
        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        logger.exception("Error saving footer settings")
        return JsonResponse(
            {
                "error": "Something went wrong saving footer settings."
            },
            status=500,
        )

    return JsonResponse({"saved": True})
 
# ==========================================
# WEBSITE BUILDER - ABOUT US SECTION
# ==========================================
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_about_section(request):
    cleanup_files = []

    try:
        with transaction.atomic():
            about = AboutUsSection.load()

            _save_singleton_text_fields(
                about,
                request.POST,
                [
                    "small_title",
                    "main_heading",
                    "highlight_quote",
                    "main_paragraph",
                    "ending_signoff",
                    "floating_top_text",
                    "floating_bottom_text",
                ],
            )

            _save_singleton_image(
                about,
                request.FILES,
                "about_image",
                cleanup_files,
            )

    except ValidationError as e:
        _cleanup_files(cleanup_files)
        return JsonResponse(
            {"error": " ".join(e.messages)},
            status=400,
        )

    except Exception:
        _cleanup_files(cleanup_files)
        logger.exception("Error saving About Us Section")
        return JsonResponse(
            {"error": "Something went wrong saving the About Us section."},
            status=500,
        )

    return JsonResponse({"saved": True})


# ---------------------------------------------------------------------
# ADMIN CUSTOMER REVIEWS & CUSTOMERS MANAGEMENT
# ---------------------------------------------------------------------

def reviews_management(request):
    status_filter = request.GET.get('status', 'all')
    if status_filter not in ('all', 'pending', 'approved'):
        status_filter = 'all'

    reviews = ProductReview.objects.select_related('user').order_by('-created_at')

    if status_filter == 'pending':
        reviews = reviews.filter(is_approved=False)
    elif status_filter == 'approved':
        reviews = reviews.filter(is_approved=True)

    paginator = Paginator(reviews, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        "reviews": page_obj,
        "status_filter": status_filter,
    }
    return render(request, "adm_user/reviews_management.html", context)


@require_http_methods(["POST"])
def approve_review(request, pk):
    review = get_object_or_404(ProductReview, pk=pk)
    review.is_approved = not review.is_approved
    review.save(update_fields=['is_approved'])
    return JsonResponse({"is_approved": review.is_approved})


@require_http_methods(["POST", "DELETE"])
def delete_review(request, pk):
    review = get_object_or_404(ProductReview, pk=pk)

    for f in (review.image_1, review.image_2, review.image_3):
        if f:
            f.delete(save=False)

    review.delete()
    return JsonResponse({"deleted": True})


# ---------------------------------------------------------------------
# SIGNATURE CATEGORIES MANAGEMENT (5 SIGNATURE SAREE CATEGORIES)
# ---------------------------------------------------------------------

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIG_IMAGE_SIZE_MB = 5

def validate_image_file(file):
    """
    Validate signature-category images using the same
    production image validation rules.
    """
    try:
        _validate_image(
            file,
            max_size=MAX_SIG_IMAGE_SIZE_MB * 1024 * 1024
        )
        return None

    except ValueError as e:
        return str(e)

def parse_display_order(raw_value):
    try:
        return int(raw_value or 0), None
    except (TypeError, ValueError):
        return None, "Invalid display order."

@require_http_methods(["GET", "POST"])
def signature_categories_api(request):
    if request.method == "GET":
        categories = SignatureCategoryItem.objects.all().order_by("display_order")
        data = [{
            "id": c.id,
            "name": c.name,
            "badge_text": c.badge_text,
            "origin_craft": c.origin_craft,
            "image_url": c.image.url if c.image else "",
            "display_order": c.display_order,
        } for c in categories]
        return JsonResponse({"categories": data})

    # POST — create
    name = request.POST.get("name", "").strip()
    badge_text = request.POST.get("badge_text", "").strip()
    origin_craft = request.POST.get("origin_craft", "").strip()

    if not name:
        return JsonResponse({"error": "Category name is required."}, status=400)

    display_order, error = parse_display_order(request.POST.get("display_order", 0))
    if error:
        return JsonResponse({"error": error}, status=400)

    if "image" in request.FILES:
        error = validate_image_file(request.FILES["image"])
        if error:
            return JsonResponse({"error": error}, status=400)

    item = SignatureCategoryItem(
        name=name,
        badge_text=badge_text,
        origin_craft=origin_craft,
        display_order=display_order,
    )
    if "image" in request.FILES:
        item.image = request.FILES["image"]

    try:
        item.full_clean()
        with transaction.atomic():
            item.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "A category with this name already exists."}, status=409)

    return JsonResponse({
        "id": item.id,
        "name": item.name,
        "badge_text": item.badge_text,
        "origin_craft": item.origin_craft,
        "image_url": item.image.url if item.image else "",
    }, status=201)


@require_http_methods(["POST"])
def signature_category_edit(request, pk):
    item = get_object_or_404(SignatureCategoryItem, pk=pk)

    if "name" in request.POST:
        name = request.POST.get("name", "").strip()
        if not name:
            return JsonResponse({"error": "Category name is required."}, status=400)
        item.name = name
    if "badge_text" in request.POST:
        item.badge_text = request.POST.get("badge_text", "").strip()
    if "origin_craft" in request.POST:
        item.origin_craft = request.POST.get("origin_craft", "").strip()
    if "display_order" in request.POST:
        display_order, error = parse_display_order(request.POST.get("display_order", 0))
        if error:
            return JsonResponse({"error": error}, status=400)
        item.display_order = display_order

    old_image = None
    if "image" in request.FILES:
        error = validate_image_file(request.FILES["image"])
        if error:
            return JsonResponse({"error": error}, status=400)
        old_image = item.image if item.image else None
        item.image = request.FILES["image"]
    try:
        item.full_clean()
        with transaction.atomic():
            item.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "Another category already has this name."}, status=409)

    if old_image:
        old_image.delete(save=False)
    
    return JsonResponse({
        "id": item.id,
        "name": item.name,
        "badge_text": item.badge_text,
        "origin_craft": item.origin_craft,
        "image_url": item.image.url if item.image else "",
    })


@require_http_methods(["POST", "DELETE"])
def signature_category_delete(request, pk):
    item = get_object_or_404(SignatureCategoryItem, pk=pk)
    image_to_delete = item.image if item.image else None

    try:
        with transaction.atomic():
            item.delete()
    except ProtectedError:
        return JsonResponse(
            {"error": "This category is linked to existing data and can't be deleted."},
            status=409,
        )

    if image_to_delete:
        image_to_delete.delete(save=False)

    return JsonResponse({"deleted": True})

 