# Migration to recreate Document model with UUID primary key

import uuid
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        # Drop existing tables and recreate with new structure
        migrations.RunSQL(
            "DROP TABLE IF EXISTS documents_history;",
            reverse_sql="-- No reverse operation"
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS documents_analysis;",
            reverse_sql="-- No reverse operation"
        ),
        migrations.RunSQL(
            "DROP TABLE IF EXISTS documents_document;",
            reverse_sql="-- No reverse operation"
        ),
        
        # Recreate Document model with UUID primary key
        migrations.CreateModel(
            name='Document',
            fields=[
                ('document_id', models.UUIDField(primary_key=True, help_text='UUID provided by frontend for consistent identification across Firebase services')),
                ('title', models.CharField(max_length=255, validators=[django.core.validators.MinLengthValidator(1)])),
                ('owner_uid', models.CharField(db_index=True, help_text='Firebase user ID', max_length=128)),
                ('file_type', models.CharField(help_text='MIME type of original document', max_length=128)),
                ('storage_path', models.CharField(help_text='GCS path to original document', max_length=512)),
                ('extracted_text', models.TextField(blank=True, help_text='Plain text extracted from document', null=True)),
                ('language_code', models.CharField(blank=True, help_text='ISO 639-1 language code', max_length=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending Processing'), ('PROCESSING', 'Processing'), ('ANALYZED', 'Analysis Complete'), ('ERROR', 'Processing Error')], default='PENDING', max_length=20)),
            ],
            options={
                'ordering': ['-updated_at'],
                'indexes': [models.Index(fields=['owner_uid', '-updated_at'], name='documents_d_owner_u_new_idx')],
            },
        ),
        
        # Recreate Analysis model with foreign key to document_id
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version', models.PositiveIntegerField()),
                ('target_language', models.CharField(blank=True, help_text='ISO 639-1 target language code', max_length=10, null=True)),
                ('summary', models.JSONField(default=dict, help_text='Summary in simple language')),
                ('key_points', models.JSONField(default=list, help_text='Key points with citations')),
                ('risk_alerts', models.JSONField(default=list, help_text='Risk and compliance alerts')),
                ('token_usage', models.JSONField(default=dict, help_text='LLM token usage stats')),
                ('completion_time', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analyses', to='documents.document', to_field='document_id')),
            ],
            options={
                'ordering': ['-version'],
                'indexes': [models.Index(fields=['document', '-version'], name='documents_a_documen_new_idx')],
                'unique_together': {('document', 'version')},
            },
        ),
        
        # Recreate History model with foreign key to document_id
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATED', 'Document Created'), ('UPLOADED', 'File Uploaded'), ('ANALYZED', 'Analysis Completed'), ('REPORT', 'Report Generated'), ('DOWNLOADED', 'Report Downloaded'), ('ERROR', 'Error Occurred')], max_length=20)),
                ('actor_uid', models.CharField(help_text='Firebase user ID', max_length=128)),
                ('version', models.PositiveIntegerField(blank=True, null=True)),
                ('payload', models.JSONField(blank=True, help_text='Additional action data', null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='documents.document', to_field='document_id')),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['document', '-timestamp'], name='documents_h_documen_new_idx')],
            },
        ),
    ]