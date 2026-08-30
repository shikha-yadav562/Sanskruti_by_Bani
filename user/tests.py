from django.test import TestCase

# Create your tests here.
# tests/test_submit_review.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import ProductReview
from adm_user.models import Product, SignatureCategoryItem, Fabric

User = get_user_model()


class SubmitReviewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='pass1234',
        )

        self.category = SignatureCategoryItem.objects.create(name='Paithani')
        self.fabric = Fabric.objects.create(name='Silk')

        self.product = Product.objects.create(
            name='Test Saree',
            slug='test-saree',
            category=self.category,
            fabric=self.fabric,
            base_price=1500,
            is_active=True,
        )

        self.client.login(email='testuser@example.com', password='pass1234')
        self.url = reverse('user:submit_review')

    def test_requires_login(self):
        self.client.logout()
        response = self.client.post(self.url, {'product_slug': self.product.slug})
        self.assertEqual(response.status_code, 302)  # redirect to login

    def test_rejects_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)  # require_POST

    def test_valid_submission_creates_review(self):
        response = self.client.post(self.url, {
            'product_slug': self.product.slug,
            'title': 'Great saree',
            'comment': 'Loved the fabric quality.',
            'rating': 5,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        review = ProductReview.objects.get(product_slug=self.product.slug)
        self.assertEqual(review.user, self.user)
        self.assertFalse(review.is_approved)
        self.assertFalse(review.is_verified_buyer)

    def test_missing_product_slug_fails(self):
        response = self.client.post(self.url, {'title': 'x', 'comment': 'y', 'rating': 5})
        self.assertEqual(response.status_code, 400)
        self.assertIn('product', response.json()['error'].lower())

    def test_nonexistent_product_returns_404(self):
        response = self.client.post(self.url, {
            'product_slug': 'does-not-exist',
            'title': 'x', 'comment': 'y', 'rating': 5,
        })
        self.assertEqual(response.status_code, 404)

    def test_missing_title_or_comment_fails(self):
        response = self.client.post(self.url, {
            'product_slug': self.product.slug, 'title': '', 'comment': 'y', 'rating': 5,
        })
        self.assertEqual(response.status_code, 400)

    def test_rating_out_of_range_rejected(self):
        response = self.client.post(self.url, {
            'product_slug': self.product.slug,
            'title': 'x', 'comment': 'y', 'rating': 999,
        })
        self.assertEqual(response.status_code, 400)

    def test_non_integer_rating_rejected(self):
        response = self.client.post(self.url, {
            'product_slug': self.product.slug,
            'title': 'x', 'comment': 'y', 'rating': 'not-a-number',
        })
        self.assertEqual(response.status_code, 400)

    def test_oversized_image_rejected(self):
        big_file = SimpleUploadedFile(
            'big.jpg', b'a' * (6 * 1024 * 1024), content_type='image/jpeg'
        )
        response = self.client.post(self.url, {
            'product_slug': self.product.slug,
            'title': 'x', 'comment': 'y', 'rating': 5,
            'image_1': big_file,
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_content_type_rejected(self):
        bad_file = SimpleUploadedFile(
            'file.exe', b'not an image', content_type='application/octet-stream'
        )
        response = self.client.post(self.url, {
            'product_slug': self.product.slug,
            'title': 'x', 'comment': 'y', 'rating': 5,
            'image_1': bad_file,
        })
        self.assertEqual(response.status_code, 400)

    def test_valid_image_upload_saves(self):
        # 1x1 pixel GIF, smallest valid image payload for a quick test
        gif_bytes = (
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,'
            b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        )
        img = SimpleUploadedFile('test.gif', gif_bytes, content_type='image/gif')
        # note: your content-type allowlist is jpeg/png/webp — this would
        # actually get rejected; swap content_type to one you allow, or
        # generate real bytes for that format if you want this to pass
        ...