# adm_user/tests/test_product_views.py
import pytest
from decimal import Decimal
from django.urls import reverse
from adm_user.models import Product, SignatureCategoryItem, Fabric
import json
pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return SignatureCategoryItem.objects.create(name="Test Category", display_order=1)


@pytest.fixture
def fabric():
    return Fabric.objects.create(name="Silk")

@pytest.fixture
def client(client):
    """
    Override the default `client` fixture so every request uses SERVER_NAME='localhost'.
    Needed because Django's test client defaults to SERVER_NAME='testserver', which
    build_absolute_uri() turns into a URL Django's own URLValidator rejects
    ('testserver' has no TLD and isn't 'localhost') — breaking any test that
    uploads an image and stores an absolute URL.
    """
    client.defaults["SERVER_NAME"] = "localhost"
    return client


def test_product_create_get_renders_form(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.get(url)

    assert response.status_code == 200
    assert category in response.context["categories"]
    assert fabric in response.context["fabrics"]


def test_product_create_valid_minimal(client, category, fabric):
    url = reverse("adm_user:create")

    response = client.post(url, {
        "name": "Banarasi Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2500",
    })

    assert response.status_code == 302
    assert response.url == reverse("adm_user:products")

    product = Product.objects.get(name="Banarasi Saree")
    assert product.category == category
    assert product.fabric == fabric
    assert product.base_price == Decimal("2500")
    assert product.slug
    assert product.stock_quantity == 0  # default when not sent
    assert product.blouse_included is True  # _parse_bool default "Yes"

def test_product_create_missing_name(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "1000",
    })

    assert response.status_code == 200  # re-renders form, no redirect
    assert not Product.objects.filter(category=category).exists()


def test_product_create_missing_category(client, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "No Category Saree",
        "fabric": fabric.pk,
        "base_price": "1000",
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="No Category Saree").exists()


def test_product_create_missing_fabric(client, category):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "No Fabric Saree",
        "category": category.pk,
        "base_price": "1000",
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="No Fabric Saree").exists()


def test_product_create_invalid_category_id(client, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Bad Category Saree",
        "category": 99999,
        "fabric": fabric.pk,
        "base_price": "1000",
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Bad Category Saree").exists()


def test_product_create_inactive_category_rejected(client, fabric):
    inactive_category = SignatureCategoryItem.objects.create(
        name="Inactive Cat", display_order=1, is_active=False
    )
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Inactive Cat Saree",
        "category": inactive_category.pk,
        "fabric": fabric.pk,
        "base_price": "1000",
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Inactive Cat Saree").exists()


def test_product_create_invalid_price(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Bad Price Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "not-a-number",
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Bad Price Saree").exists()


def test_product_create_discount_not_less_than_base(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Bad Discount Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "1000",
        "discount_price": "1000",  # equal, not less — should be rejected
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Bad Discount Saree").exists()


def test_product_create_valid_discount(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Good Discount Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "1000",
        "discount_price": "800",
    })

    assert response.status_code == 302
    product = Product.objects.get(name="Good Discount Saree")
    assert product.discount_price == Decimal("800")
    assert product.final_price == 800

import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from adm_user.models import Color, ProductVariant, ProductImage


def make_test_image(name="test.png", size=(20, 20), content_type="image/png"):
    buf = io.BytesIO()
    Image.new("RGB", size, color=(0, 128, 0)).save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type=content_type)


@pytest.fixture
def color():
    return Color.objects.create(name="Ruby Red", hex_code="#9B111E")


def test_product_create_with_variant_and_image(client, category, fabric, color):
    url = reverse("adm_user:create")

    response = client.post(
        url,
        {
            "name": "Variant Saree",
            "category": category.pk,
            "fabric": fabric.pk,
            "base_price": "3000",
            "variant_color_id": [str(color.pk)],
            "variant_price": ["2800"],
            f"variant_images_{color.pk}": [make_test_image(name="variant.png")],
        },
        
    )

    assert response.status_code == 302
    product = Product.objects.get(name="Variant Saree")

    variant = ProductVariant.objects.get(product=product, color=color)
    assert variant.price == Decimal("2800")
    assert variant.is_active is True

    images = ProductImage.objects.filter(variant=variant)
    assert images.count() == 1
    assert images.first().image_url

def test_product_create_with_default_image_no_color(client, category, fabric):
    url = reverse("adm_user:create")

    response = client.post(
        url,
        {
            "name": "Default Image Saree",
            "category": category.pk,
            "fabric": fabric.pk,
            "base_price": "1500",
            "default_images": [make_test_image(name="default.png")],
        },
      
    )

    assert response.status_code == 302
    product = Product.objects.get(name="Default Image Saree")

    default_images = ProductImage.objects.filter(product=product, variant__isnull=True)
    assert default_images.count() == 1
    
def test_product_create_with_multiple_variants(client, category, fabric):
    from adm_user.models import Color
    color_a = Color.objects.create(name="Ruby Red", hex_code="#9B111E")
    color_b = Color.objects.create(name="Royal Blue", hex_code="#4169E1")

    url = reverse("adm_user:create")

    response = client.post(url, {
        "name": "Multi Variant Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "3500",
        "variant_color_id": [str(color_a.pk), str(color_b.pk)],
        "variant_price": ["3200", "3400"],
        f"variant_images_{color_a.pk}": [make_test_image(name="red.png")],
        f"variant_images_{color_b.pk}": [make_test_image(name="blue.png")],
    })

    assert response.status_code == 302
    product = Product.objects.get(name="Multi Variant Saree")

    variant_a = ProductVariant.objects.get(product=product, color=color_a)
    variant_b = ProductVariant.objects.get(product=product, color=color_b)

    assert variant_a.price == Decimal("3200")
    assert variant_b.price == Decimal("3400")
    assert variant_a.is_active is True
    assert variant_b.is_active is True

    assert ProductImage.objects.filter(variant=variant_a).count() == 1
    assert ProductImage.objects.filter(variant=variant_b).count() == 1

def test_product_create_variant_invalid_price(client, category, fabric):
    from adm_user.models import Color, Product, ProductVariant
    color = Color.objects.create(name="Emerald Green", hex_code="#50C878")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Bad Variant Price Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": [str(color.pk)],
        "variant_price": ["not-a-number"],
    })

    assert response.status_code == 200  # re-renders form, same as top-level validation errors
    assert not Product.objects.filter(name="Bad Variant Price Saree").exists()


