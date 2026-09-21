# adm_user/tests/test_review_views.py
import pytest
from django.urls import reverse
from user.models import ProductReview
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def make_review():
    def _make(**kwargs):
        defaults = {
            "title": "Great saree",
            "comment": "Loved the fabric quality.",
            "rating": 5,
        }
        defaults.update(kwargs)
        return ProductReview.objects.create(**defaults)
    return _make


def test_reviews_management_lists_all_by_default(client, make_review):
    make_review(title="Approved Review", is_approved=True)
    make_review(title="Pending Review", is_approved=False)

    url = reverse("adm_user:reviews_management")
    response = client.get(url)

    assert response.status_code == 200
    titles = [r.title for r in response.context["reviews"]]
    assert "Approved Review" in titles
    assert "Pending Review" in titles
    assert response.context["status_filter"] == "all"


def test_reviews_management_filters_pending(client, make_review):
    make_review(title="Approved Review", is_approved=True)
    make_review(title="Pending Review", is_approved=False)

    url = reverse("adm_user:reviews_management")
    response = client.get(url, {"status": "pending"})

    titles = [r.title for r in response.context["reviews"]]
    assert titles == ["Pending Review"]
    assert response.context["status_filter"] == "pending"


def test_reviews_management_filters_approved(client, make_review):
    make_review(title="Approved Review", is_approved=True)
    make_review(title="Pending Review", is_approved=False)

    url = reverse("adm_user:reviews_management")
    response = client.get(url, {"status": "approved"})

    titles = [r.title for r in response.context["reviews"]]
    assert titles == ["Approved Review"]


def test_reviews_management_invalid_status_falls_back_to_all(client, make_review):
    make_review(title="Some Review", is_approved=True)

    url = reverse("adm_user:reviews_management")
    response = client.get(url, {"status": "bogus"})

    assert response.context["status_filter"] == "all"
    titles = [r.title for r in response.context["reviews"]]
    assert "Some Review" in titles


def test_reviews_management_pagination(client, make_review):
    for i in range(25):
        make_review(title=f"Review {i}")

    url = reverse("adm_user:reviews_management")
    response = client.get(url)

    # Paginator(reviews, 20) — page 1 should have 20, not all 25
    assert len(response.context["reviews"]) == 20

    response_page_2 = client.get(url, {"page": 2})
    assert len(response_page_2.context["reviews"]) == 5
    
def test_approve_review_toggles_from_false_to_true(client, make_review):
    review = make_review(title="Toggle Me", is_approved=False)
    url = reverse("adm_user:approve_review", args=[review.pk])

    response = client.post(url)

    assert response.status_code == 200
    assert response.json()["is_approved"] is True

    review.refresh_from_db()
    assert review.is_approved is True


def test_approve_review_toggles_from_true_to_false(client, make_review):
    review = make_review(title="Untoggle Me", is_approved=True)
    url = reverse("adm_user:approve_review", args=[review.pk])

    response = client.post(url)

    assert response.status_code == 200
    assert response.json()["is_approved"] is False

    review.refresh_from_db()
    assert review.is_approved is False


def test_approve_review_not_found(client):
    url = reverse("adm_user:approve_review", args=[99999])
    response = client.post(url)
    assert response.status_code == 404


def test_approve_review_rejects_get(client, make_review):
    """@require_http_methods(["POST"]) should reject GET with 405."""
    review = make_review(title="GET Not Allowed")
    url = reverse("adm_user:approve_review", args=[review.pk])

    response = client.get(url)

    assert response.status_code == 405

from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image as PILImage


def make_test_image(name="test.png"):
    buf = io.BytesIO()
    PILImage.new("RGB", (10, 10), color=(255, 0, 0)).save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


def test_delete_review_post(client, make_review):
    review = make_review(title="Delete Me POST")
    url = reverse("adm_user:delete_review", args=[review.pk])

    response = client.post(url)

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not ProductReview.objects.filter(pk=review.pk).exists()


def test_delete_review_via_delete_method(client, make_review):
    review = make_review(title="Delete Me DELETE-verb")
    url = reverse("adm_user:delete_review", args=[review.pk])

    response = client.delete(url)

    assert response.status_code == 200
    assert response.json()["deleted"] is True
    assert not ProductReview.objects.filter(pk=review.pk).exists()


def test_delete_review_not_found(client):
    url = reverse("adm_user:delete_review", args=[99999])
    response = client.post(url)
    assert response.status_code == 404


def test_delete_review_rejects_get(client, make_review):
    review = make_review(title="GET Not Allowed Delete")
    url = reverse("adm_user:delete_review", args=[review.pk])

    response = client.get(url)

    assert response.status_code == 405


def test_delete_review_removes_image_files(client, make_review):
    from django.core.files.storage import default_storage

    review = make_review(
        title="Delete With Images",
        image_1=make_test_image(name="img1.png"),
        image_2=make_test_image(name="img2.png"),
    )
    image_1_path = review.image_1.name
    image_2_path = review.image_2.name

    assert default_storage.exists(image_1_path)
    assert default_storage.exists(image_2_path)

    url = reverse("adm_user:delete_review", args=[review.pk])
    response = client.post(url)

    assert response.status_code == 200
    assert not default_storage.exists(image_1_path)
    assert not default_storage.exists(image_2_path)
    assert not ProductReview.objects.filter(pk=review.pk).exists()


def test_delete_review_without_images_succeeds(client, make_review):
    """image_1/2/3 are all null/blank — the `if f:` guard should just skip cleanly."""
    review = make_review(title="No Images To Delete")
    url = reverse("adm_user:delete_review", args=[review.pk])

    response = client.post(url)

    assert response.status_code == 200
    assert response.json()["deleted"] is True