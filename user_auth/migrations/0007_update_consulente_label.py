from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_auth', '0006_alter_adminreferente_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='ruolo',
            field=models.CharField(
                choices=[
                    ('ADMIN', 'Amministratore di Sistema'),
                    ('CONSULENTE', 'Consulente'),
                    ('REFERENTE', 'Referente Privacy Aziendale'),
                    ('STUDENTE', 'Dipendente / Utente E-learning'),
                ],
                default='STUDENTE',
                max_length=20,
                verbose_name='Ruolo Utente',
            ),
        ),
    ]
