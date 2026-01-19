from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0007_alter_adminreferente_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='azienda',
            name='mod_analisi_rischi',
            field=models.BooleanField(default=False, verbose_name='Attiva Analisi Rischi'),
        ),
        migrations.AddField(
            model_name='azienda',
            name='mod_asset',
            field=models.BooleanField(default=False, verbose_name='Attiva Asset Aziendali'),
        ),
        migrations.AddField(
            model_name='azienda',
            name='mod_fornitori',
            field=models.BooleanField(default=False, verbose_name='Attiva Fornitori'),
        ),
        migrations.AddField(
            model_name='azienda',
            name='mod_rete',
            field=models.BooleanField(default=False, verbose_name='Attiva Configurazione Rete'),
        ),
        migrations.AddField(
            model_name='azienda',
            name='mod_whistleblowing',
            field=models.BooleanField(default=False, verbose_name='Attiva Whistleblowing'),
        ),
    ]
