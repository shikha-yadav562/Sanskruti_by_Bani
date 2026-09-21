# adm_user/tests/test_filter_views.py
import json
import pytest
from django.urls import reverse
from adm_user.models import Color

pytestmark = pytest.mark.django_db


def test_create_color_valid_data(client):
    url = reverse("adm_user:color_list_create")

    response = client.post(
        url,
        data=json.dumps({"name": "Maroon", "hex_code": "#800000"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Maroon"
    assert data["hex_code"] == "#800000"
    assert data["slug"]  # SlugMixin should have generated one

    assert Color.objects.filter(name="Maroon", hex_code="#800000").exists()

def test_create_fabric_valid_data(client):
    from adm_user.models import Fabric
    url = reverse("adm_user:fabric_list_create")

    response = client.post(
        url,
        data=json.dumps({"name": "Cotton"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Cotton"
    assert data["slug"]
    assert Fabric.objects.filter(name="Cotton").exists()


def test_create_print_valid_data(client):
    from adm_user.models import Print
    url = reverse("adm_user:print_list_create")

    response = client.post(
        url,
        data=json.dumps({"name": "Floral"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Floral"
    assert data["slug"]
    assert Print.objects.filter(name="Floral").exists()


def test_create_tag_valid_data(client):
    from adm_user.models import Tag
    url = reverse("adm_user:tag_list_create")

    response = client.post(
        url,
        data=json.dumps({"name": "Wedding"}),
        content_type="application/json",
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Wedding"
    assert data["slug"]
    assert Tag.objects.filter(name="Wedding").exists()

def test_create_color_duplicate_name(client):
    from adm_user.models import Color
    url = reverse("adm_user:color_list_create")

    client.post(url, data=json.dumps({"name": "Maroon", "hex_code": "#800000"}), content_type="application/json")
    response = client.post(url, data=json.dumps({"name": "maroon", "hex_code": "#900000"}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "This color already exists."
    assert Color.objects.filter(name__iexact="Maroon").count() == 1


def test_create_fabric_duplicate_name(client):
    from adm_user.models import Fabric
    url = reverse("adm_user:fabric_list_create")

    client.post(url, data=json.dumps({"name": "Cotton"}), content_type="application/json")
    response = client.post(url, data=json.dumps({"name": "cotton"}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "This fabric already exists."
    assert Fabric.objects.filter(name__iexact="Cotton").count() == 1


def test_create_print_duplicate_name(client):
    from adm_user.models import Print
    url = reverse("adm_user:print_list_create")

    client.post(url, data=json.dumps({"name": "Floral"}), content_type="application/json")
    response = client.post(url, data=json.dumps({"name": "floral"}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "This print already exists."
    assert Print.objects.filter(name__iexact="Floral").count() == 1


def test_create_tag_duplicate_name(client):
    from adm_user.models import Tag
    url = reverse("adm_user:tag_list_create")

    client.post(url, data=json.dumps({"name": "Wedding"}), content_type="application/json")
    response = client.post(url, data=json.dumps({"name": "wedding"}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "This tag already exists."
    assert Tag.objects.filter(name__iexact="Wedding").count() == 1

def test_create_color_empty_name(client):
    from adm_user.models import Color
    url = reverse("adm_user:color_list_create")

    response = client.post(url, data=json.dumps({"name": "", "hex_code": "#111111"}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Color name is required."
    assert not Color.objects.filter(hex_code="#111111").exists()


def test_create_fabric_empty_name(client):
    from adm_user.models import Fabric
    url = reverse("adm_user:fabric_list_create")

    response = client.post(url, data=json.dumps({"name": ""}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Fabric name is required."


def test_create_print_empty_name(client):
    from adm_user.models import Print
    url = reverse("adm_user:print_list_create")

    response = client.post(url, data=json.dumps({"name": ""}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Print name is required."


def test_create_tag_empty_name(client):
    from adm_user.models import Tag
    url = reverse("adm_user:tag_list_create")

    response = client.post(url, data=json.dumps({"name": ""}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Tag name is required."

def test_update_color(client):
    from adm_user.models import Color
    color = Color.objects.create(name="Old Name", hex_code="#111111")
    url = reverse("adm_user:color_update", args=[color.pk])

    response = client.put(
        url,
        data=json.dumps({"name": "New Name", "hex_code": "#222222"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["hex_code"] == "#222222"

    color.refresh_from_db()
    assert color.name == "New Name"
    assert color.hex_code == "#222222"


def test_update_color_not_found(client):
    url = reverse("adm_user:color_update", args=[99999])

    response = client.put(
        url,
        data=json.dumps({"name": "Doesn't Matter"}),
        content_type="application/json",
    )

    assert response.status_code == 404
    assert response.json()["error"] == "Color not found."

def test_update_color_regenerates_slug_on_rename(client):
    from adm_user.models import Color
    color = Color.objects.create(name="Crimson", hex_code="#DC143C")
    old_slug = color.slug

    url = reverse("adm_user:color_update", args=[color.pk])
    response = client.put(
        url,
        data=json.dumps({"name": "Scarlet", "hex_code": "#DC143C"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    color.refresh_from_db()
    assert color.slug != old_slug
    assert color.slug  # not empty — mixin regenerated it
    assert "scarlet" in color.slug.lower()


def test_update_color_same_name_keeps_slug(client):
    from adm_user.models import Color
    color = Color.objects.create(name="Crimson", hex_code="#DC143C")
    old_slug = color.slug

    url = reverse("adm_user:color_update", args=[color.pk])
    client.put(
        url,
        data=json.dumps({"name": "Crimson", "hex_code": "#FF0000"}),  # only hex changes
        content_type="application/json",
    )

    color.refresh_from_db()
    assert color.slug == old_slug  # name unchanged → slug untouched

def test_delete_color(client):
    from adm_user.models import Color
    color = Color.objects.create(name="Delete Me", hex_code="#000000")
    url = reverse("adm_user:color_delete", args=[color.pk])

    response = client.delete(url)

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not Color.objects.filter(pk=color.pk).exists()


def test_delete_color_not_found(client):
    url = reverse("adm_user:color_delete", args=[99999])
    response = client.delete(url)

    assert response.status_code == 404
    assert response.json()["error"] == "Color not found."


def test_delete_inactive_color_returns_not_found(client):
    """
    color_delete filters on is_active=True, so a color that's been
    soft-deactivated is invisible to this endpoint even though the
    row still exists in the DB.
    """
    from adm_user.models import Color
    color = Color.objects.create(name="Inactive Color", hex_code="#123456", is_active=False)
    url = reverse("adm_user:color_delete", args=[color.pk])

    response = client.delete(url)

    assert response.status_code == 404
    # row is untouched — still exists, just not reachable via this endpoint
    assert Color.objects.filter(pk=color.pk, is_active=False).exists()

def test_delete_color_with_linked_variant(client):
    from adm_user.models import Color, Product, ProductVariant, Fabric, SignatureCategoryItem
    category = SignatureCategoryItem.objects.create(name="Test Cat", display_order=1)
    fabric = Fabric.objects.create(name="Silk")
    product = Product.objects.create(name="Test Saree", category=category, fabric=fabric, base_price=1000)
    color = Color.objects.create(name="Ruby Red", hex_code="#9B111E")
    ProductVariant.objects.create(product=product, color=color)

    url = reverse("adm_user:color_delete", args=[color.pk])
    response = client.delete(url)

    assert response.status_code == 409
    assert response.json()["error"] == "This color is linked to existing products and can't be deleted."
    assert Color.objects.filter(pk=color.pk).exists()

# ---- Fabric: update ----
def test_update_fabric(client):
    from adm_user.models import Fabric
    fabric = Fabric.objects.create(name="Old Fabric")
    url = reverse("adm_user:fabric_update", args=[fabric.pk])

    response = client.put(url, data=json.dumps({"name": "New Fabric"}), content_type="application/json")

    assert response.status_code == 200
    fabric.refresh_from_db()
    assert fabric.name == "New Fabric"


def test_update_fabric_not_found(client):
    url = reverse("adm_user:fabric_update", args=[99999])
    response = client.put(url, data=json.dumps({"name": "X"}), content_type="application/json")

    assert response.status_code == 404
    assert response.json()["error"] == "Fabric not found."


# ---- Fabric: delete ----
def test_delete_fabric(client):
    from adm_user.models import Fabric
    fabric = Fabric.objects.create(name="Delete Me")
    url = reverse("adm_user:fabric_delete", args=[fabric.pk])

    response = client.delete(url)

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not Fabric.objects.filter(pk=fabric.pk).exists()


def test_delete_fabric_not_found(client):
    url = reverse("adm_user:fabric_delete", args=[99999])
    response = client.delete(url)

    assert response.status_code == 404
    assert response.json()["error"] == "Fabric not found."


# ---- Print: update ----
def test_update_print(client):
    from adm_user.models import Print
    p = Print.objects.create(name="Old Print")
    url = reverse("adm_user:print_update", args=[p.pk])

    response = client.put(url, data=json.dumps({"name": "New Print"}), content_type="application/json")

    assert response.status_code == 200
    p.refresh_from_db()
    assert p.name == "New Print"


def test_update_print_not_found(client):
    url = reverse("adm_user:print_update", args=[99999])
    response = client.put(url, data=json.dumps({"name": "X"}), content_type="application/json")

    assert response.status_code == 404
    assert response.json()["error"] == "Print not found."


# ---- Print: delete ----
def test_delete_print(client):
    from adm_user.models import Print
    p = Print.objects.create(name="Delete Me")
    url = reverse("adm_user:print_delete", args=[p.pk])

    response = client.delete(url)

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not Print.objects.filter(pk=p.pk).exists()


def test_delete_print_not_found(client):
    url = reverse("adm_user:print_delete", args=[99999])
    response = client.delete(url)

    assert response.status_code == 404
    assert response.json()["error"] == "Print not found."


def test_delete_print_with_linked_product(client):
    from adm_user.models import Print, Product, Fabric, SignatureCategoryItem
    category = SignatureCategoryItem.objects.create(name="Test Cat", display_order=1)
    fabric = Fabric.objects.create(name="Silk")
    p = Print.objects.create(name="Floral Linked")
    Product.objects.create(name="Test Saree", category=category, fabric=fabric, print_type=p, base_price=1000)

    url = reverse("adm_user:print_delete", args=[p.pk])
    response = client.delete(url)

    assert response.status_code == 409
    assert Print.objects.filter(pk=p.pk).exists()


# ---- Tag: update ----
def test_update_tag(client):
    from adm_user.models import Tag
    tag = Tag.objects.create(name="Old Tag")
    url = reverse("adm_user:tag_update", args=[tag.pk])

    response = client.put(url, data=json.dumps({"name": "New Tag"}), content_type="application/json")

    assert response.status_code == 200
    tag.refresh_from_db()
    assert tag.name == "New Tag"


def test_update_tag_not_found(client):
    url = reverse("adm_user:tag_update", args=[99999])
    response = client.put(url, data=json.dumps({"name": "X"}), content_type="application/json")

    assert response.status_code == 404
    assert response.json()["error"] == "Tag not found."


# ---- Tag: delete (no protected-delete case — M2M can't raise ProtectedError) ----
def test_delete_tag(client):
    from adm_user.models import Tag
    tag = Tag.objects.create(name="Delete Me")
    url = reverse("adm_user:tag_delete", args=[tag.pk])

    response = client.delete(url)

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not Tag.objects.filter(pk=tag.pk).exists()


def test_delete_tag_not_found(client):
    url = reverse("adm_user:tag_delete", args=[99999])
    response = client.delete(url)

    assert response.status_code == 404
    assert response.json()["error"] == "Tag not found."

def test_delete_fabric_with_linked_product(client):
    from adm_user.models import Fabric, Product, SignatureCategoryItem
    category = SignatureCategoryItem.objects.create(name="Test Cat", display_order=1)
    fabric = Fabric.objects.create(name="Silk")
    Product.objects.create(name="Test Saree", category=category, fabric=fabric, base_price=1000)

    url = reverse("adm_user:fabric_delete", args=[fabric.pk])
    response = client.delete(url)

    assert response.status_code == 409
    assert response.json()["error"] == "This fabric is linked to existing products and can't be deleted."
    assert Fabric.objects.filter(pk=fabric.pk).exists()

# ---- Update: duplicate name ----
def test_update_color_duplicate_name(client):
    from adm_user.models import Color
    Color.objects.create(name="Crimson", hex_code="#DC143C")
    target = Color.objects.create(name="Scarlet", hex_code="#FF2400")

    url = reverse("adm_user:color_update", args=[target.pk])
    response = client.put(url, data=json.dumps({"name": "crimson"}), content_type="application/json")

    assert response.status_code in (400, 409)
    target.refresh_from_db()
    assert target.name == "Scarlet"  # unchanged


def test_update_fabric_duplicate_name(client):
    from adm_user.models import Fabric
    Fabric.objects.create(name="Cotton")
    target = Fabric.objects.create(name="Silk")

    url = reverse("adm_user:fabric_update", args=[target.pk])
    response = client.put(url, data=json.dumps({"name": "cotton"}), content_type="application/json")

    assert response.status_code in (400, 409)
    target.refresh_from_db()
    assert target.name == "Silk"


def test_update_print_duplicate_name(client):
    from adm_user.models import Print
    Print.objects.create(name="Floral")
    target = Print.objects.create(name="Polka Dot")

    url = reverse("adm_user:print_update", args=[target.pk])
    response = client.put(url, data=json.dumps({"name": "floral"}), content_type="application/json")

    assert response.status_code in (400, 409)
    target.refresh_from_db()
    assert target.name == "Polka Dot"


def test_update_tag_duplicate_name(client):
    from adm_user.models import Tag
    Tag.objects.create(name="Wedding")
    target = Tag.objects.create(name="Party Wear")

    url = reverse("adm_user:tag_update", args=[target.pk])
    response = client.put(url, data=json.dumps({"name": "wedding"}), content_type="application/json")

    assert response.status_code in (400, 409)
    target.refresh_from_db()
    assert target.name == "Party Wear"


# ---- Update: empty name ----
def test_update_color_empty_name(client):
    from adm_user.models import Color
    target = Color.objects.create(name="Keep Me", hex_code="#000000")
    url = reverse("adm_user:color_update", args=[target.pk])

    response = client.put(url, data=json.dumps({"name": ""}), content_type="application/json")

    assert response.status_code == 400
    target.refresh_from_db()
    assert target.name == "Keep Me"


def test_update_fabric_empty_name(client):
    from adm_user.models import Fabric
    target = Fabric.objects.create(name="Keep Me")
    url = reverse("adm_user:fabric_update", args=[target.pk])

    response = client.put(url, data=json.dumps({"name": ""}), content_type="application/json")

    assert response.status_code == 400
    target.refresh_from_db()
    assert target.name == "Keep Me"


def test_update_print_empty_name(client):
    from adm_user.models import Print
    target = Print.objects.create(name="Keep Me")
    url = reverse("adm_user:print_update", args=[target.pk])

    response = client.put(url, data=json.dumps({"name": ""}), content_type="application/json")

    assert response.status_code == 400
    target.refresh_from_db()
    assert target.name == "Keep Me"


def test_update_tag_empty_name(client):
    from adm_user.models import Tag
    target = Tag.objects.create(name="Keep Me")
    url = reverse("adm_user:tag_update", args=[target.pk])

    response = client.put(url, data=json.dumps({"name": ""}), content_type="application/json")

    assert response.status_code == 400
    target.refresh_from_db()
    assert target.name == "Keep Me"


# ---- is_active=False lookup on update (Color only has confirmed view code for this) ----
def test_update_inactive_color_returns_not_found(client):
    from adm_user.models import Color
    color = Color.objects.create(name="Inactive", hex_code="#111111", is_active=False)
    url = reverse("adm_user:color_update", args=[color.pk])

    response = client.put(url, data=json.dumps({"name": "Renamed"}), content_type="application/json")

    assert response.status_code == 404
    color.refresh_from_db()
    assert color.name == "Inactive"


# ---- GET list endpoints ----
def test_get_color_list(client):
    from adm_user.models import Color
    Color.objects.create(name="Active Color", hex_code="#111111", is_active=True)
    Color.objects.create(name="Inactive Color", hex_code="#222222", is_active=False)

    url = reverse("adm_user:color_list_create")
    response = client.get(url)

    assert response.status_code == 200
    names = [c["name"] for c in response.json()["colors"]]
    assert "Active Color" in names
    assert "Inactive Color" not in names

def test_get_fabric_list(client):
    from adm_user.models import Fabric
    Fabric.objects.create(name="Active Fabric", is_active=True)
    Fabric.objects.create(name="Inactive Fabric", is_active=False)

    response = client.get(reverse("adm_user:fabric_list_create"))
    names = [f["name"] for f in response.json()["fabrics"]]
    assert "Active Fabric" in names
    assert "Inactive Fabric" not in names


def test_get_print_list(client):
    from adm_user.models import Print
    Print.objects.create(name="Active Print", is_active=True)
    Print.objects.create(name="Inactive Print", is_active=False)

    response = client.get(reverse("adm_user:print_list_create"))
    names = [p["name"] for p in response.json()["prints"]]
    assert "Active Print" in names
    assert "Inactive Print" not in names


def test_get_tag_list_includes_all_tags(client):
    """Tag has no is_active field — tag_list_create doesn't filter on it at all."""
    from adm_user.models import Tag
    Tag.objects.create(name="Tag One")
    Tag.objects.create(name="Tag Two")

    response = client.get(reverse("adm_user:tag_list_create"))
    names = [t["name"] for t in response.json()["tags"]]
    assert "Tag One" in names
    assert "Tag Two" in names