from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from adm_user.models import Product, SignatureCategoryItem


class StaticViewSitemap(Sitemap):
    """Home, catalogue, and the three policy pages."""

    changefreq_map = {
        "index": "daily",
        "catalogue": "daily",
        "terms_conditions": "yearly",
        "return_refund_policy": "yearly",
        "privacy_policy": "yearly",
    }
    priority_map = {
        "index": 1.0,
        "catalogue": 0.9,
        "terms_conditions": 0.3,
        "return_refund_policy": 0.3,
        "privacy_policy": 0.3,
    }

    def items(self):
        return list(self.changefreq_map.keys())

    def location(self, item):
        return reverse(f"user:{item}")

    def changefreq(self, item):
        return self.changefreq_map[item]

    def priority(self, item):
        return self.priority_map[item]


class CategorySitemap(Sitemap):
    """Every active category landing page — /catalogue/<slug>/"""

    changefreq = "weekly"
    priority = 0.85  # between catalogue (0.9) and individual products (0.8)

    def items(self):
        return SignatureCategoryItem.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("user:catalogue_category", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class ProductSitemap(Sitemap):
    """Every active saree listing."""

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True).order_by("-created_at")

    def location(self, obj):
        return reverse("user:product", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


sitemaps = {
    "static": StaticViewSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}