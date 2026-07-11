import sys
sys.path.append('backend')
from app.core.config import settings
import os

print(f'BASE_DIR: {settings.BASE_DIR}')
print(f'DATABASE_URL: {settings.DATABASE_URL}')
print(f'Env file: {settings.BASE_DIR / ".env"}')

# Resolve the actual path
url = settings.DATABASE_URL
if url.startswith('sqlite:///'):
    path = url[10:]  # Remove 'sqlite:///'
    if not os.path.isabs(path):
        path = os.path.join(settings.BASE_DIR, path)
    print(f'Resolved DB path: {os.path.abspath(path)}')
    print(f'Exists: {os.path.exists(os.path.abspath(path))}')
