from django.shortcuts import render
import json

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Category

# Create your views here.
def index(request):
    return render(request, 'adm_user/index.html')

def dashboard(request):
    return render(request, 'adm_user/dashboard.html')

def products(request):
    return render(request, 'adm_user/products.html')

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


def filters(request):
    return render(request, 'adm_user/filters.html')

def img_manager(request):
    return render(request, 'adm_user/image_manager.html')

def website_builder(request):
    return render(request, 'adm_user/website_builder.html')

def coming_soon(request):
    return render(request, 'adm_user/coming-soon.html')