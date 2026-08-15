
import json
import uuid
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import get_valid_filename
from django.views.decorators.http import require_http_methods
from django.core.validators import get_available_image_extensions

from .models import Category, Color, Fabric, Print, Tag, Product, ProductVariant, ProductImage, HeroSlideMain, HeroSlideImageOnly, HeroSlideOffer, SweetMemoriesSection, SweetMemoryImage, MemoriesOfferSlide, MemoriesSlide3, OfferBarItem, HeaderSettings, FooterSettings, AboutUsSection

# Create your views here.
def index(request):
    return render(request, 'adm_user/index.html')

def dashboard(request):
    return render(request, 'adm_user/dashboard.html')


# Views For CATEGORY
def categories(request):
    from .models import SignatureCategoryItem
    context = {
        "signature_categories": SignatureCategoryItem.objects.all(),
    }
    return render(request, 'adm_user/categories.html', context)


@require_http_methods(["GET", "POST"])
def category_list_create(request):
    if request.method == "GET":
        categories = Category.objects.filter(is_active=True).order_by("created_at")
        data = [{"id": c.id, "name": c.name, "slug": c.slug} for c in categories]
        return JsonResponse({"categories": data})

    # POST — create a new category
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Category name is required."}, status=400)

    category = Category(name=name)
    try:
        category.full_clean()
        with transaction.atomic():
            category.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "This category already exists."}, status=409)

    return JsonResponse(
        {"id": category.id, "name": category.name, "slug": category.slug}, status=201
    )

@require_http_methods(["PUT"])
def category_update(request, pk):
    try:
        category = Category.objects.get(pk=pk, is_active=True)
    except Category.DoesNotExist:
        return JsonResponse({"error": "Category not found."}, status=404)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid request."}, status=400)

    name = (payload.get("name") or "").strip()
    if not name:
        return JsonResponse({"error": "Category name is required."}, status=400)

    if name != category.name:
        category.name = name
        category.slug = ""  # forces the mixin to regenerate it on save()

    try:
        category.full_clean()
        with transaction.atomic():
            category.save()
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    except IntegrityError:
        return JsonResponse({"error": "Another category already has this name."}, status=409)

    return JsonResponse({"id": category.id, "name": category.name, "slug": category.slug})

@require_http_methods(["DELETE"])
def category_delete(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return JsonResponse({"error": "Category not found."}, status=404)

    try:
        category.delete()
    except IntegrityError:
        return JsonResponse(
            {"error": "This category is linked to existing products and can't be deleted."},
            status=409,
        )
    return JsonResponse({"deleted": True})


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
        colors = Color.objects.filter(is_active=True).order_by("created_at")
        data = [{"id": c.id, "name": c.name, "hex_code": c.hex_code, "slug": c.slug} for c in colors]
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
    color.hex_code = hex_code

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
        color = Color.objects.get(pk=pk)
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
        fabrics = Fabric.objects.filter(is_active=True).order_by("created_at")
        data = [{"id": f.id, "name": f.name, "slug": f.slug} for f in fabrics]
        return JsonResponse({"fabrics": data})

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
        fabric = Fabric.objects.get(pk=pk)
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
        prints = Print.objects.filter(is_active=True).order_by("created_at")
        data = [{"id": p.id, "name": p.name, "slug": p.slug} for p in prints]
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
        print_obj = Print.objects.get(pk=pk)
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
        tags = Tag.objects.all().order_by("created_at")
        data = [{"id": t.id, "name": t.name, "slug": t.slug} for t in tags]
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

    tag.delete()
    return JsonResponse({"deleted": True})

# ==========================================
# PRODUCTS
# ==========================================

@require_http_methods(["GET"])
def products(request):
    context = {"products": Product.objects.filter(is_active=True).select_related("category")}
    context.update(_product_form_context())   # adds categories, fabrics, prints, colors, tags
    return render(request, FORM_TEMPLATE, context)


FORM_TEMPLATE = "adm_user/products.html"

def _save_uploaded_image(request, file_obj):
    safe_name = get_valid_filename(file_obj.name)
    path = default_storage.save(f"products/{uuid.uuid4().hex}_{safe_name}", file_obj)
    return request.build_absolute_uri(default_storage.url(path))

def _product_form_context(product=None):
    context = {
        "categories": Category.objects.filter(is_active=True),
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
    product.category = get_object_or_404(Category, pk=category_id, is_active=True)

    fabric_id = post.get("fabric")
    if not fabric_id:
        raise ValueError("Fabric is required.")
    product.fabric = get_object_or_404(Fabric, pk=fabric_id, is_active=True)

    print_id = post.get("print_type")
    product.print_type = get_object_or_404(Print, pk=print_id, is_active=True) if print_id else None

    try:
        product.base_price = post.get("base_price") or 0
        product.discount_price = post.get("discount_price") or None
        product.stock_quantity = post.get("stock_quantity") or 0
    except (TypeError, ValueError):
        raise ValueError("Price and stock fields must be numbers.")

    if product.discount_price is not None and product.discount_price >= product.base_price:
        raise ValueError("Discount price must be less than the base price.")

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

        variant, _created = ProductVariant.objects.update_or_create(
            product=product,
            color=color,
            defaults={
                "stock_quantity": stock or 0,
                "price": price or None,
                "is_active": True,
            },
        )
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

    try:
        with transaction.atomic():
            product.delete()
    except ProtectedError:
        error = "This product can't be deleted because it's linked to existing orders."
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": error}, status=409)
        messages.error(request, error)
        return redirect("adm_user:products")

    messages.success(request, f'"{product_name}" was permanently deleted.')

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "id": product_id})
    return redirect("adm_user:products")

