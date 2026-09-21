# tests/test_signature_category_views.py
import pytest
from django.urls import reverse
from adm_user.models import SignatureCategoryItem  # fix import path
import io
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from PIL import Image

pytestmark = pytest.mark.django_db


def test_create_signature_category_valid_data(client):
    url = reverse("adm_user:signature_categories_api")

    response = client.post(url, {
        "name": "Banarasi Silk",
        "badge_text": "Heritage",
        "origin_craft": "Varanasi",
        "display_order": 1,
    })

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Banarasi Silk"
    assert data["badge_text"] == "Heritage"
    assert data["origin_craft"] == "Varanasi"

    item = SignatureCategoryItem.objects.get(name="Banarasi Silk")
    assert item.display_order == 1
    assert item.badge_text == "Heritage"

    # confirm it now shows up in the GET list too
    list_response = client.get(url)
    names = [c["name"] for c in list_response.json()["categories"]]
    assert "Banarasi Silk" in names


def test_create_signature_category_duplicate_name(client):
    url = reverse("adm_user:signature_categories_api")

    client.post(url, {"name": "Banarasi Silk", "display_order": 1})
    response = client.post(url, {"name": "banarasi silk", "display_order": 2})

    assert response.status_code == 400
    assert response.json()["error"] == "This category already exists."
    assert SignatureCategoryItem.objects.filter(name__iexact="Banarasi Silk").count() == 1

def test_create_signature_category_empty_name(client):
    url = reverse("adm_user:signature_categories_api")

    response = client.post(url, {"name": "", "display_order": 1})

    assert response.status_code == 400
    assert response.json()["error"] == "Category name is required."
    assert not SignatureCategoryItem.objects.filter(display_order=1).exists()

# def test_unauthenticated_access_to_create_category(client):
#     """
#     TC-04 — expected to FAIL until auth is enforced on this view.
#     Once @login_required / @staff_member_required is added to
#     signature_categories_api, this should pass.
#     """
#     url = reverse("adm_user:signature_categories_api")

#     response = client.post(url, {"name": "Should Not Be Allowed", "display_order": 1})

#     # currently no auth guard exists, so this will fail — that's expected
#     assert response.status_code in (302, 403)
#     assert not SignatureCategoryItem.objects.filter(name="Should Not Be Allowed").exists()

def test_edit_signature_category(client):
    category = SignatureCategoryItem.objects.create(
        name="Original Name",
        badge_text="Old Badge",
        display_order=1,
    )
    url = reverse("adm_user:signature_category_edit", args=[category.pk])

    response = client.post(url, {"name": "Updated Name", "badge_text": "New Badge"})

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["badge_text"] == "New Badge"

    category.refresh_from_db()
    assert category.name == "Updated Name"
    assert category.badge_text == "New Badge"
    assert category.display_order == 1  # untouched field should be unchanged

def test_delete_signature_category(client):
    category = SignatureCategoryItem.objects.create(
        name="To Be Deleted",
        display_order=1,
    )
    url = reverse("adm_user:signature_category_delete", args=[category.pk])

    response = client.post(url)

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not SignatureCategoryItem.objects.filter(pk=category.pk).exists()

def test_delete_signature_category_with_linked_product(client):
    from adm_user.models import Product, Fabric  # adjust import path if these live elsewhere

    category = SignatureCategoryItem.objects.create(
        name="Category With Products",
        display_order=1,
    )
    fabric = Fabric.objects.create(name="Cotton")
    Product.objects.create(
        name="Test Saree",
        category=category,
        fabric=fabric,
        base_price=1500,
    )

    url = reverse("adm_user:signature_category_delete", args=[category.pk])
    response = client.post(url)

    assert response.status_code == 409
    assert response.json()["error"] == "This category is linked to existing data and can't be deleted."

    # category and product should both still exist — delete must have been blocked
    assert SignatureCategoryItem.objects.filter(pk=category.pk).exists()
    assert Product.objects.filter(name="Test Saree").exists()

# ---- TC-11: list ordering ----
def test_signature_category_list_ordering(client):
    SignatureCategoryItem.objects.create(name="Third", display_order=3)
    SignatureCategoryItem.objects.create(name="First", display_order=1)
    SignatureCategoryItem.objects.create(name="Second", display_order=2)

    url = reverse("adm_user:signature_categories_api")
    response = client.get(url)

    names = [c["name"] for c in response.json()["categories"]]
    assert names == ["First", "Second", "Third"]


# ---- Edit: duplicate name ----
def test_edit_signature_category_duplicate_name(client):
    SignatureCategoryItem.objects.create(name="Existing Name", display_order=1)
    target = SignatureCategoryItem.objects.create(name="Rename Me", display_order=2)

    url = reverse("adm_user:signature_category_edit", args=[target.pk])
    response = client.post(url, {"name": "existing name"})  # different case, same constraint

    assert response.status_code == 400
    assert response.json()["error"] == "This category already exists."
    target.refresh_from_db()
    assert target.name == "Rename Me"  # unchanged


# ---- Edit: empty name ----
def test_edit_signature_category_empty_name(client):
    target = SignatureCategoryItem.objects.create(name="Keep Me", display_order=1)
    url = reverse("adm_user:signature_category_edit", args=[target.pk])

    response = client.post(url, {"name": ""})

    assert response.status_code == 400
    assert response.json()["error"] == "Category name is required."
    target.refresh_from_db()
    assert target.name == "Keep Me"


# ---- Invalid display_order on create ----
def test_create_signature_category_invalid_display_order(client):
    url = reverse("adm_user:signature_categories_api")
    response = client.post(url, {"name": "Bad Order", "display_order": "not-a-number"})

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid display order."
    assert not SignatureCategoryItem.objects.filter(name="Bad Order").exists()


