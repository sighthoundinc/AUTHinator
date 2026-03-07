"""
"""Management command to populate Authinator with demo authentication data.

Creates demo user accounts with credentials only.
Company assignments and roles are managed in USERinator.
Passwords: 'admin' for admins, 'manager' for managers, 'member' for members.
Idempotent — safe to run multiple times.
"""
from django.core.management.base import BaseCommand
from users.models import User

# Demo users - credentials only, no company assignments
# Company/role data is managed in USERinator
USERS = [
    # (user_id, username, email, password, is_admin)
    (1, 'admin', 'admin@example.com', 'admin', True),
    (2, 'alice.admin', 'alice@example.com', 'admin', True),
    
    # Acme Corporation
    (101, 'bob.manager', 'bob@acme.example.com', 'manager', False),
    (102, 'carol.member', 'carol@acme.example.com', 'member', False),
    (103, 'dave.member', 'dave@acme.example.com', 'member', False),
    
    # Globex Industries
    (104, 'frank.manager', 'frank@globex.example.com', 'manager', False),
    (105, 'grace.member', 'grace@globex.example.com', 'member', False),
    
    # Initech LLC
    (106, 'henry.manager', 'henry@initech.example.com', 'manager', False),
    (107, 'iris.member', 'iris@initech.example.com', 'member', False),
    
    # Wayne Enterprises
    (108, 'jack.manager', 'jack@wayne.example.com', 'manager', False),
    (109, 'kate.member', 'kate@wayne.example.com', 'member', False),
    (110, 'leo.member', 'leo@wayne.example.com', 'member', False),
]


class Command(BaseCommand):
    help = 'Populate Authinator with demo user credentials'

    def handle(self, *args, **options):
        self.stdout.write('🔑 Seeding AUTHinator demo users...')

        # Create demo users (credentials only, no company assignment)
        for user_id, username, email, password, is_admin in USERS:
            auth_role = 'ADMIN' if is_admin else 'USER'
            
            # Check if user exists
            try:
                user = User.objects.get(username=username)
                # Update existing user
                user.email = email
                user.role = auth_role
                user.is_verified = True
                user.is_staff = is_admin
                user.set_password(password)
                user.save()
                self.stdout.write(f'  User: {username} (updated)')
            except User.DoesNotExist:
                # Create new user
                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    role=auth_role,
                    is_verified=True,
                    is_staff=is_admin,
                )
                user.set_password(password)
                user.save()
                self.stdout.write(f'  User: {user.username} (created)')

        self.stdout.write(self.style.SUCCESS('✅ AUTHinator: 12 users seeded'))
        self.stdout.write('   Passwords: admin/manager/member based on role')
        self.stdout.write('   Company assignments managed in USERinator')
