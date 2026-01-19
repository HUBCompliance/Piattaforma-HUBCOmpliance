from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('compliance', '0016_fornitore_allegatofornitore'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='rispostaquestionariofornitore',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='rispostaquestionariofornitore',
            name='azienda',
        ),
        migrations.AddField(
            model_name='rispostaquestionariofornitore',
            name='fornitore',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='risposte_clusit', to='compliance.fornitore'),
        ),
        migrations.AlterUniqueTogether(
            name='rispostaquestionariofornitore',
            unique_together={('fornitore', 'domanda')},
        ),
    ]
