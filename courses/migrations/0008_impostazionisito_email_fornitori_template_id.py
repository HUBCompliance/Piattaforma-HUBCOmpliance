from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0007_impostazionisito_emailjs_template_id_allerta_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='impostazionisito',
            name='email_fornitori_template_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Email Template ID (Fornitori)'),
        ),
    ]
