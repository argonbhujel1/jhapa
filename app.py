import os
from flask import Flask, send_from_directory, session
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from models import db, User, CartItem, SiteSetting
from routes import main_bp, shop_bp, admin_bp
from services.seed import seed_all

def ensure_schema(app):
    """Add missing columns for SQLite when models evolve (safe no-op if exists)."""
    from sqlalchemy import text, inspect
    with app.app_context():
        try:
            eng = db.engine
            insp = inspect(eng)
            if 'members' in insp.get_table_names():
                cols = {c['name'] for c in insp.get_columns('members')}
                alters = []
                if 'payment_status' not in cols:
                    alters.append("ALTER TABLE members ADD COLUMN payment_status VARCHAR(20) DEFAULT 'pending'")
                if 'payment_method' not in cols:
                    alters.append("ALTER TABLE members ADD COLUMN payment_method VARCHAR(50)")
                if 'payment_reference' not in cols:
                    alters.append("ALTER TABLE members ADD COLUMN payment_reference VARCHAR(100)")
                if 'payment_proof' not in cols:
                    alters.append("ALTER TABLE members ADD COLUMN payment_proof VARCHAR(255)")
                if 'free_tickets' not in cols:
                    alters.append("ALTER TABLE members ADD COLUMN free_tickets INTEGER DEFAULT 0")
                for sql in alters:
                    try:
                        with eng.begin() as conn:
                            conn.execute(text(sql))
                        print('Schema:', sql[:60])
                    except Exception as e:
                        print('Schema skip:', e)
            if 'membership_plans' in insp.get_table_names():
                cols = {c['name'] for c in insp.get_columns('membership_plans')}
                if 'free_tickets' not in cols:
                    try:
                        with eng.begin() as conn:
                            conn.execute(text("ALTER TABLE membership_plans ADD COLUMN free_tickets INTEGER DEFAULT 0"))
                        print('Schema: membership_plans.free_tickets')
                    except Exception as e:
                        print('Schema skip:', e)
            
            if 'contact_messages' in insp.get_table_names():
                cols = {c['name'] for c in insp.get_columns('contact_messages')}
                if 'admin_reply' not in cols:
                    try:
                        with eng.begin() as conn:
                            conn.execute(text("ALTER TABLE contact_messages ADD COLUMN admin_reply TEXT"))
                            conn.execute(text("ALTER TABLE contact_messages ADD COLUMN replied_at DATETIME"))
                        print('Schema: contact_messages.admin_reply')
                    except Exception as e:
                        print('Schema skip:', e)
            if 'products' in insp.get_table_names():
                cols = {c['name'] for c in insp.get_columns('products')}
                if 'is_limited_offer' not in cols:
                    try:
                        with eng.begin() as conn:
                            conn.execute(text("ALTER TABLE products ADD COLUMN is_limited_offer BOOLEAN DEFAULT 0"))
                        print('Schema: products.is_limited_offer')
                    except Exception as e:
                        print('Schema skip:', e)

            if 'leadership' in insp.get_table_names():
                cols = {c['name'] for c in insp.get_columns('leadership')}
                if 'section' not in cols:
                    try:
                        with eng.begin() as conn:
                            conn.execute(text("ALTER TABLE leadership ADD COLUMN section VARCHAR(50) DEFAULT 'Executive Board'"))
                        print('Schema: leadership.section')
                    except Exception as e:
                        print('Schema skip:', e)
        except Exception as e:
            print('ensure_schema:', e)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    def _safe_makedirs(path):
        """Vercel is read-only except /tmp — never crash on makedirs."""
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except OSError:
            return False

    # Prefer /tmp on serverless (VERCEL=1)
    is_serverless = bool(os.environ.get('VERCEL') or os.environ.get('AWS_LAMBDA_FUNCTION_NAME'))
    if is_serverless:
        upload_base = '/tmp/jhapa_uploads'
        _safe_makedirs(upload_base)
        app.config['UPLOAD_FOLDER'] = upload_base
    else:
        if not os.path.isabs(app.config['UPLOAD_FOLDER']):
            app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
        _safe_makedirs(os.path.join(app.root_path, 'instance'))
        _safe_makedirs(app.config['UPLOAD_FOLDER'])

    for sub in ['news', 'products', 'players', 'leadership', 'gallery', 'members', 'sponsors', 'branding']:
        _safe_makedirs(os.path.join(app.config['UPLOAD_FOLDER'], sub))

    db.init_app(app)
    migrate = Migrate(app, db)

    login_manager = LoginManager()
    login_manager.login_view = 'admin.login'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Global template context — available on ALL blueprints
    @app.context_processor
    def inject_globals():
        def get_cart_count():
            sid = session.get('cart_id')
            if not sid:
                return 0
            try:
                return CartItem.query.filter_by(session_id=sid).count()
            except Exception:
                return 0
        def get_setting(key, default=''):
            try:
                s = SiteSetting.query.filter_by(key=key).first()
                return s.value if s else default
            except Exception:
                return default
        return {
            'cart_count': get_cart_count(),
            'site_title': get_setting('site_title', 'Jhapa FC | Official Football Club'),
            'tagline': get_setting('site_tagline', 'ONE CLUB. ONE PRIDE.'),
            'club_logo': get_setting('club_logo', ''),
            'bam_logo': get_setting('bam_logo', ''),
            'bam_name': get_setting('bam_name', 'BAM Studio'),
            'bam_url': get_setting('bam_url', 'https://argan.com.np/'),
            'home_bg': get_setting('home_bg', ''),
            'loading_bg': get_setting('loading_bg', ''),
            'hero_card': get_setting('hero_card', ''),
            'about_card': get_setting('about_card', ''),
        }

    @app.template_filter('media_url')
    def media_url_filter(path):
        if not path:
            return ''
        if str(path).startswith('http://') or str(path).startswith('https://'):
            return path
        return '/uploads/' + str(path).lstrip('/')

    app.register_blueprint(main_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp)

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    with app.app_context():
        try:
            db.create_all()
            ensure_schema(app)
            if app.config.get('SEED_ON_START', True):
                seed_all(app)
        except Exception as e:
            print('DB init warning:', e)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
