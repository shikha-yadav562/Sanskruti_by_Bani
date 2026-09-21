# adm_user/tests/test_website_builder_views.py
import pytest
import json
from django.urls import reverse
from adm_user.models import (
    HeroSlideMain, HeroSlideImageOnly, HeroSlideOffer,
    SweetMemoriesSection, SweetMemoryImage, MemoriesOfferSlide, MemoriesSlide3,
    OfferBarItem, HeaderSettings, FooterSettings, AboutUsSection,
    SignatureCategoryItem,
)

pytestmark = pytest.mark.django_db


def test_website_builder_page_loads(client):
    url = reverse("adm_user:website_builder")
    response = client.get(url)

    assert response.status_code == 200
    # every singleton should auto-create via .load() on first access
    assert response.context["hero_main"].pk == 1
    assert response.context["hero_image_only"].pk == 1
    assert response.context["hero_offer"].pk == 1
    assert response.context["memories"].pk == 1
    assert response.context["memories_offer_slide"].pk == 1
    assert response.context["memories_slide3"].pk == 1
    assert response.context["header"].pk == 1
    assert response.context["footer"].pk == 1
    assert response.context["about"].pk == 1


def test_website_builder_singleton_load_never_duplicates(client):
    """Calling .load() repeatedly (e.g. across multiple page requests) shouldn't create pk=2, 3, etc."""
    url = reverse("adm_user:website_builder")

    client.get(url)
    client.get(url)
    client.get(url)

    assert HeroSlideMain.objects.count() == 1
    assert FooterSettings.objects.count() == 1
    assert AboutUsSection.objects.count() == 1

# adm_user/tests/test_website_builder_views.py
import io
import pytest
from PIL import Image as PILImage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from django.urls import reverse
from adm_user.models import HeroSlideMain

pytestmark = pytest.mark.django_db


def make_test_image(name="test.png", size=(10, 10)):
    buf = io.BytesIO()
    PILImage.new("RGB", size, color=(0, 128, 0)).save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


def test_save_hero_main_text_only(client):
    url = reverse("adm_user:save_hero_main")
    response = client.post(url, {
        "tagline": "Timeless Elegance",
        "title_line_1": "Handwoven",
        "title_line_2": "Heritage",
        "title_line_3": "Sarees",
        "description": "Crafted with love.",
        "button_1_text": "Shop Now",
        "button_2_text": "Learn More",
    })

    assert response.status_code == 200
    assert response.json()["saved"] is True

    hero = HeroSlideMain.load()
    assert hero.tagline == "Timeless Elegance"
    assert hero.title_line_3 == "Sarees"
    assert hero.button_2_text == "Learn More"


def test_save_hero_main_with_images(client):
    url = reverse("adm_user:save_hero_main")
    response = client.post(url, {
        "tagline": "With Images",
        "desktop_image": make_test_image(name="desktop.png"),
        "mobile_image": make_test_image(name="mobile.png"),
    })

    assert response.status_code == 200
    hero = HeroSlideMain.load()
    assert hero.desktop_image.name
    assert hero.mobile_image.name
    assert default_storage.exists(hero.desktop_image.name)
    assert default_storage.exists(hero.mobile_image.name)


def test_save_hero_main_image_replace_deletes_old_file(client, django_capture_on_commit_callbacks):
    url = reverse("adm_user:save_hero_main")

    with django_capture_on_commit_callbacks(execute=True):
        client.post(url, {"desktop_image": make_test_image(name="first.png")})

    hero = HeroSlideMain.load()
    old_name = hero.desktop_image.name
    assert default_storage.exists(old_name)

    with django_capture_on_commit_callbacks(execute=True):
        client.post(url, {"desktop_image": make_test_image(name="second.png")})

    hero.refresh_from_db()
    new_name = hero.desktop_image.name
    assert new_name != old_name
    assert default_storage.exists(new_name)
    assert not default_storage.exists(old_name)


def test_save_hero_main_invalid_image_type(client):
    url = reverse("adm_user:save_hero_main")
    bad_file = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")

    response = client.post(url, {"desktop_image": bad_file})

    assert response.status_code == 400
    hero = HeroSlideMain.load()
    assert not hero.desktop_image  # unchanged / still empty