def test_product_create_variant_invalid_color_id(client, category, fabric):
    from adm_user.models import Product

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Bad Variant Color Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": ["99999"],  # nonexistent color
        "variant_price": ["1800"],
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Bad Variant Color Saree").exists()
    
def test_product_create_variant_image_wrong_content_type(client, category, fabric, color):
    from django.core.files.uploadedfile import SimpleUploadedFile
    bad_file = SimpleUploadedFile("bad.txt", b"just some text", content_type="text/plain")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Bad Variant Image Type Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": [str(color.pk)],
        "variant_price": ["1800"],
        f"variant_images_{color.pk}": [bad_file],
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Bad Variant Image Type Saree").exists()


def test_product_create_variant_image_oversized(client, category, fabric, color):
    from django.core.files.uploadedfile import SimpleUploadedFile
    oversized = SimpleUploadedFile("big.jpg", b"0" * (6 * 1024 * 1024), content_type="image/jpeg")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Oversized Variant Image Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": [str(color.pk)],
        "variant_price": ["1800"],
        f"variant_images_{color.pk}": [oversized],
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Oversized Variant Image Saree").exists()


def test_product_create_variant_image_corrupted(client, category, fabric, color):
    from django.core.files.uploadedfile import SimpleUploadedFile
    corrupted = SimpleUploadedFile("fake.png", b"this is not actually a png file", content_type="image/png")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Corrupted Variant Image Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": [str(color.pk)],
        "variant_price": ["1800"],
        f"variant_images_{color.pk}": [corrupted],
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Corrupted Variant Image Saree").exists()


def test_product_create_default_image_wrong_content_type(client, category, fabric):
    from django.core.files.uploadedfile import SimpleUploadedFile
    bad_file = SimpleUploadedFile("bad.txt", b"just some text", content_type="text/plain")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Bad Default Image Type Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "default_images": [bad_file],
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Bad Default Image Type Saree").exists()
    
def test_product_update_get_renders_form_with_existing_data(client, category, fabric):
    product = Product.objects.create(
        name="Existing Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:update", args=[product.slug])

    response = client.get(url)

    assert response.status_code == 200
    assert response.context["product"] == product