def img_manager(request):
    return render(request, 'adm_user/image_manager.html')

# def website_builder(request):
#     return render(request, 'adm_user/website_builder.html')

def coming_soon(request):
    return render(request, 'adm_user/coming-soon.html')

def login(request):
    return render(request, 'adm_user/login.html')

def signup(request):
    return render(request, 'adm_user/signup.html')


# ==========================================
# WEBSITE BUILDER
# ==========================================
 
MAX_IMAGE_SIZE_MB = 9  # matches the "Max 2MB per image" guideline in your UI
MAX_MEMORY_IMAGES = 20  # sane production cap so the slider can't grow unbounded
 
 
def _validate_image_file(f):
    """
    ImageField validates that the file IS an image, but does nothing
    about size — enforce that here so a 40MB phone photo doesn't hit
    your media storage (and R2 bill) unchecked.
    """
    if f.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(f"Image must be under {MAX_IMAGE_SIZE_MB}MB.")
    ext = f.name.rsplit(".", 1)[-1].lower()
    if ext not in get_available_image_extensions():
        raise ValidationError("Unsupported image file type.")
 
 
# ---------------------------------------------------------------------
# PAGE LOAD
# ---------------------------------------------------------------------
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
def website_builder(request):
    from .models import SignatureCategoryItem
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
    """
    Only overwrite fields present in `data` — a partial update. Keeps
    image fields untouched here entirely; images are handled by the
    dedicated _save_singleton_image() below so a text-only save can
    never accidentally wipe out an existing photo.
    """
    for field in fields:
        if field in data:
            setattr(instance, field, data[field])
    instance.full_clean(exclude=[f.name for f in instance._meta.fields if f.name.endswith("image") or f.name in ("desktop_image", "mobile_image", "logo", "about_image")])
    instance.save()
 
 