def test_save_hero_main_text_field_too_long_rejected(client):
    url = reverse("adm_user:save_hero_main")
    response = client.post(url, {
        "tagline": "x" * 101,  # max_length=100
    })

    assert response.status_code == 400
    hero = HeroSlideMain.load()
    assert hero.tagline != "x" * 101


def test_save_hero_main_partial_update_preserves_untouched_fields(client):
    url = reverse("adm_user:save_hero_main")
    client.post(url, {"tagline": "Original Tagline", "title_line_1": "Original Title"})

    # second save only touches tagline
    response = client.post(url, {"tagline": "Updated Tagline"})

    assert response.status_code == 200
    hero = HeroSlideMain.load()
    assert hero.tagline == "Updated Tagline"
    assert hero.title_line_1 == "Original Title"  # untouched


def test_save_hero_main_empty_post_still_succeeds(client):
    url = reverse("adm_user:save_hero_main")
    response = client.post(url, {})

    assert response.status_code == 200
    assert response.json()["saved"] is True


def test_save_hero_main_rejects_get(client):
    url = reverse("adm_user:save_hero_main")
    response = client.get(url)
    assert response.status_code == 405

from adm_user.models import HeroSlideImageOnly, HeroSlideOffer


def test_save_hero_image_only_with_images(client):
    url = reverse("adm_user:save_hero_image_only")
    response = client.post(url, {
        "desktop_image": make_test_image(name="io_desktop.png"),
        "mobile_image": make_test_image(name="io_mobile.png"),
    })

    assert response.status_code == 200
    hero = HeroSlideImageOnly.load()
    assert hero.desktop_image.name
    assert hero.mobile_image.name


def test_save_hero_image_only_invalid_image_type(client):
    url = reverse("adm_user:save_hero_image_only")
    bad_file = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")

    response = client.post(url, {"desktop_image": bad_file})

    assert response.status_code == 400
    hero = HeroSlideImageOnly.load()
    assert not hero.desktop_image


def test_save_hero_image_only_rejects_get(client):
    url = reverse("adm_user:save_hero_image_only")
    response = client.get(url)
    assert response.status_code == 405


def test_save_hero_image_only_replace_deletes_old_file(client, django_capture_on_commit_callbacks):
    url = reverse("adm_user:save_hero_image_only")

    with django_capture_on_commit_callbacks(execute=True):
        client.post(url, {"mobile_image": make_test_image(name="io_first.png")})

    hero = HeroSlideImageOnly.load()
    old_name = hero.mobile_image.name
    assert default_storage.exists(old_name)

    with django_capture_on_commit_callbacks(execute=True):
        client.post(url, {"mobile_image": make_test_image(name="io_second.png")})

    hero.refresh_from_db()
    assert not default_storage.exists(old_name)
    assert default_storage.exists(hero.mobile_image.name)


def test_save_hero_offer_with_images(client):
    url = reverse("adm_user:save_hero_offer")
    response = client.post(url, {
        "desktop_image": make_test_image(name="offer_desktop.png"),
        "mobile_image": make_test_image(name="offer_mobile.png"),
    })

    assert response.status_code == 200
    hero = HeroSlideOffer.load()
    assert hero.desktop_image.name
    assert hero.mobile_image.name


def test_save_hero_offer_invalid_image_type(client):
    url = reverse("adm_user:save_hero_offer")
    bad_file = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")

    response = client.post(url, {"desktop_image": bad_file})

    assert response.status_code == 400
    hero = HeroSlideOffer.load()
    assert not hero.desktop_image


def test_save_hero_offer_rejects_get(client):
    url = reverse("adm_user:save_hero_offer")
    response = client.get(url)
    assert response.status_code == 405

from adm_user.models import SweetMemoriesSection, MemoriesOfferSlide, MemoriesSlide3


def test_save_memories_section_text_only(client):
    url = reverse("adm_user:save_memories_section")
    response = client.post(url, {
        "section_label": "Our Story",
        "main_heading": "Woven Into\nYour Beautiful Moments",
        "paragraph_text": "Every saree tells a story.",
    })

    assert response.status_code == 200
    section = SweetMemoriesSection.load()
    assert section.section_label == "Our Story"
    assert "Beautiful Moments" in section.main_heading


def test_save_memories_section_rejects_get(client):
    url = reverse("adm_user:save_memories_section")
    response = client.get(url)
    assert response.status_code == 405


