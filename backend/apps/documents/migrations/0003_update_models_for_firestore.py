# Migration to update Analysis and History models for Firestore compatibility

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_recreate_with_uuid_pk'),
    ]

    operations = [
        # Update Analysis model for Firestore compatibility
        migrations.RunSQL(
            """
            -- Create new Analysis table with document_id field
            CREATE TABLE documents_analysis_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                target_language VARCHAR(10),
                summary TEXT NOT NULL,
                key_points TEXT NOT NULL,
                risk_alerts TEXT NOT NULL,
                token_usage TEXT NOT NULL,
                completion_time DATETIME NOT NULL
            );
            
            -- Copy existing data if any (convert foreign key to document_id)
            INSERT INTO documents_analysis_new (
                id, document_id, version, target_language, summary, 
                key_points, risk_alerts, token_usage, completion_time
            )
            SELECT 
                a.id, a.document_id, a.version, a.target_language, a.summary,
                a.key_points, a.risk_alerts, a.token_usage, a.completion_time
            FROM documents_analysis a;
            
            -- Drop old table and rename new one
            DROP TABLE documents_analysis;
            ALTER TABLE documents_analysis_new RENAME TO documents_analysis;
            
            -- Create indexes
            CREATE INDEX documents_analysis_document_id_idx ON documents_analysis (document_id);
            CREATE INDEX documents_analysis_document_id_version_idx ON documents_analysis (document_id, version DESC);
            CREATE UNIQUE INDEX documents_analysis_document_id_version_unique ON documents_analysis (document_id, version);
            """,
            reverse_sql="""
            -- Reverse migration would recreate foreign key structure
            DROP TABLE documents_analysis;
            """
        ),
        
        # Update History model for Firestore compatibility
        migrations.RunSQL(
            """
            -- Create new History table with document_id field
            CREATE TABLE documents_history_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                action VARCHAR(20) NOT NULL,
                actor_uid VARCHAR(128) NOT NULL,
                version INTEGER,
                payload TEXT,
                timestamp DATETIME NOT NULL
            );
            
            -- Copy existing data if any (convert foreign key to document_id)
            INSERT INTO documents_history_new (
                id, document_id, action, actor_uid, version, payload, timestamp
            )
            SELECT 
                h.id, h.document_id, h.action, h.actor_uid, h.version, h.payload, h.timestamp
            FROM documents_history h;
            
            -- Drop old table and rename new one
            DROP TABLE documents_history;
            ALTER TABLE documents_history_new RENAME TO documents_history;
            
            -- Create indexes
            CREATE INDEX documents_history_document_id_idx ON documents_history (document_id);
            CREATE INDEX documents_history_document_id_timestamp_idx ON documents_history (document_id, timestamp DESC);
            """,
            reverse_sql="""
            -- Reverse migration would recreate foreign key structure
            DROP TABLE documents_history;
            """
        ),
    ]