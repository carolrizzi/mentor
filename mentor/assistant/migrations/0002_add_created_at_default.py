from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("assistant", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            """
            ALTER TABLE chat_message
            ALTER COLUMN created_at
            SET DEFAULT now();
            """,
            reverse_sql="""
            ALTER TABLE chat_message
            ALTER COLUMN created_at
            DROP DEFAULT;
            """,
        )
    ]