def test_save_memories_offer_slide_text_and_images(client):
    url = reverse("adm_user:save_memories_offer_slide")
    response = client.post(url, {
        "frame1_title": "Custom Frame 1 Title",
        "frame1_badge": "Custom Badge",
        "frame2_ribbon": "30% OFF",
        "frame3_wa_link": "https://wa.me/919999999999",
        "desktop_image": make_test_image(name="mos_desktop.png"),
        "frame1_image": make_test_image(name="mos_frame1.png"),
    })

    assert response.status_code == 200
    slide = MemoriesOfferSlide.load()
    assert slide.frame1_title == "Custom Frame 1 Title"
    assert slide.frame1_badge == "Custom Badge"
    assert slide.frame2_ribbon == "30% OFF"
    assert slide.frame3_wa_link == "https://wa.me/919999999999"
    assert slide.desktop_image.name
    assert slide.frame1_image.name
    # untouched frame2/frame3 images should remain empty
    assert not slide.frame2_image
    assert not slide.frame3_image


def test_save_memories_offer_slide_defaults_preserved_when_not_sent(client):
    """frame titles/badges/ribbons have model defaults — confirm an empty POST doesn't wipe them."""
    url = reverse("adm_user:save_memories_offer_slide")
    response = client.post(url, {})

    assert response.status_code == 200
    slide = MemoriesOfferSlide.load()
    assert slide.frame1_title == "Timeless Tradition Collection"  # model default, untouched
    assert slide.frame2_badge == "✦ WELCOME OFFER · 10% OFF ✦"


def test_save_memories_offer_slide_invalid_image_rejects_whole_save(client):
    url = reverse("adm_user:save_memories_offer_slide")
    bad_file = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")

    response = client.post(url, {
        "frame1_title": "Should Not Be Saved",
        "frame2_image": bad_file,
    })

    assert response.status_code == 400
    slide = MemoriesOfferSlide.load()
    # frame1_title change should roll back along with the bad image, since both
    # are inside the same transaction.atomic() block
    assert slide.frame1_title == "Timeless Tradition Collection"  # unchanged


def test_save_memories_offer_slide_rejects_get(client):
    url = reverse("adm_user:save_memories_offer_slide")
    response = client.get(url)
    assert response.status_code == 405


def test_save_memories_slide3_with_images(client):
    url = reverse("adm_user:save_memories_slide3")
    response = client.post(url, {
        "desktop_image": make_test_image(name="slide3_desktop.png"),
        "mobile_image": make_test_image(name="slide3_mobile.png"),
    })

    assert response.status_code == 200
    slide = MemoriesSlide3.load()
    assert slide.desktop_image.name
    assert slide.mobile_image.name


def test_save_memories_slide3_rejects_get(client):
    url = reverse("adm_user:save_memories_slide3")
    response = client.get(url)
    assert response.status_code == 405

from adm_user.models import SweetMemoryImage


def test_memory_images_get_empty(client):
    url = reverse("adm_user:memory_images")
    response = client.get(url)

    assert response.status_code == 200
    assert response.json()["images"] == []


def test_memory_images_upload_single(client):
    url = reverse("adm_user:memory_images")
    response = client.post(url, {"images": [make_test_image(name="mem1.png")]})

    assert response.status_code == 201
    data = response.json()
    assert len(data["created"]) == 1
    assert data["created"][0]["display_order"] == 0
    assert SweetMemoryImage.objects.count() == 1


def test_memory_images_upload_multiple_assigns_sequential_order(client):
    url = reverse("adm_user:memory_images")
    response = client.post(url, {
        "images": [make_test_image(name="a.png"), make_test_image(name="b.png"), make_test_image(name="c.png")]
    })

    assert response.status_code == 201
    orders = [img["display_order"] for img in response.json()["created"]]
    assert orders == [0, 1, 2]


def test_memory_images_upload_no_files(client):
    url = reverse("adm_user:memory_images")
    response = client.post(url, {})

    assert response.status_code == 400
    assert response.json()["error"] == "No images provided."


def test_memory_images_next_order_accounts_for_gaps(client):
    """With images at display_order 0,1,2 — delete order 0, leaving a gap.
    The next upload should continue from max()+1 = 3, not fall into the gap at 0."""
    url = reverse("adm_user:memory_images")
    client.post(url, {"images": [make_test_image(name="x.png"), make_test_image(name="y.png"), make_test_image(name="z.png")]})

    img_to_delete = SweetMemoryImage.objects.get(display_order=0)
    client.delete(reverse("adm_user:memory_image_delete", args=[img_to_delete.pk]))

    response = client.post(url, {"images": [make_test_image(name="w.png")]})
    assert response.json()["created"][0]["display_order"] == 3
    
