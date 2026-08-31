
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
from django.db.models import ProtectedError, Q, Case, When

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods

from .models import Category, Color, Fabric, Print, Tag, Product, ProductVariant, ProductImage, HeroSlideMain, HeroSlideImageOnly, HeroSlideOffer, SweetMemoriesSection, SweetMemoryImage, MemoriesOfferSlide, MemoriesSlide3, OfferBarItem, HeaderSettings, FooterSettings, AboutUsSection,SignatureCategoryItem
from decimal import Decimal, InvalidOperation

from PIL import Image
from user.models import ProductReview
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


FORM_TEMPLATE = "adm_user/products.html"

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# WEBSITE BUILDER
MAX_IMAGE_SIZE_MB = 25  # Relaxed size limit to support high-res banners
MAX_MEMORY_IMAGES = 20  # sane production cap so the slider can't grow unbounded

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
        relative_path = relative_path[len(settings.MEDIA_URL):]  # -> "products/abc123_photo.jpeg"
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
    qs = Product.objects.filter(is_active=True).select_related("category").order_by("-created_at")

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


def _save_uploaded_image(request, file_obj):
    if file_obj.content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Only JPEG, PNG, or WEBP images are allowed.")
    if file_obj.size > MAX_IMAGE_SIZE:
        raise ValueError("Image files must be under 5MB.")

    safe_name = get_valid_filename(file_obj.name)
    path = default_storage.save(f"products/{uuid.uuid4().hex}_{safe_name}", file_obj)
    return request.build_absolute_uri(default_storage.url(path))

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
    product.category = get_object_or_404(SignatureCategoryItem, pk=category_id, is_active=True)

    fabric_id = post.get("fabric")
    if not fabric_id:
        raise ValueError("Fabric is required.")
    product.fabric = get_object_or_404(Fabric, pk=fabric_id, is_active=True)

    print_id = post.get("print_type")
    product.print_type = get_object_or_404(Print, pk=print_id, is_active=True) if print_id else None

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
    stocks = request.POST.getlist("variant_stock")
    prices = request.POST.getlist("variant_price")

    kept_variant_ids = []

    for color_id, stock, price in zip(color_ids, stocks, prices):
        if not color_id:
            continue
        color = get_object_or_404(Color, pk=color_id, is_active=True)

        try:
            variant_price = Decimal(price) if price else None
        except InvalidOperation:
            raise ValueError(f"Invalid price for variant color {color.name}.")

        variant, _ = ProductVariant.objects.get_or_create(product=product, color=color)
        variant.stock_quantity = stock or 0
        variant.price = variant_price
        variant.is_active = True
        variant.full_clean()
        variant.save()

        kept_variant_ids.append(variant.id)

        for image_file in request.FILES.getlist(f"variant_images_{color_id}"):
            url = _save_uploaded_image(request, image_file)
            ProductImage.objects.create(
                product=product,
                variant=variant,
                image_url=url,
                display_order=variant.images.count(),
            )

    product.variants.exclude(id__in=kept_variant_ids).update(is_active=False)

    for image_file in request.FILES.getlist("default_images"):
        url = _save_uploaded_image(request, image_file)
        ProductImage.objects.create(
            product=product,
            variant=None,
            image_url=url,
            display_order=product.images.filter(variant__isnull=True).count(),
        )

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
            return _handle_save_errors(request, exc)

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
        new_stock = int(payload.get("stock_quantity"))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Enter a valid stock quantity."}, status=400)

    if new_stock < 0:
        return JsonResponse({"ok": False, "error": "Stock can't be negative."}, status=400)

    product.stock_quantity = new_stock
    try:
        product.full_clean(validate_unique=False)
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
    Validates uploaded image size and verifies format using Pillow with clear user-facing error messages.
    """
    file_size_mb = round(f.size / (1024 * 1024), 2)
    filename = getattr(f, 'name', 'Uploaded image')

    if f.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            f"Image '{filename}' is too large ({file_size_mb}MB). Maximum allowed image size is {MAX_IMAGE_SIZE_MB}MB. Please compress or choose a smaller image."
        )
    
    try:
        
        img = Image.open(f)
        img.verify()
        f.seek(0)
    except Exception:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        allowed = set(get_available_image_extensions()) | {"jpg", "jpeg", "png", "webp", "gif", "bmp", "jfif", "avif", "svg", "blob", ""}
        if ext not in allowed:
            raise ValidationError(
                f"File '{filename}' is not a recognized image format. Please upload a JPG, PNG, or WEBP image."
            )
 
 
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


def _save_singleton_image(instance, files, field_name):
    f = files.get(field_name)
    if not f:
        return
    _validate_image_file(f)

    old_file = getattr(instance, field_name)

    setattr(instance, field_name, f)
    instance.full_clean(exclude=[fld.name for fld in instance._meta.fields if isinstance(fld, models.ImageField)])
    instance.save(update_fields=[field_name])

    if old_file and old_file.name != getattr(instance, field_name).name:
        old_file.delete(save=False)

# ==========================================
# WEBSITE BUILDER - HERO BANNER
# ==========================================

# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented

@require_http_methods(["POST"])
def save_hero_main(request):
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
            _save_singleton_image(hero, request.FILES, "desktop_image")
            _save_singleton_image(hero, request.FILES, "mobile_image")
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except Exception:
        logger.exception("Error saving Main Hero Slide")
        return JsonResponse({"error": "Something went wrong saving the Main Hero Slide."}, status=500)
    return JsonResponse({"saved": True})
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_hero_image_only(request):
    try:
        with transaction.atomic():
            hero = HeroSlideImageOnly.load()
            _save_singleton_image(hero, request.FILES, "desktop_image")
            _save_singleton_image(hero, request.FILES, "mobile_image")
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except Exception as e:
        logger.exception("Error saving Main Hero Slide 2")
        return JsonResponse({"error": f"Error saving Image Only Slide: {str(e)}"}, status=500)
        
    return JsonResponse({"saved": True})
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_hero_offer(request):
    try:
        with transaction.atomic():
            hero = HeroSlideOffer.load()
            _save_singleton_image(hero, request.FILES, "desktop_image")
            _save_singleton_image(hero, request.FILES, "mobile_image")
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except Exception as e:
        logger.exception("Error saving Main Hero Slide 3")
        return JsonResponse({"error": f"Error saving Hero Offer Banner: {str(e)}"}, status=500)
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
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    return JsonResponse({"saved": True})
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_memories_offer_slide(request):
    try:
        with transaction.atomic():
            slide = MemoriesOfferSlide.load()
            _save_singleton_text_fields(
                slide,
                request.POST,
                [
                    "frame1_title", "frame1_badge", "frame1_ribbon", "frame1_wa_link",
                    "frame2_title", "frame2_badge", "frame2_ribbon", "frame2_wa_link",
                    "frame3_title", "frame3_badge", "frame3_ribbon", "frame3_wa_link",
                ]
            )
            _save_singleton_image(slide, request.FILES, "desktop_image")
            _save_singleton_image(slide, request.FILES, "mobile_image")
            _save_singleton_image(slide, request.FILES, "frame1_image")
            _save_singleton_image(slide, request.FILES, "frame2_image")
            _save_singleton_image(slide, request.FILES, "frame3_image")
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    return JsonResponse({"saved": True})


@require_http_methods(["POST"])
def save_memories_slide3(request):
    try:
        with transaction.atomic():
            slide = MemoriesSlide3.load()
            _save_singleton_image(slide, request.FILES, "desktop_image")
            _save_singleton_image(slide, request.FILES, "mobile_image")
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    return JsonResponse({"saved": True})


# ---------------------------------------------------------------------
# SWEET MEMORIES GALLERY (dynamic list — "Add Photos" / drag to reorder)
# ---------------------------------------------------------------------
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["GET", "POST"])
def memory_images(request):
    if request.method == "GET":
        images = SweetMemoryImage.objects.order_by("display_order")
        return JsonResponse(
            {"images": [{"id": i.id, "url": i.image.url, "display_order": i.display_order} for i in images]}
        )

    uploaded = request.FILES.getlist("images")
    if not uploaded:
        return JsonResponse({"error": "No images provided."}, status=400)

    created = []
    try:
        with transaction.atomic():
            # lock existing rows so a concurrent upload can't read a stale count
            current_count = SweetMemoryImage.objects.select_for_update().count()

            if current_count + len(uploaded) > MAX_MEMORY_IMAGES:
                return JsonResponse(
                    {"error": f"Maximum {MAX_MEMORY_IMAGES} memory images allowed."}, status=400
                )

            next_order = current_count
            for f in uploaded:
                _validate_image_file(f)
                img = SweetMemoryImage(image=f, display_order=next_order)
                img.full_clean()
                img.save()
                created.append({"id": img.id, "url": img.image.url})
                next_order += 1
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)

    return JsonResponse({"created": created}, status=201)
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["DELETE"])
def memory_image_delete(request, pk):
    image = get_object_or_404(SweetMemoryImage, pk=pk)
    image.image.delete(save=False) 
    image.delete()
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
    try:
        with transaction.atomic():
            header = HeaderSettings.load()
            _save_singleton_image(header, request.FILES, "logo")
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
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
                    "brand_name", "brand_description", "store_address",
                    "phone_number", "email", "instagram_link", "whatsapp_number",
                ],
            )
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    return JsonResponse({"saved": True})
 
# ==========================================
# WEBSITE BUILDER - ABOUT US SECTION
# ==========================================
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_about_section(request):
    try:
        with transaction.atomic():
            about = AboutUsSection.load()
            _save_singleton_text_fields(
                about,
                request.POST,
                [
                    "small_title", "main_heading", "highlight_quote",
                    "main_paragraph", "ending_signoff",
                    "floating_top_text", "floating_bottom_text",
                ],
            )
            _save_singleton_image(about, request.FILES, "about_image")
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    return JsonResponse({"saved": True})



# ---------------------------------------------------------------------
# ADMIN CUSTOMER REVIEWS & CUSTOMERS MANAGEMENT
# ---------------------------------------------------------------------

def reviews_management(request):
    status_filter = request.GET.get('status', 'all')
    reviews = ProductReview.objects.select_related('user')

    if status_filter == 'pending':
        reviews = reviews.filter(is_approved=False)
    elif status_filter == 'approved':
        reviews = reviews.filter(is_approved=True)

    paginator = Paginator(reviews, 2)
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
    review.delete()
    return JsonResponse({"deleted": True})


# ---------------------------------------------------------------------
# SIGNATURE CATEGORIES MANAGEMENT (5 SIGNATURE SAREE CATEGORIES)
# ---------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def signature_categories_api(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        badge_text = request.POST.get("badge_text", "").strip()
        origin_craft = request.POST.get("origin_craft", "").strip()
        display_order = request.POST.get("display_order", 0)

        if not name:
            return JsonResponse({"error": "Category name is required."}, status=400)

        item = SignatureCategoryItem.objects.create(
            name=name,
            badge_text=badge_text,
            origin_craft=origin_craft,
            display_order=int(display_order or 0),
        )

        if "image" in request.FILES:
            item.image = request.FILES["image"]
            item.save()

        return JsonResponse({
            "id": item.id,
            "name": item.name,
            "badge_text": item.badge_text,
            "origin_craft": item.origin_craft,
            
            "image_url": item.image.url if item.image else "",
        })

    categories = SignatureCategoryItem.objects.all()
    data = [{
        "id": c.id,
        "name": c.name,
        "badge_text": c.badge_text,
        "origin_craft": c.origin_craft,
        "image_url": c.image.url if c.image else "",
        "display_order": c.display_order,
    } for c in categories]
    return JsonResponse({"categories": data})


@require_http_methods(["POST"])
def signature_category_edit(request, pk):
    item = get_object_or_404(SignatureCategoryItem, pk=pk)

    if "name" in request.POST:
        item.name = request.POST.get("name", "").strip()
    if "badge_text" in request.POST:
        item.badge_text = request.POST.get("badge_text", "").strip()
    if "origin_craft" in request.POST:
        item.origin_craft = request.POST.get("origin_craft", "").strip()
    if "display_order" in request.POST:
        item.display_order = int(request.POST.get("display_order", 0) or 0)
    if "image" in request.FILES:
        item.image = request.FILES["image"]

    item.save()
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
    item.delete()
    return JsonResponse({"deleted": True})

 