def test_product_update_valid_fields(client, category, fabric):
    product = Product.objects.create(
        name="Old Name Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:update", args=[product.slug])

    response = client.post(url, {
        "name": "New Name Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2500",
    })

    assert response.status_code == 302
    assert response.url == reverse("adm_user:products")

    product.refresh_from_db()
    assert product.name == "New Name Saree"
    assert product.base_price == Decimal("2500")

def test_product_update_missing_name(client, category, fabric):
    product = Product.objects.create(
        name="Keep This Name", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:update", args=[product.slug])

    response = client.post(url, {
        "name": "",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
    })

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.name == "Keep This Name"

def test_product_update_not_found(client):
    url = reverse("adm_user:update", args=["nonexistent-slug"])
    response = client.get(url)
    assert response.status_code == 404

def test_product_update_existing_variant_price_updated_not_duplicated(client, category, fabric, color):
    product = Product.objects.create(
        name="Variant Update Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    variant = ProductVariant.objects.create(product=product, color=color, price=Decimal("1800"))

    url = reverse("adm_user:update", args=[product.slug])
    response = client.post(url, {
        "name": product.name,
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": [str(color.pk)],
        "variant_price": ["1900"],
    })

    assert response.status_code == 302

    # only one variant for this color — confirms get_or_create updated, not duplicated
    assert ProductVariant.objects.filter(product=product, color=color).count() == 1

    variant.refresh_from_db()
    assert variant.price == Decimal("1900")
    assert variant.is_active is True

def test_product_update_dropped_variant_deactivated(client, category, fabric, color):
    product = Product.objects.create(
        name="Drop Variant Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    variant = ProductVariant.objects.create(product=product, color=color, price=Decimal("1800"), is_active=True)
    ProductImage.objects.create(product=product, variant=variant, image_url="http://localhost/media/x.png", display_order=0)

    url = reverse("adm_user:update", args=[product.slug])
    response = client.post(url, {
        "name": product.name,
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
    })

    assert response.status_code == 302

    variant.refresh_from_db()
    assert variant.is_active is False
    assert ProductImage.objects.filter(variant=variant).count() == 0

def test_product_variant_delete(client, category, fabric, color):
    product = Product.objects.create(
        name="Direct Delete Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    variant = ProductVariant.objects.create(product=product, color=color, price=Decimal("1800"), is_active=True)
    ProductImage.objects.create(product=product, variant=variant, image_url="http://localhost/media/y.png", display_order=0)

    url = reverse("adm_user:product_variant_delete", args=[variant.pk])
    response = client.post(url)

    assert response.status_code == 200
    assert response.json()["ok"] is True

    variant.refresh_from_db()
    assert variant.is_active is False
    assert ProductImage.objects.filter(variant=variant).count() == 0
    assert ProductVariant.objects.filter(pk=variant.pk).exists()


def test_product_variant_delete_not_found(client):
    url = reverse("adm_user:product_variant_delete", args=[99999])
    response = client.post(url)
    assert response.status_code == 404

def test_product_image_delete(client, category, fabric):
    product = Product.objects.create(
        name="Image Delete Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    image = ProductImage.objects.create(
        product=product, variant=None, image_url="http://localhost/media/z.png", display_order=0
    )

    url = reverse("adm_user:product_image_delete", args=[image.pk])
    response = client.post(url)

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert not ProductImage.objects.filter(pk=image.pk).exists()


def test_product_image_delete_not_found(client):
    url = reverse("adm_user:product_image_delete", args=[99999])
    response = client.post(url)
    assert response.status_code == 404


def test_product_delete(client, category, fabric):
    product = Product.objects.create(
        name="Delete Me Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:delete", args=[product.slug])

    response = client.post(url)

    assert response.status_code == 302
    assert response.url == reverse("adm_user:products")
    assert not Product.objects.filter(pk=product.pk).exists()


def test_product_delete_not_found(client):
    url = reverse("adm_user:delete", args=["nonexistent-slug"])
    response = client.post(url)
    assert response.status_code == 404


def test_product_delete_ajax(client, category, fabric):
    product = Product.objects.create(
        name="AJAX Delete Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:delete", args=[product.slug])

    response = client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["id"] == product.id
    assert not Product.objects.filter(pk=product.pk).exists()


def test_product_delete_cleans_up_images(client, category, fabric):
    product = Product.objects.create(
        name="Image Cleanup Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    ProductImage.objects.create(
        product=product, variant=None, image_url="http://localhost/media/a.png", display_order=0
    )
    ProductImage.objects.create(
        product=product, variant=None, image_url="http://localhost/media/b.png", display_order=1
    )

    url = reverse("adm_user:delete", args=[product.slug])
    response = client.post(url)

    assert response.status_code == 302
    assert not ProductImage.objects.filter(product_id=product.pk).exists()

def test_product_delete_calls_delete_stored_image(client, category, fabric, monkeypatch):
    import adm_user.views as views_module
    deleted_urls = []

    def traced_delete_stored_image(url):
        deleted_urls.append(url)

    monkeypatch.setattr(views_module, "_delete_stored_image", traced_delete_stored_image)

    product = Product.objects.create(
        name="Traced Delete Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    ProductImage.objects.create(
        product=product, variant=None, image_url="http://localhost/media/a.png", display_order=0
    )
    ProductImage.objects.create(
        product=product, variant=None, image_url="http://localhost/media/b.png", display_order=1
    )

    url = reverse("adm_user:delete", args=[product.slug])
    client.post(url)

    assert set(deleted_urls) == {"http://localhost/media/a.png", "http://localhost/media/b.png"}
    
from adm_user.models import Product, ProductVariant, ProductImage, SignatureCategoryItem, Fabric
def test_product_image_fifth_variant_image_rejected(client, category, fabric, color):
    from django.core.exceptions import ValidationError

    product = Product.objects.create(
        name="Max Images Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    variant = ProductVariant.objects.create(product=product, color=color, price=Decimal("1800"))

    for i in range(4):
        ProductImage.objects.create(
            product=product, variant=variant,
            image_url=f"http://localhost/media/img{i}.png", display_order=i,
        )

    with pytest.raises(ValidationError, match="already has 4 images"):
        ProductImage.objects.create(
            product=product, variant=variant,
            image_url="http://localhost/media/img5.png", display_order=4,
        )

    assert ProductImage.objects.filter(variant=variant).count() == 4

def test_product_create_with_print_type(client, category, fabric):
    from adm_user.models import Print
    print_type = Print.objects.create(name="Floral")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Printed Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "print_type": print_type.pk,
        "base_price": "1800",
    })

    assert response.status_code == 302
    product = Product.objects.get(name="Printed Saree")
    assert product.print_type == print_type


def test_product_create_without_print_type(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Plain Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "1800",
        # no print_type sent at all
    })

    assert response.status_code == 302
    product = Product.objects.get(name="Plain Saree")
    assert product.print_type is None

def test_product_create_with_tags(client, category, fabric):
    from adm_user.models import Tag
    tag_a = Tag.objects.create(name="Wedding")
    tag_b = Tag.objects.create(name="Festive")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Tagged Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "1800",
        "tags": [str(tag_a.pk), str(tag_b.pk)],
    })

    assert response.status_code == 302
    product = Product.objects.get(name="Tagged Saree")
    assert set(product.tags.all()) == {tag_a, tag_b}