def test_memory_images_invalid_file_rejects_whole_batch(client):
    url = reverse("adm_user:memory_images")
    bad_file = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")

    response = client.post(url, {
        "images": [make_test_image(name="good.png"), bad_file]
    })

    assert response.status_code == 400
    # neither should be saved, since validation happens before any save
    assert SweetMemoryImage.objects.count() == 0


def test_memory_image_delete(client):
    url = reverse("adm_user:memory_images")
    client.post(url, {"images": [make_test_image(name="delete_me.png")]})
    image = SweetMemoryImage.objects.first()

    response = client.delete(reverse("adm_user:memory_image_delete", args=[image.pk]))

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not SweetMemoryImage.objects.filter(pk=image.pk).exists()


def test_memory_image_delete_not_found(client):
    response = client.delete(reverse("adm_user:memory_image_delete", args=[99999]))
    assert response.status_code == 404


def test_memory_images_reorder(client):
    url = reverse("adm_user:memory_images")
    client.post(url, {"images": [make_test_image(name="a.png"), make_test_image(name="b.png"), make_test_image(name="c.png")]})
    imgs = list(SweetMemoryImage.objects.order_by("display_order"))
    a, b, c = imgs[0], imgs[1], imgs[2]

    reorder_url = reverse("adm_user:memory_images_reorder")
    response = client.post(
        reorder_url,
        data=json.dumps({"order": [c.pk, a.pk, b.pk]}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["reordered"] is True

    c.refresh_from_db(); a.refresh_from_db(); b.refresh_from_db()
    assert c.display_order == 0
    assert a.display_order == 1
    assert b.display_order == 2


def test_memory_images_reorder_invalid_id(client):
    reorder_url = reverse("adm_user:memory_images_reorder")
    response = client.post(
        reorder_url,
        data=json.dumps({"order": [99999]}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Some images could not be found."


def test_memory_images_reorder_invalid_json(client):
    reorder_url = reverse("adm_user:memory_images_reorder")
    response = client.post(reorder_url, data="not json{{{", content_type="application/json")
    assert response.status_code == 400
    
def test_memory_images_single_request_exceeds_cap(client):
    url = reverse("adm_user:memory_images")
    files = [make_test_image(name=f"img{i}.png") for i in range(21)]  # 21 > 20

    response = client.post(url, {"images": files})

    assert response.status_code == 400
    assert response.json()["error"] == "You can upload a maximum of 20 images at once."
    assert SweetMemoryImage.objects.count() == 0


def test_memory_images_single_request_at_exact_cap_succeeds(client):
    url = reverse("adm_user:memory_images")
    files = [make_test_image(name=f"img{i}.png") for i in range(20)]  # exactly 20

    response = client.post(url, {"images": files})

    assert response.status_code == 201
    assert len(response.json()["created"]) == 20
    assert SweetMemoryImage.objects.count() == 20


def test_memory_images_cumulative_total_exceeds_cap(client):
    """18 existing images + 3 new = 21, over the cap, even though 3 alone is well under 20."""
    url = reverse("adm_user:memory_images")

    # seed 18 existing images first
    for i in range(18):
        client.post(url, {"images": [make_test_image(name=f"existing{i}.png")]})
    assert SweetMemoryImage.objects.count() == 18

    response = client.post(url, {"images": [make_test_image(name=f"new{i}.png") for i in range(3)]})

    assert response.status_code == 400
    assert response.json()["error"] == "Maximum 20 memory images allowed."
    # none of the 3 new ones should have been saved — still exactly 18
    assert SweetMemoryImage.objects.count() == 18


def test_memory_images_cumulative_total_at_exact_cap_succeeds(client):
    """18 existing + 2 new = 20, exactly at the cap — should succeed."""
    url = reverse("adm_user:memory_images")

    for i in range(18):
        client.post(url, {"images": [make_test_image(name=f"existing{i}.png")]})

    response = client.post(url, {"images": [make_test_image(name="new1.png"), make_test_image(name="new2.png")]})

    assert response.status_code == 201
    assert SweetMemoryImage.objects.count() == 20

from adm_user.models import HeaderSettings, OfferBarItem


def test_save_header_settings_with_logo(client):
    url = reverse("adm_user:save_header_settings")
    response = client.post(url, {"logo": make_test_image(name="logo.png")})

    assert response.status_code == 200
    header = HeaderSettings.load()
    assert header.logo.name


def test_save_header_settings_invalid_image_type(client):
    url = reverse("adm_user:save_header_settings")
    bad_file = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")

    response = client.post(url, {"logo": bad_file})

    assert response.status_code == 400
    header = HeaderSettings.load()
    assert not header.logo


def test_save_header_settings_rejects_get(client):
    url = reverse("adm_user:save_header_settings")
    response = client.get(url)
    assert response.status_code == 405


def test_offer_items_get_empty(client):
    url = reverse("adm_user:offer_items")
    response = client.get(url)

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_offer_items_create(client):
    url = reverse("adm_user:offer_items")
    response = client.post(
        url,
        data=json.dumps({"text": "Free shipping over ₹2000"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Free shipping over ₹2000"
    assert OfferBarItem.objects.count() == 1
    assert OfferBarItem.objects.first().display_order == 1  # last_order (0, since none exist) + 1


def test_offer_items_create_assigns_incrementing_display_order(client):
    url = reverse("adm_user:offer_items")
    client.post(url, data=json.dumps({"text": "First"}), content_type="application/json")
    client.post(url, data=json.dumps({"text": "Second"}), content_type="application/json")

    items = list(OfferBarItem.objects.order_by("display_order"))
    assert items[0].display_order == 1
    assert items[1].display_order == 2


def test_offer_items_create_missing_text(client):
    url = reverse("adm_user:offer_items")
    response = client.post(url, data=json.dumps({"text": ""}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Offer text is required."


def test_offer_items_update_existing(client):
    url = reverse("adm_user:offer_items")
    create_response = client.post(url, data=json.dumps({"text": "Original"}), content_type="application/json")
    item_id = create_response.json()["id"]

    response = client.post(url, data=json.dumps({"id": item_id, "text": "Updated"}), content_type="application/json")

    assert response.status_code == 200
    assert response.json()["text"] == "Updated"
    assert OfferBarItem.objects.count() == 1  # still just one row, not a duplicate
    assert OfferBarItem.objects.get(pk=item_id).text == "Updated"


def test_offer_items_update_not_found(client):
    url = reverse("adm_user:offer_items")
    response = client.post(url, data=json.dumps({"id": 99999, "text": "Ghost"}), content_type="application/json")

    assert response.status_code == 404
    assert response.json()["error"] == "Item not found."


def test_offer_items_invalid_id_type(client):
    url = reverse("adm_user:offer_items")
    response = client.post(url, data=json.dumps({"id": "not-an-int", "text": "Bad ID"}), content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"] == "Invalid item id."


def test_offer_items_invalid_json(client):
    url = reverse("adm_user:offer_items")
    response = client.post(url, data="not json{{{", content_type="application/json")
    assert response.status_code == 400


def test_offer_item_delete(client):
    url = reverse("adm_user:offer_items")
    create_response = client.post(url, data=json.dumps({"text": "Delete Me"}), content_type="application/json")
    item_id = create_response.json()["id"]

    response = client.delete(reverse("adm_user:offer_item_delete", args=[item_id]))

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not OfferBarItem.objects.filter(pk=item_id).exists()


def test_offer_item_delete_not_found(client):
    response = client.delete(reverse("adm_user:offer_item_delete", args=[99999]))
    assert response.status_code == 404

from adm_user.models import FooterSettings, AboutUsSection


def test_save_footer_settings_text_fields(client):
    url = reverse("adm_user:save_footer_settings")
    response = client.post(url, {
        "brand_name": "Sanskruti By Bani",
        "brand_description": "Handwoven heritage sarees.",
        "store_address": "Kalyan, Maharashtra",
        "phone_number": "9876543210",
        "email": "hello@sanskrutibybani.com",
        "instagram_link": "https://instagram.com/sanskrutibybani",
        "whatsapp_number": "919372471363",
    })

    assert response.status_code == 200
    footer = FooterSettings.load()
    assert footer.brand_name == "Sanskruti By Bani"
    assert footer.email == "hello@sanskrutibybani.com"
    assert footer.instagram_link == "https://instagram.com/sanskrutibybani"


def test_save_footer_settings_invalid_email_rejected(client):
    url = reverse("adm_user:save_footer_settings")
    response = client.post(url, {"email": "not-an-email"})

    assert response.status_code == 400
    footer = FooterSettings.load()
    assert footer.email != "not-an-email"


def test_save_footer_settings_invalid_url_rejected(client):
    url = reverse("adm_user:save_footer_settings")
    response = client.post(url, {"instagram_link": "not-a-url"})

    assert response.status_code == 400
    footer = FooterSettings.load()
    assert footer.instagram_link != "not-a-url"


def test_save_footer_settings_partial_update_preserves_other_fields(client):
    url = reverse("adm_user:save_footer_settings")
    client.post(url, {"brand_name": "Original Name", "phone_number": "1111111111"})

    response = client.post(url, {"brand_name": "Updated Name"})

    assert response.status_code == 200
    footer = FooterSettings.load()
    assert footer.brand_name == "Updated Name"
    assert footer.phone_number == "1111111111"  # untouched


def test_save_footer_settings_rejects_get(client):
    url = reverse("adm_user:save_footer_settings")
    response = client.get(url)
    assert response.status_code == 405


def test_save_about_section_text_and_image(client):
    url = reverse("adm_user:save_about_section")
    response = client.post(url, {
        "small_title": "Our Journey",
        "main_heading": "A Legacy of Craftsmanship",
        "highlight_quote": "Every thread tells a story.",
        "main_paragraph": "We started with a single loom.",
        "ending_signoff": "With love, Bani.",
        "floating_top_text": "Since 2020",
        "floating_bottom_text": "Handwoven with care",
        "about_image": make_test_image(name="about.png"),
    })

    assert response.status_code == 200
    about = AboutUsSection.load()
    assert about.small_title == "Our Journey"
    assert about.highlight_quote == "Every thread tells a story."
    assert about.about_image.name


def test_save_about_section_invalid_image_type(client):
    url = reverse("adm_user:save_about_section")
    bad_file = SimpleUploadedFile("bad.txt", b"not an image", content_type="text/plain")

    response = client.post(url, {"small_title": "Should Not Save", "about_image": bad_file})

    assert response.status_code == 400
    about = AboutUsSection.load()
    assert about.small_title != "Should Not Save"  # text save rolled back with the bad image


def test_save_about_section_rejects_get(client):
    url = reverse("adm_user:save_about_section")
    response = client.get(url)
    assert response.status_code == 405

# ---- Untouched image preserved when not resent (representative singletons) ----

def test_save_hero_main_image_untouched_when_not_resent(client):
    url = reverse("adm_user:save_hero_main")
    client.post(url, {"desktop_image": make_test_image(name="keep_me.png")})

    hero = HeroSlideMain.load()
    original_name = hero.desktop_image.name
    assert original_name

    # second save only touches a text field, no image sent
    response = client.post(url, {"tagline": "New Tagline"})

    assert response.status_code == 200
    hero.refresh_from_db()
    assert hero.desktop_image.name == original_name
    assert default_storage.exists(original_name)


def test_save_header_settings_logo_untouched_when_no_change_sent(client):
    url = reverse("adm_user:save_header_settings")
    client.post(url, {"logo": make_test_image(name="logo_keep.png")})

    header = HeaderSettings.load()
    original_name = header.logo.name
    assert original_name

    # resend with no files at all
    response = client.post(url, {})

    assert response.status_code == 200
    header.refresh_from_db()
    assert header.logo.name == original_name


def test_save_about_section_image_untouched_when_only_text_resent(client):
    url = reverse("adm_user:save_about_section")
    client.post(url, {"small_title": "First", "about_image": make_test_image(name="about_keep.png")})

    about = AboutUsSection.load()
    original_name = about.about_image.name
    assert original_name

    response = client.post(url, {"small_title": "Updated"})

    assert response.status_code == 200
    about.refresh_from_db()
    assert about.about_image.name == original_name
    assert about.small_title == "Updated"


# ---- Oversized image rejection (25MB builder limit) ----

def test_save_hero_main_oversized_image_rejected(client):
    url = reverse("adm_user:save_hero_main")
    oversized = SimpleUploadedFile(
        "big.jpg", b"0" * (26 * 1024 * 1024), content_type="image/jpeg"  # 26MB > 25MB limit
    )

    response = client.post(url, {"desktop_image": oversized})

    assert response.status_code == 400
    hero = HeroSlideMain.load()
    assert not hero.desktop_image


def test_save_header_settings_oversized_logo_rejected(client):
    url = reverse("adm_user:save_header_settings")
    oversized = SimpleUploadedFile(
        "big.jpg", b"0" * (26 * 1024 * 1024), content_type="image/jpeg"
    )

    response = client.post(url, {"logo": oversized})

    assert response.status_code == 400
    header = HeaderSettings.load()
    assert not header.logo


# ---- Dimension/pixel limit rejection (monkeypatched, same pattern as SignatureCategoryItem) ----

def test_save_hero_main_image_exceeds_max_width(client, monkeypatch):
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_WIDTH", 50)

    url = reverse("adm_user:save_hero_main")
    image = make_test_image(size=(100, 20))

    response = client.post(url, {"desktop_image": image})

    assert response.status_code == 400
    hero = HeroSlideMain.load()
    assert not hero.desktop_image


def test_save_hero_main_image_exceeds_max_pixels(client, monkeypatch):
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_WIDTH", 200)
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_HEIGHT", 200)
    monkeypatch.setattr("adm_user.views.MAX_IMAGE_PIXELS", 1000)

    url = reverse("adm_user:save_hero_main")
    image = make_test_image(size=(100, 100))  # 10,000px > patched 1,000, each side < 200

    response = client.post(url, {"desktop_image": image})

    assert response.status_code == 400
    hero = HeroSlideMain.load()
    assert not hero.desktop_image


# ---- memory_images GET reflects order after reorder ----

def test_memory_images_get_reflects_order_after_reorder(client):
    url = reverse("adm_user:memory_images")
    client.post(url, {"images": [make_test_image(name="a.png"), make_test_image(name="b.png"), make_test_image(name="c.png")]})
    imgs = list(SweetMemoryImage.objects.order_by("display_order"))
    a, b, c = imgs[0], imgs[1], imgs[2]

    reorder_url = reverse("adm_user:memory_images_reorder")
    client.post(reorder_url, data=json.dumps({"order": [c.pk, a.pk, b.pk]}), content_type="application/json")

    response = client.get(url)
    ids_in_order = [img["id"] for img in response.json()["images"]]
    assert ids_in_order == [c.pk, a.pk, b.pk]


# ---- offer_items GET reflects display_order ----

def test_offer_items_get_reflects_display_order(client):
    url = reverse("adm_user:offer_items")
    r1 = client.post(url, data=json.dumps({"text": "First"}), content_type="application/json")
    r2 = client.post(url, data=json.dumps({"text": "Second"}), content_type="application/json")
    r3 = client.post(url, data=json.dumps({"text": "Third"}), content_type="application/json")

    # update the first one's text — shouldn't change its display_order/position
    client.post(url, data=json.dumps({"id": r1.json()["id"], "text": "First Updated"}), content_type="application/json")

    response = client.get(url)
    texts_in_order = [item["text"] for item in response.json()["items"]]
    assert texts_in_order == ["First Updated", "Second", "Third"]


# ---- save_about_section text-only, no image ----

def test_save_about_section_text_only_no_image(client):
    url = reverse("adm_user:save_about_section")
    response = client.post(url, {
        "small_title": "Text Only Title",
        "main_heading": "Text Only Heading",
    })

    assert response.status_code == 200
    about = AboutUsSection.load()
    assert about.small_title == "Text Only Title"
    assert not about.about_image  # never set, and about_image has no blank=True


# ---- HeaderSettings / AboutUsSection non-blank image field, first .load() with nothing set ----

def test_header_settings_load_with_no_logo_ever_set_does_not_crash(client):
    """HeaderSettings.logo has no blank=True — confirm .load()'s get_or_create doesn't
    choke on creating row 1 with an empty logo field."""
    url = reverse("adm_user:website_builder")
    response = client.get(url)

    assert response.status_code == 200
    header = HeaderSettings.load()
    assert header.pk == 1
    assert not header.logo  # empty, but the row exists without error


def test_about_section_load_with_no_image_ever_set_does_not_crash(client):
    url = reverse("adm_user:website_builder")
    response = client.get(url)

    assert response.status_code == 200
    about = AboutUsSection.load()
    assert about.pk == 1
    assert not about.about_image