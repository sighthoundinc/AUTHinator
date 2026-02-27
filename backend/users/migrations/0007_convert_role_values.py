"""
Data migration to convert legacy role values to simplified ADMIN/USER roles.

SYSTEM_ADMIN, CUSTOMER_ADMIN → ADMIN
CUSTOMER_USER, CUSTOMER_READONLY → USER
"""
from django.db import migrations


def convert_roles_forward(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(role__in=['SYSTEM_ADMIN', 'CUSTOMER_ADMIN']).update(role='ADMIN')
    User.objects.filter(role__in=['CUSTOMER_USER', 'CUSTOMER_READONLY']).update(role='USER')


def convert_roles_backward(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(role='ADMIN').update(role='SYSTEM_ADMIN')
    User.objects.filter(role='USER').update(role='CUSTOMER_USER')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_simplify_roles_to_admin_user'),
    ]

    operations = [
        migrations.RunPython(convert_roles_forward, convert_roles_backward),
    ]