def _save_singleton_image(instance, files, field_name):
    """
    Only replaces the image if a new file was actually uploaded —
    re-submitting the form without picking a new file must NOT clear
    the existing image (ImageField's blank/empty submission behavior
    would otherwise do exactly that).
    """
    f = files.get(field_name)
    if not f:
        return
    _validate_image_file(f)
    setattr(instance, field_name, f)
    instance.save()
 
 
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
    return JsonResponse({"saved": True})
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_hero_offer(request):
    try:
        with transaction.atomic():
            hero = HeroSlideOffer.load()
            _save_singleton_text_fields(
                hero,
                request.POST,
                ["small_top_text", "big_highlight_text", "subtext", "button_text"],
            )
            _save_singleton_image(hero, request.FILES, "desktop_image")
            _save_singleton_image(hero, request.FILES, "mobile_image")
    except ValidationError as e:
        return JsonResponse({"error": " ".join(e.messages)}, status=400)
    return JsonResponse({"saved": True})
 
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["POST"])
def save_memories_section(request):
    theme = request.POST.get("background_theme")
    valid_themes = dict(SweetMemoriesSection.THEME_CHOICES)
    if theme and theme not in valid_themes:
        return JsonResponse({"error": "Invalid theme selection."}, status=400)
 
    try:
        with transaction.atomic():
            section = SweetMemoriesSection.load()
            _save_singleton_text_fields(
                section,
                request.POST,
                ["section_label", "main_heading", "background_theme", "paragraph_text"],
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
# OFFER BAR ITEMS (dynamic list — "Add Another Offer")
# ---------------------------------------------------------------------
 
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

    # UPDATE
    if item_id:
        try:
            item = OfferBarItem.objects.get(id=item_id)
        except OfferBarItem.DoesNotExist:
            return JsonResponse({"error": "Item not found."}, status=404)

        item.text = text

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

    try:
        item.full_clean()
        with transaction.atomic():
            item.save()
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
 
 
# ---------------------------------------------------------------------
# SWEET MEMORIES GALLERY (dynamic list — "Add Photos" / drag to reorder)
# ---------------------------------------------------------------------
 
# TODO: add @login_required(login_url="adm_user:login") once login/signup is implemented
@require_http_methods(["GET", "POST"])
def memory_images(request):
    if request.method == "GET":
        images = SweetMemoryImage.objects.all()
        return JsonResponse(
            {"images": [{"id": i.id, "url": i.image.url, "display_order": i.display_order} for i in images]}
        )
 
    current_count = SweetMemoryImage.objects.count()
    uploaded = request.FILES.getlist("images")
    if not uploaded:
        return JsonResponse({"error": "No images provided."}, status=400)
    if current_count + len(uploaded) > MAX_MEMORY_IMAGES:
        return JsonResponse(
            {"error": f"Maximum {MAX_MEMORY_IMAGES} memory images allowed."}, status=400
        )
 
    created = []
    try:
        with transaction.atomic():
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
 
    with transaction.atomic():
        for position, image_id in enumerate(ordered_ids):
            SweetMemoryImage.objects.filter(pk=image_id).update(display_order=position)

    return JsonResponse({"reordered": True})


# ---------------------------------------------------------------------
# ADMIN CUSTOMER REVIEWS & CUSTOMERS MANAGEMENT
# ---------------------------------------------------------------------

def reviews_management(request):
    from user.models import ProductReview
    status_filter = request.GET.get('status', 'all')
    reviews = ProductReview.objects.all()

    if status_filter == 'pending':
        reviews = reviews.filter(is_approved=False)
    elif status_filter == 'approved':
        reviews = reviews.filter(is_approved=True)

    context = {
        "reviews": reviews,
        "status_filter": status_filter,
    }
    return render(request, "adm_user/reviews_management.html", context)


@require_http_methods(["POST"])
def approve_review(request, pk):
    from user.models import ProductReview
    review = get_object_or_404(ProductReview, pk=pk)
    review.is_approved = not review.is_approved
    review.save()
    return JsonResponse({"is_approved": review.is_approved})


@require_http_methods(["POST", "DELETE"])
def delete_review(request, pk):
    from user.models import ProductReview
    review = get_object_or_404(ProductReview, pk=pk)
    review.delete()
    return JsonResponse({"deleted": True})


# ---------------------------------------------------------------------
# SIGNATURE CATEGORIES MANAGEMENT (5 SIGNATURE SAREE CATEGORIES)
# ---------------------------------------------------------------------

@require_http_methods(["GET", "POST"])
def signature_categories_api(request):
    from .models import SignatureCategoryItem
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        badge_text = request.POST.get("badge_text", "").strip()
        origin_craft = request.POST.get("origin_craft", "").strip()
        whatsapp_link = request.POST.get("whatsapp_link", "").strip()
        display_order = request.POST.get("display_order", 0)

        if not name:
            return JsonResponse({"error": "Category name is required."}, status=400)

        item = SignatureCategoryItem.objects.create(
            name=name,
            badge_text=badge_text,
            origin_craft=origin_craft,
            whatsapp_link=whatsapp_link,
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
            "whatsapp_link": item.whatsapp_link,
            "image_url": item.image.url if item.image else "",
        })

    categories = SignatureCategoryItem.objects.all()
    data = [{
        "id": c.id,
        "name": c.name,
        "badge_text": c.badge_text,
        "origin_craft": c.origin_craft,
        "whatsapp_link": c.whatsapp_link,
        "image_url": c.image.url if c.image else "",
        "display_order": c.display_order,
    } for c in categories]
    return JsonResponse({"categories": data})


@require_http_methods(["POST"])
def signature_category_edit(request, pk):
    from .models import SignatureCategoryItem
    item = get_object_or_404(SignatureCategoryItem, pk=pk)

    if "name" in request.POST:
        item.name = request.POST.get("name", "").strip()
    if "badge_text" in request.POST:
        item.badge_text = request.POST.get("badge_text", "").strip()
    if "origin_craft" in request.POST:
        item.origin_craft = request.POST.get("origin_craft", "").strip()
    if "whatsapp_link" in request.POST:
        item.whatsapp_link = request.POST.get("whatsapp_link", "").strip()
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
        "whatsapp_link": item.whatsapp_link,
        "image_url": item.image.url if item.image else "",
    })


@require_http_methods(["POST", "DELETE"])
def signature_category_delete(request, pk):
    from .models import SignatureCategoryItem
    item = get_object_or_404(SignatureCategoryItem, pk=pk)
    item.delete()
    return JsonResponse({"deleted": True})

 