from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


MANAGER_PERMISSIONS = [
    "add_asset", "change_asset", "delete_asset", "view_asset", "change_asset_details",
    "add_category", "change_category", "delete_category", "view_category",
    "add_location", "change_location", "delete_location", "view_location",
    "view_assethistory",
]

AUTHORIZED_USER_PERMISSIONS = [
    "view_asset", "change_asset",
    "view_category", "view_location",
    "view_assethistory",
]


ROLES = {
    "Manager" : MANAGER_PERMISSIONS,
    "Authorized user" : AUTHORIZED_USER_PERMISSIONS,
}



class Command(BaseCommand):
    help = "Create or update the Manager and Authorized user groups with the appropriate permissions."

    def handle(self, *args, **options):
        for group_name, codenames in ROLES.items():
            group, created = Group.objects.get_or_create(name=group_name)
            permissions = Permission.objects.filter(
                content_type__app_label="assets", codename__in=codenames
            )
            
            group.permissions.set(permissions)
            self.stdout.write(
                f"{'Created' if created else 'Updated'} group '{group_name}' "
                f"with {permissions.count()} permissions."
            )
        