def test_product_create_without_tags(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Untagged Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "1800",
    })

    assert response.status_code == 302
    product = Product.objects.get(name="Untagged Saree")
    assert product.tags.count() == 0


def test_product_update_replaces_tags(client, category, fabric):
    from adm_user.models import Tag
    tag_a = Tag.objects.create(name="Wedding")
    tag_b = Tag.objects.create(name="Festive")
    tag_c = Tag.objects.create(name="Casual")

    product = Product.objects.create(
        name="Retag Saree", category=category, fabric=fabric, base_price=Decimal("1800")
    )
    product.tags.set([tag_a, tag_b])

    url = reverse("adm_user:update", args=[product.slug])
    response = client.post(url, {
        "name": product.name,
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "1800",
        "tags": [str(tag_c.pk)],  # swap entirely — drop a/b, add c
    })

    assert response.status_code == 302
    product.refresh_from_db()
    assert set(product.tags.all()) == {tag_c}

def test_product_create_duplicate_product_code(client, category, fabric):
    Product.objects.create(
        name="First Saree", category=category, fabric=fabric,
        base_price=Decimal("1800"), product_code="SBB-001",
    )

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Second Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "product_code": "SBB-001",
    })

    assert response.status_code == 200  # re-renders form on validation failure
    assert not Product.objects.filter(name="Second Saree").exists()


