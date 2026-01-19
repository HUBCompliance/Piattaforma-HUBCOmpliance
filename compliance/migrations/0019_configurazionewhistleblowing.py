from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0008_azienda_mod_extra_modules'),
        ('compliance', '0018_segnalazionewhistleblowing_allegatowhistleblowing'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigurazioneWhistleblowing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_pacchetto', models.CharField(default='Pacchetto Whistleblowing Standard', max_length=100)),
                ('data_attivazione', models.DateField(auto_now_add=True)),
                ('attivo', models.BooleanField(default=True)),
                ('azienda', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wb_config', to='user_auth.azienda')),
            ],
        ),
    ]
