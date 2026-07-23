from django.shortcuts import render
import json

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import ProtectedError
from .models import Category, Color, Fabric, Print, Tag

# Create your views here.
def index(request):
    return render(request, 'adm_user/index.html')

def dashboard(request):
    return render(request, 'adm_user/dashboard.html')

def products(request):
    return render(request, 'adm_user/products.html')


# Views For CATEGORY
def categories(request):
    return render(request, 'adm_user/categories.html')


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

def img_manager(request):
    return render(request, 'adm_user/image_manager.html')

def coming_soon(request):
    return render(request, 'adm_user/coming-soon.html')