# ---- Invalid display_order on edit ----
def test_edit_signature_category_invalid_display_order(client):
    target = SignatureCategoryItem.objects.create(name="Test", display_order=1)
    url = reverse("adm_user:signature_category_edit", args=[target.pk])

    response = client.post(url, {"display_order": "not-a-number"})

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid display order."
    target.refresh_from_db()
    assert target.display_order == 1  # unchanged

def make_test_image(name="test.png", format="PNG", size=(10, 10), content_type="image/png"):
    buf = io.BytesIO()
    Image.new("RGB", size, color=(255, 0, 0)).save(buf, format=format)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type=content_type)


def test_create_signature_category_with_valid_image(client):
    url = reverse("adm_user:signature_categories_api")
    image = make_test_image()

    response = client.post(url, {"name": "With Image", "image": image})

    assert response.status_code == 201
    assert response.json()["image_url"]
    item = SignatureCategoryItem.objects.get(name="With Image")
    assert item.image.name


def test_create_signature_category_wrong_image_content_type(client):
    url = reverse("adm_user:signature_categories_api")
    bad_file = SimpleUploadedFile("bad.txt", b"just some text", content_type="text/plain")

    response = client.post(url, {"name": "Bad Type", "image": bad_file})

    assert response.status_code == 400
    assert response.json()["error"] == "Only JPEG, PNG, or WEBP images are allowed."
    assert not SignatureCategoryItem.objects.filter(name="Bad Type").exists()


def test_create_signature_category_oversized_image(client):
    url = reverse("adm_user:signature_categories_api")
    oversized = SimpleUploadedFile("big.jpg", b"0" * (6 * 1024 * 1024), content_type="image/jpeg")

    response = client.post(url, {"name": "Too Big", "image": oversized})

    assert response.status_code == 400
    assert response.json()["error"] == "Image files must be under 5MB."
    assert not SignatureCategoryItem.objects.filter(name="Too Big").exists()


def test_create_signature_category_corrupted_image(client):
    url = reverse("adm_user:signature_categories_api")
    corrupted = SimpleUploadedFile("fake.png", b"this is not actually a png file", content_type="image/png")

    response = client.post(url, {"name": "Corrupted", "image": corrupted})

    assert response.status_code == 400
    assert response.json()["error"] == "The uploaded file is not a valid JPEG, PNG, or WEBP image."
    assert not SignatureCategoryItem.objects.filter(name="Corrupted").exists()


def test_edit_signature_category_replaces_image_and_deletes_old(client):
    create_response = client.post(
        reverse("adm_user:signature_categories_api"),
        {"name": "Swap Image", "image": make_test_image(name="first.png")},
    )
    item = SignatureCategoryItem.objects.get(pk=create_response.json()["id"])
    old_image_name = item.image.name
    assert default_storage.exists(old_image_name)

    response = client.post(
        reverse("adm_user:signature_category_edit", args=[item.pk]),
        {"image": make_test_image(name="second.png")},
    )

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.image.name != old_image_name
    assert not default_storage.exists(old_image_name)  # old file actually cleaned up

def test_edit_signature_category_leaves_image_untouched_when_not_sent(client):
    create_response = client.post(
        reverse("adm_user:signature_categories_api"),
        {"name": "Has Image", "image": make_test_image()},
    )
    item = SignatureCategoryItem.objects.get(pk=create_response.json()["id"])
    original_image_name = item.image.name
    assert original_image_name  # sanity check it was actually saved

    # Edit only the badge_text, no image in the payload
    response = client.post(
        reverse("adm_user:signature_category_edit", args=[item.pk]),
        {"badge_text": "Updated Badge"},
    )

    assert response.status_code == 200
    item.refresh_from_db()
    assert item.image.name == original_image_name  # untouched
    assert default_storage.exists(original_image_name)  # not deleted either
    assert item.badge_text == "Updated Badge"

def test_create_signature_category_image_exceeds_max_width(client, monkeypatch):
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_WIDTH", 50)

    url = reverse("adm_user:signature_categories_api")
    image = make_test_image(size=(100, 20))  # wider than patched limit

    response = client.post(url, {"name": "Too Wide", "image": image})

    assert response.status_code == 400
    assert response.json()["error"] == "Image width cannot exceed 50px."
    assert not SignatureCategoryItem.objects.filter(name="Too Wide").exists()


def test_create_signature_category_image_exceeds_max_height(client, monkeypatch):
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_HEIGHT", 50)

    url = reverse("adm_user:signature_categories_api")
    image = make_test_image(size=(20, 100))  # taller than patched limit

    response = client.post(url, {"name": "Too Tall", "image": image})

    assert response.status_code == 400
    assert response.json()["error"] == "Image height cannot exceed 50px."
    assert not SignatureCategoryItem.objects.filter(name="Too Tall").exists()


def test_create_signature_category_image_exceeds_max_pixels(client, monkeypatch):
    # keep width/height under their own limits individually, but total pixels over
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_WIDTH", 200)
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_HEIGHT", 200)
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_PIXELS", 1000)

    url = reverse("adm_user:signature_categories_api")
    image = make_test_image(size=(100, 100))  # 10,000 px > patched 1,000 limit, but 100<200 on each side

    response = client.post(url, {"name": "Too Many Pixels", "image": image})

    assert response.status_code == 400
    assert response.json()["error"] == "Image resolution is too large. Please upload a smaller image."
    assert not SignatureCategoryItem.objects.filter(name="Too Many Pixels").exists()

