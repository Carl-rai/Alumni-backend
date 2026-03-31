# MIGRATION INSTRUCTIONS

After making the model changes, you need to create and apply migrations:

## Step 1: Create Migration
Run this command in your backend directory:
```bash
python manage.py makemigrations
```

## Step 2: Apply Migration
Run this command to apply the migration to your database:
```bash
python manage.py migrate
```

## Step 3: Update Existing Users (Optional)
If you have existing users in the database, you may want to set their role to 'user' by default.
You can do this through Django admin or by running this in Django shell:

```bash
python manage.py shell
```

Then in the shell:
```python
from user.models import CustomUser
CustomUser.objects.filter(role__isnull=True).update(role='user')
# Or if role is empty string
CustomUser.objects.filter(role='').update(role='user')
```

## Step 4: Create Admin User (if needed)
To create an admin user from command line:
```bash
python manage.py createsuperuser
```

Then update the role in Django admin panel to 'admin'.

## Notes:
- The role field has been added with choices: 'user', 'staff', 'admin'
- Default role is 'user'
- Admin users will have is_staff=True and is_superuser=True
- Staff users will have is_staff=True
- Regular users will have is_staff=False
