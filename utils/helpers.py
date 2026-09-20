import os
import uuid
import re
import urllib.request
from datetime import datetime
from flask import current_app


def allowed_file(filename):
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in current_app.config.get(
        'ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    )


def cloudinary_enabled():
    return bool(
        current_app.config.get('CLOUDINARY_CLOUD_NAME')
        and current_app.config.get('CLOUDINARY_API_KEY')
        and current_app.config.get('CLOUDINARY_API_SECRET')
    )


def _cloudinary_config():
    import cloudinary
    cloudinary.config(
        cloud_name=current_app.config['CLOUDINARY_CLOUD_NAME'],
        api_key=current_app.config['CLOUDINARY_API_KEY'],
        api_secret=current_app.config['CLOUDINARY_API_SECRET'],
        secure=True,
    )


def _upload_root():
    folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
    if not os.path.isabs(folder):
        folder = os.path.join(current_app.root_path, folder)
    try:
        os.makedirs(folder, exist_ok=True)
    except OSError:
        folder = '/tmp/jhapa_uploads'
        os.makedirs(folder, exist_ok=True)
    return folder


def save_upload(file, subfolder=''):
    """Save to Cloudinary when configured, else local disk. Returns URL or relative path."""
    if not file or not getattr(file, 'filename', None):
        return None
    if not allowed_file(file.filename):
        return None

    if cloudinary_enabled():
        try:
            _cloudinary_config()
            import cloudinary.uploader
            folder = current_app.config.get('CLOUDINARY_FOLDER', 'jhapa-fc')
            if subfolder:
                folder = f'{folder}/{subfolder}'
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type='image',
                overwrite=False,
            )
            return result.get('secure_url') or result.get('url')
        except Exception as e:
            print('Cloudinary upload error:', e)
            # fall through to local if possible

    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f'{uuid.uuid4().hex}.{ext}'
        folder = os.path.join(_upload_root(), subfolder) if subfolder else _upload_root()
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        file.save(path)
        rel = os.path.join(subfolder, filename).replace('\\', '/') if subfolder else filename
        return rel.replace('\\', '/')
    except Exception as e:
        print('Local upload error:', e)
        return None


def save_image_from_url(url, subfolder=''):
    if not url or not url.strip().startswith(('http://', 'https://')):
        return None
    url = url.strip()
    # Already a Cloudinary / external CDN URL — store as-is
    if 'res.cloudinary.com' in url or cloudinary_enabled() is False:
        if cloudinary_enabled() and 'res.cloudinary.com' not in url:
            try:
                _cloudinary_config()
                import cloudinary.uploader
                folder = current_app.config.get('CLOUDINARY_FOLDER', 'jhapa-fc')
                if subfolder:
                    folder = f'{folder}/{subfolder}'
                result = cloudinary.uploader.upload(url, folder=folder, resource_type='image')
                return result.get('secure_url') or result.get('url')
            except Exception as e:
                print('Cloudinary URL upload error:', e)
                return url
        return url

    try:
        _cloudinary_config()
        import cloudinary.uploader
        folder = current_app.config.get('CLOUDINARY_FOLDER', 'jhapa-fc')
        if subfolder:
            folder = f'{folder}/{subfolder}'
        result = cloudinary.uploader.upload(url, folder=folder, resource_type='image')
        return result.get('secure_url') or result.get('url')
    except Exception as e:
        print('save_image_from_url cloudinary:', e)

    # Local fallback
    try:
        ext = 'jpg'
        lower = url.lower().split('?')[0]
        for e in ('png', 'jpg', 'jpeg', 'webp', 'gif'):
            if lower.endswith('.' + e):
                ext = 'jpg' if e == 'jpeg' else e
                break
        filename = f'{uuid.uuid4().hex}.{ext}'
        folder = os.path.join(_upload_root(), subfolder) if subfolder else _upload_root()
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        req = urllib.request.Request(url, headers={'User-Agent': 'JhapaFC/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if len(data) < 100:
            return None
        with open(path, 'wb') as f:
            f.write(data)
        rel = os.path.join(subfolder, filename).replace('\\', '/') if subfolder else filename
        return rel.replace('\\', '/')
    except Exception as e:
        print('save_image_from_url local error:', e)
        return url if url.startswith('http') else None


def resolve_image_input(files_key, url_field, form, files, subfolder=''):
    if files_key in files and files[files_key].filename:
        path = save_upload(files[files_key], subfolder)
        if path:
            return path
    url = (form.get(url_field) or '').strip()
    if url:
        return save_image_from_url(url, subfolder) or (url if url.startswith('http') else None)
    return None


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text[:200]


def generate_order_number():
    return f"JFC{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"


def generate_membership_number():
    return f"JFC-M{datetime.utcnow().strftime('%y%m')}{uuid.uuid4().hex[:6].upper()}"


def format_currency(amount):
    try:
        return f"Rs. {float(amount):,.0f}"
    except Exception:
        return 'Rs. 0'
