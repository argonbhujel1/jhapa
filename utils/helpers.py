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
            # Werkzeug FileStorage — pass stream or file object
            try:
                file.stream.seek(0)
            except Exception:
                pass
            result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type='image',
                overwrite=False,
            )
            print('Cloudinary OK:', (result.get('secure_url') or '')[:80])
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


def fetch_player_photo_url(player_name):
    """Find a public player photo URL.
    Order: TheSportsDB → DuckDuckGo images → Wikipedia.
    Query bias: "<name> Jhapa FC football" style searches.
    """
    if not player_name or not str(player_name).strip():
        return None
    import json
    import re
    import urllib.parse
    name = str(player_name).strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; JhapaFCBot/1.0; +https://jhapacityfc.vercel.app)',
        'Accept': 'application/json,text/html',
    }

    def _get(url, timeout=5):
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()

    def _get_json(url, timeout=5):
        return json.loads(_get(url, timeout).decode('utf-8', errors='ignore'))

    # --- 1 TheSportsDB ---
    try:
        data = _get_json(
            'https://www.thesportsdb.com/api/v1/json/3/searchplayers.php?p='
            + urllib.parse.quote(name)
        )
        for pl in (data.get('player') or []):
            sport = (pl.get('strSport') or '').lower()
            thumb = pl.get('strCutout') or pl.get('strThumb') or pl.get('strRender')
            if thumb and thumb.startswith('http') and (
                not sport or 'soccer' in sport or 'football' in sport
            ):
                return thumb
        if data.get('player'):
            t = data['player'][0].get('strCutout') or data['player'][0].get('strThumb')
            if t and t.startswith('http'):
                return t
    except Exception:
        pass

    # --- 2 DuckDuckGo image (unofficial, Google-like search) ---
    try:
        queries = [
            name + ' Jhapa FC football',
            name + ' played for Jhapa FC',
            name + ' Nepal footballer',
            name + ' footballer',
        ]
        for q in queries:
            # Step A: get vqd token
            html = _get(
                'https://duckduckgo.com/?q=' + urllib.parse.quote(q) + '&iax=images&ia=images',
                timeout=5,
            ).decode('utf-8', errors='ignore')
            m = re.search(r'vqd=([\'"])([^\'"]+)\1', html) or re.search(r'vqd=([^&]+)&', html)
            vqd = m.group(2) if m and m.lastindex >= 2 else (m.group(1) if m else None)
            if not vqd:
                continue
            api = (
                'https://duckduckgo.com/i.js?l=us-en&o=json&q='
                + urllib.parse.quote(q)
                + '&vqd=' + urllib.parse.quote(vqd)
                + '&f=,,,,,&p=1'
            )
            headers2 = dict(headers)
            headers2['Referer'] = 'https://duckduckgo.com/'
            req = urllib.request.Request(api, headers=headers2)
            with urllib.request.urlopen(req, timeout=5) as resp:
                idata = json.loads(resp.read().decode('utf-8', errors='ignore'))
            for img in (idata.get('results') or [])[:8]:
                url = img.get('image') or img.get('thumbnail')
                if not url or not url.startswith('http'):
                    continue
                low = url.lower()
                # skip obvious logos / tiny icons
                if any(x in low for x in ('.svg', 'logo', 'icon', 'sprite', 'favicon')):
                    continue
                return url
    except Exception:
        pass

    # --- 3 Wikipedia ---
    overrides = {
        'Anjan Bista': 'Anjan_Bista',
        'Laken Limbu': 'Laken_Limbu',
        'Alhaji Gero': 'Alhaji_Gero',
        'Stefan Cupic': 'Stefan_Čupić',
        'Stefan Čupić': 'Stefan_Čupić',
        'Lazar Arsic': 'Lazar_Arsić',
        'Lazar Arsić': 'Lazar_Arsić',
    }
    titles = []
    if name in overrides:
        titles.append(overrides[name])
    titles += [name.replace(' ', '_'), name.replace(' ', '_') + '_(footballer)']
    try:
        sdata = _get_json(
            'https://en.wikipedia.org/w/api.php?action=query&list=search'
            '&srlimit=3&format=json&srsearch=' + urllib.parse.quote(name + ' football Nepal')
        )
        for hit in (sdata.get('query') or {}).get('search') or []:
            if hit.get('title'):
                titles.append(hit['title'].replace(' ', '_'))
    except Exception:
        pass
    seen = set()
    for title in titles:
        if not title or title in seen:
            continue
        seen.add(title)
        try:
            data = _get_json(
                'https://en.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(title)
            )
            if data.get('type') == 'disambiguation':
                continue
            thumb = (data.get('thumbnail') or {}).get('source') or (data.get('originalimage') or {}).get('source')
            if thumb:
                return thumb.replace('/60px-', '/300px-').replace('/40px-', '/300px-')
        except Exception:
            continue
    return None


def ensure_player_photos(players, only_missing=True):
    """Fill missing player.photo from Wikipedia when possible."""
    updated = 0
    for pl in players:
        if only_missing and pl.photo:
            continue
        url = fetch_player_photo_url(pl.name)
        if url:
            pl.photo = url
            updated += 1
    return updated
