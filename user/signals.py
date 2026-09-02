from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

HOMEPAGE_MODELS = {
    "HeroSlideOffer", "HeroSlideMain", "HeroSlideImageOnly", "HeaderSettings",
    "OfferBarItem", "FooterSettings", "AboutUsSection", "SweetMemoriesSection",
    "SweetMemoryImage", "MemoriesOfferSlide", "MemoriesSlide3",
    "SignatureCategoryItem", "Tag", "Product", "ProductImage",
}


@receiver(post_save)
@receiver(post_delete)
def invalidate_homepage_cache(sender, **kwargs):
    if sender.__name__ in HOMEPAGE_MODELS:
        cache.delete("homepage_context")