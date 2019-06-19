set -e
python /app/src/OIPA/manage.py shell -c \
"from django.contrib.auth.models import User; \
User.objects.create_superuser('oipa', 'oipa@catalpa.io', 'oipa') \
if not User.objects.filter(username='oipa').exists() \
else 'Superuser already exists . . .'"