def test_product_create_blank_product_code_allowed_multiple_times(client, category, fabric):
    """product_code is nullable+blank, so multiple products with no code shouldn't collide."""
    url = reverse("adm_user:create")

    response_a = client.post(url, {
        "name": "No Code Saree A", "category": category.pk, "fabric": fabric.pk, "base_price": "1500",
    })
    response_b = client.post(url, {
        "name": "No Code Saree B", "category": category.pk, "fabric": fabric.pk, "base_price": "1500",
    })

    assert response_a.status_code == 302
    assert response_b.status_code == 302
    assert Product.objects.filter(name="No Code Saree A").exists()
    assert Product.objects.filter(name="No Code Saree B").exists()

def test_product_create_with_optional_text_fields(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Detailed Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2200",
        "saree_length": "5.5 Meter",
        "blouse_type": "Stitched",
        "blouse_size": "M",
        "weaving_style": "Handloom",
        "border_style": "Zari Border",
        "care_instructions": "Dry clean only",
    })

    assert response.status_code == 302
    product = Product.objects.get(name="Detailed Saree")
    assert product.saree_length == "5.5 Meter"
    assert product.blouse_type == "Stitched"
    assert product.blouse_size == "M"
    assert product.weaving_style == "Handloom"
    assert product.border_style == "Zari Border"
    assert product.care_instructions == "Dry clean only"


def test_product_create_without_optional_text_fields(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Minimal Detail Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2200",
    })

    assert response.status_code == 302
    product = Product.objects.get(name="Minimal Detail Saree")
    assert product.saree_length == ""
    assert product.blouse_type == ""
    assert product.blouse_size == ""
    assert product.weaving_style == ""
    assert product.border_style == ""
    assert product.care_instructions == ""


def test_product_create_blouse_not_included(client, category, fabric):
    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "No Blouse Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "1800",
        "blouse_included": "No",
    })

    assert response.status_code == 302
    product = Product.objects.get(name="No Blouse Saree")
    assert product.blouse_included is False

def test_product_create_duplicate_name_gets_unique_slug(client, category, fabric):
    url = reverse("adm_user:create")

    response_a = client.post(url, {
        "name": "Kanjivaram Saree", "category": category.pk, "fabric": fabric.pk, "base_price": "3000",
    })
    response_b = client.post(url, {
        "name": "Kanjivaram Saree", "category": category.pk, "fabric": fabric.pk, "base_price": "3200",
    })

    assert response_a.status_code == 302
    assert response_b.status_code == 302

    products = Product.objects.filter(name="Kanjivaram Saree").order_by("id")
    assert products.count() == 2

    slug_a, slug_b = products[0].slug, products[1].slug
    assert slug_a != slug_b
    assert slug_a  # not empty
    assert slug_b  # not empty

