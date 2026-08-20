# 0011_signaturecategoryitem_slug_alter_product_category.py

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adm_user', '0010_alter_heroslideimageonly_desktop_image_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='signaturecategoryitem',
            name='slug',
            field=models.SlugField(blank=True, max_length=120, default=''),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='products',
                to='adm_user.category',   # unchanged target — just adding null=True
            ),
        ),
    ]