from adm_user.models import Category, HeaderSettings, FooterSettings, OfferBarItem

def global_website_data(request):
    try:
        return {
            'nav_categories': Category.objects.filter(is_active=True).order_by('created_at'),
            'header_settings': HeaderSettings.load(),
            'footer_settings': FooterSettings.load(),
            'offer_items': OfferBarItem.objects.all(),
        }
    except Exception:
        return {}