# ---- #5: Adding a new variant on update, alongside an existing one ----
def test_product_update_adds_new_variant_alongside_existing(client, category, fabric, color):
    from adm_user.models import Color
    color_b = Color.objects.create(name="Emerald Green", hex_code="#50C878")

    product = Product.objects.create(
        name="Add Variant Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    existing_variant = ProductVariant.objects.create(product=product, color=color, price=Decimal("1800"))

    url = reverse("adm_user:update", args=[product.slug])
    response = client.post(url, {
        "name": product.name,
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": [str(color.pk), str(color_b.pk)],  # existing + new
        "variant_price": ["1800", "1900"],
    })

    assert response.status_code == 302

    existing_variant.refresh_from_db()
    assert existing_variant.is_active is True  # untouched, still active

    new_variant = ProductVariant.objects.get(product=product, color=color_b)
    assert new_variant.price == Decimal("1900")
    assert new_variant.is_active is True

    assert ProductVariant.objects.filter(product=product).count() == 2


# ---- #6: Adding images to an existing variant on update (staying under cap) ----
def test_product_update_adds_images_to_existing_variant_under_cap(client, category, fabric, color):
    product = Product.objects.create(
        name="Add Images Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    variant = ProductVariant.objects.create(product=product, color=color, price=Decimal("1800"))
    ProductImage.objects.create(product=product, variant=variant, image_url="http://localhost/media/existing1.png", display_order=0)
    ProductImage.objects.create(product=product, variant=variant, image_url="http://localhost/media/existing2.png", display_order=1)

    url = reverse("adm_user:update", args=[product.slug])
    response = client.post(url, {
        "name": product.name,
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": [str(color.pk)],
        "variant_price": ["1800"],
        f"variant_images_{color.pk}": [make_test_image(name="new1.png"), make_test_image(name="new2.png")],
    })

    assert response.status_code == 302
    # 2 existing + 2 new = 4, exactly at the cap — should succeed
    assert ProductImage.objects.filter(variant=variant).count() == 4


# ---- #7: Hitting the 4-image cap via the view (not just the raw model) ----
def test_product_update_exceeding_image_cap_via_view_rolls_back(client, category, fabric, color):
    product = Product.objects.create(
        name="Cap Exceed Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    variant = ProductVariant.objects.create(product=product, color=color, price=Decimal("1800"))
    for i in range(4):
        ProductImage.objects.create(
            product=product, variant=variant,
            image_url=f"http://localhost/media/existing{i}.png", display_order=i,
        )

    url = reverse("adm_user:update", args=[product.slug])
    response = client.post(url, {
        "name": product.name,
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "variant_color_id": [str(color.pk)],
        "variant_price": ["1800"],
        f"variant_images_{color.pk}": [make_test_image(name="one_too_many.png")],  # 5th image
    })

    # _save_variants_and_images validates images (type/size) in Phase 1, but the
    # MAX_IMAGES_PER_VARIANT check only lives in ProductImage.clean(), which fires
    # during Phase 2's ProductImage.objects.create(...) — i.e. mid-save, not
    # pre-validated like color/price. The outer try/except in product_update
    # catches ValidationError, so this should re-render (200), not 500.
    assert response.status_code == 200
    # still exactly 4 — the 5th was never actually committed, and no partial state remains
    assert ProductImage.objects.filter(variant=variant).count() == 4


# ---- #8: Default image validation — oversized and corrupted ----
def test_product_create_default_image_oversized(client, category, fabric):
    from django.core.files.uploadedfile import SimpleUploadedFile
    oversized = SimpleUploadedFile("big.jpg", b"0" * (6 * 1024 * 1024), content_type="image/jpeg")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Oversized Default Image Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "default_images": [oversized],
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Oversized Default Image Saree").exists()


def test_product_create_default_image_corrupted(client, category, fabric):
    from django.core.files.uploadedfile import SimpleUploadedFile
    corrupted = SimpleUploadedFile("fake.png", b"this is not actually a png file", content_type="image/png")

    url = reverse("adm_user:create")
    response = client.post(url, {
        "name": "Corrupted Default Image Saree",
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "default_images": [corrupted],
    })

    assert response.status_code == 200
    assert not Product.objects.filter(name="Corrupted Default Image Saree").exists()


# ---- #9: Update-side validation parity ----
def test_product_update_invalid_category_id(client, category, fabric):
    product = Product.objects.create(
        name="Update Bad Category Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:update", args=[product.slug])

    response = client.post(url, {
        "name": product.name,
        "category": 99999,
        "fabric": fabric.pk,
        "base_price": "2000",
    })

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.category == category  # unchanged


def test_product_update_inactive_category_rejected(client, category, fabric):
    inactive_category = SignatureCategoryItem.objects.create(
        name="Inactive Update Cat", display_order=1, is_active=False
    )
    product = Product.objects.create(
        name="Update Inactive Cat Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:update", args=[product.slug])

    response = client.post(url, {
        "name": product.name,
        "category": inactive_category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
    })

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.category == category  # unchanged


def test_product_update_invalid_price(client, category, fabric):
    product = Product.objects.create(
        name="Update Bad Price Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:update", args=[product.slug])

    response = client.post(url, {
        "name": product.name,
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "not-a-number",
    })

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.base_price == Decimal("2000")  # unchanged


def test_product_update_discount_not_less_than_base(client, category, fabric):
    product = Product.objects.create(
        name="Update Bad Discount Saree", category=category, fabric=fabric, base_price=Decimal("2000")
    )
    url = reverse("adm_user:update", args=[product.slug])

    response = client.post(url, {
        "name": product.name,
        "category": category.pk,
        "fabric": fabric.pk,
        "base_price": "2000",
        "discount_price": "2000",  # equal, not less
    })

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.discount_price is None  # unchanged

def test_products_export_no_filters(client, category, fabric):
    Product.objects.create(
        name="Export Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=10, is_active=True,
    )

    url = reverse("adm_user:products_export")
    response = client.get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/csv"
    assert response["Content-Disposition"] == 'attachment; filename="products_export.csv"'

    content = response.content.decode("utf-8")
    lines = content.strip().split("\r\n")

    header = lines[0].split(",")
    assert header == [
        "Name", "Product Code", "Category", "Fabric", "Print Type",
        "Base Price", "Discount Price", "Stock Quantity", "Stock Status", "Active",
    ]

    row = lines[1].split(",")
    assert row[0] == "Export Saree"
    assert row[2] == category.name
    assert row[3] == fabric.name
    assert row[7] == "10"
    assert row[8] == "In Stock"
    assert row[9] == "Yes"


def test_products_export_excludes_inactive_products(client, category, fabric):
    Product.objects.create(
        name="Active Export Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), is_active=True,
    )
    Product.objects.create(
        name="Inactive Export Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), is_active=False,
    )

    url = reverse("adm_user:products_export")
    response = client.get(url)

    content = response.content.decode("utf-8")
    assert "Active Export Saree" in content
    assert "Inactive Export Saree" not in content
import csv
import io


def test_products_export_stock_status_buckets(client, category, fabric):
    Product.objects.create(
        name="Out of Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=0,
    )
    Product.objects.create(
        name="Low Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=3,
    )
    Product.objects.create(
        name="In Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )

    url = reverse("adm_user:products_export")
    response = client.get(url)

    reader = csv.DictReader(io.StringIO(response.content.decode("utf-8")))
    rows = {row["Name"]: row for row in reader}

    assert rows["Out of Stock Saree"]["Stock Status"] == "Out of Stock"
    assert rows["Low Stock Saree"]["Stock Status"] == "Low Stock"
    assert rows["In Stock Saree"]["Stock Status"] == "In Stock"


def test_products_export_stock_filter(client, category, fabric):
    Product.objects.create(name="Out A", category=category, fabric=fabric, base_price=Decimal("2000"), stock_quantity=0)
    Product.objects.create(name="Low B", category=category, fabric=fabric, base_price=Decimal("2000"), stock_quantity=3)
    Product.objects.create(name="In C", category=category, fabric=fabric, base_price=Decimal("2000"), stock_quantity=10)

    url = reverse("adm_user:products_export")

    response_out = client.get(url, {"stock": "out"})
    names_out = {r["Name"] for r in csv.DictReader(io.StringIO(response_out.content.decode("utf-8")))}
    assert names_out == {"Out A"}

    response_low = client.get(url, {"stock": "low"})
    names_low = {r["Name"] for r in csv.DictReader(io.StringIO(response_low.content.decode("utf-8")))}
    assert names_low == {"Low B"}

    response_in = client.get(url, {"stock": "in"})
    names_in = {r["Name"] for r in csv.DictReader(io.StringIO(response_in.content.decode("utf-8")))}
    assert names_in == {"In C"}


def test_products_export_category_filter(client, category, fabric):
    from adm_user.models import SignatureCategoryItem
    other_category = SignatureCategoryItem.objects.create(name="Other Category", display_order=2)

    Product.objects.create(name="In Category", category=category, fabric=fabric, base_price=Decimal("2000"))
    Product.objects.create(name="Other Category Product", category=other_category, fabric=fabric, base_price=Decimal("2000"))

    url = reverse("adm_user:products_export")
    response = client.get(url, {"category": category.pk})

    names = {r["Name"] for r in csv.DictReader(io.StringIO(response.content.decode("utf-8")))}
    assert names == {"In Category"}


def test_products_export_search_filter(client, category, fabric):
    Product.objects.create(name="Banarasi Silk Saree", category=category, fabric=fabric, base_price=Decimal("2000"))
    Product.objects.create(name="Cotton Saree", category=category, fabric=fabric, base_price=Decimal("2000"), product_code="COT-01")

    url = reverse("adm_user:products_export")

    response_by_name = client.get(url, {"search": "banarasi"})
    names = {r["Name"] for r in csv.DictReader(io.StringIO(response_by_name.content.decode("utf-8")))}
    assert names == {"Banarasi Silk Saree"}

    response_by_code = client.get(url, {"search": "COT-01"})
    names_by_code = {r["Name"] for r in csv.DictReader(io.StringIO(response_by_code.content.decode("utf-8")))}
    assert names_by_code == {"Cotton Saree"}

def test_products_export_csv_safe_escapes_formula_injection(client, category, fabric):
    Product.objects.create(
        name="=cmd|'/c calc'!A1", category=category, fabric=fabric,
        base_price=Decimal("2000"), product_code="+SUM(A1:A2)",
    )

    url = reverse("adm_user:products_export")
    response = client.get(url)

    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8"))))
    row = rows[0]

    # _csv_safe prefixes a leading ', so spreadsheet apps treat it as literal text, not a formula
    assert row["Name"].startswith("'=cmd")
    assert row["Product Code"].startswith("'+SUM")


def test_products_export_csv_safe_leaves_normal_values_untouched(client, category, fabric):
    Product.objects.create(
        name="Normal Saree Name", category=category, fabric=fabric,
        base_price=Decimal("2000"), product_code="SBB-042",
    )

    url = reverse("adm_user:products_export")
    response = client.get(url)

    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8"))))
    row = rows[0]

    assert row["Name"] == "Normal Saree Name"
    assert row["Product Code"] == "SBB-042"
def test_product_stock_update_valid(client, category, fabric):
    product = Product.objects.create(
        name="Stock Update Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(
        url,
        data=json.dumps({"stock_quantity": 20}),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["stock_quantity"] == 20
    assert data["stock_status"] == "in"

    product.refresh_from_db()
    assert product.stock_quantity == 20



def test_product_stock_update_to_zero_is_out(client, category, fabric):
    product = Product.objects.create(
        name="Zero Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(url, data=json.dumps({"stock_quantity": 0}), content_type="application/json")

    assert response.status_code == 200
    data = response.json()
    assert data["stock_quantity"] == 0
    assert data["stock_status"] == "out"


def test_product_stock_update_low_bucket(client, category, fabric):
    product = Product.objects.create(
        name="Low Stock Update Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=10,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(url, data=json.dumps({"stock_quantity": 3}), content_type="application/json")

    assert response.status_code == 200
    assert response.json()["stock_status"] == "low"


def test_product_stock_update_not_found(client):
    url = reverse("adm_user:product_stock_update", args=["nonexistent-slug"])
    response = client.post(url, data=json.dumps({"stock_quantity": 5}), content_type="application/json")
    assert response.status_code == 404
    
def test_product_stock_update_rejects_float(client, category, fabric):
    product = Product.objects.create(
        name="Float Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(url, data=json.dumps({"stock_quantity": 5.5}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Enter a valid stock quantity."
    product.refresh_from_db()
    assert product.stock_quantity == 5  # unchanged


def test_product_stock_update_accepts_whole_number_float(client, category, fabric):
    """5.0 should be accepted — int(5.0) == float(5.0), so the whole-number check passes."""
    product = Product.objects.create(
        name="Whole Float Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(url, data=json.dumps({"stock_quantity": 8.0}), content_type="application/json")

    assert response.status_code == 200
    product.refresh_from_db()
    assert product.stock_quantity == 8


def test_product_stock_update_rejects_negative(client, category, fabric):
    product = Product.objects.create(
        name="Negative Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(url, data=json.dumps({"stock_quantity": -3}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Stock can't be negative."
    product.refresh_from_db()
    assert product.stock_quantity == 5  # unchanged


def test_product_stock_update_rejects_non_numeric_string(client, category, fabric):
    product = Product.objects.create(
        name="Bad String Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(url, data=json.dumps({"stock_quantity": "abc"}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Enter a valid stock quantity."


def test_product_stock_update_rejects_invalid_json(client, category, fabric):
    product = Product.objects.create(
        name="Bad JSON Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(url, data="not valid json{{{", content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Enter a valid stock quantity."


def test_product_stock_update_missing_key(client, category, fabric):
    product = Product.objects.create(
        name="Missing Key Stock Saree", category=category, fabric=fabric,
        base_price=Decimal("2000"), stock_quantity=5,
    )
    url = reverse("adm_user:product_stock_update", args=[product.slug])

    response = client.post(url, data=json.dumps({}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Enter a valid stock quantity."