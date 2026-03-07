#!/bin/bash
set -e

echo "=== Starting entrypoint script ==="

echo "Running migrations..."
python manage.py migrate

# Check if users table is empty and seed if needed
echo "Checking if users table is empty..."
USER_COUNT=$(python manage.py shell -c "
from django.contrib.auth import get_user_model
print(get_user_model().objects.count())
" 2>/dev/null | tail -1)

echo "Current user count: $USER_COUNT"

if [ "$USER_COUNT" = "0" ] || [ -z "$USER_COUNT" ]; then
    echo "Users table is empty. Seeding initial data..."
    
    if python manage.py seed_data ; then
        echo "✓ Seed data completed successfully"
    else
        echo "✗ Seed data failed with exit code $?"
        exit 1
    fi

    # Verify data was seeded
    NEW_USER_COUNT=$(python manage.py shell -c "
from django.contrib.auth import get_user_model
print(get_user_model().objects.count())
" 2>/dev/null | tail -1)
    echo "User count after seeding: $NEW_USER_COUNT"
else
    echo "Users table already has data ($USER_COUNT users). Skipping seed."
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "=== Starting Gunicorn ==="
exec python -m gunicorn backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
