from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from models import (
    db, User, Match, News, Product, ProductCategory, ProductVariant,
    MembershipPlan, Member, ContactMessage, Player, Leadership, GalleryImage,
    Sponsor, Order, ClubInfo, SiteSetting, LeagueStanding, TopPerformer
)
from utils.helpers import slugify, save_upload, save_image_from_url, resolve_image_input
from datetime import datetime
from functools import wraps
from . import admin_bp

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ('admin', 'editor'):
            flash('Please log in as admin.', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            flash('Welcome back!', 'success')
            return redirect(url_for('admin.dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_required
def dashboard():
    stats = {
        'orders': Order.query.count(),
        'revenue': db.session.query(db.func.sum(Order.total)).scalar() or 0,
        'products': Product.query.count(),
        'members': Member.query.count(),
        'news': News.query.count(),
        'matches': Match.query.count(),
        'messages': ContactMessage.query.filter_by(is_read=False).count(),
        'players': Player.query.count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)

# ---------- News CRUD ----------
@admin_bp.route('/news')
@admin_required
def news_list():
    items = News.query.order_by(News.publish_date.desc()).all()
    return render_template('admin/news_list.html', items=items)

@admin_bp.route('/news/new', methods=['GET', 'POST'])
@admin_bp.route('/news/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def news_edit(id=None):
    item = News.query.get(id) if id else None
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Title required.', 'error')
            return render_template('admin/news_form.html', item=item)
        if not item:
            item = News(slug=slugify(title))
            db.session.add(item)
        item.title = title
        item.slug = slugify(title)
        item.category = request.form.get('category', 'Club News')
        item.excerpt = request.form.get('excerpt', '')
        item.content = request.form.get('content', '')
        item.author = request.form.get('author', 'Jhapa FC Media')
        item.status = request.form.get('status', 'published')
        item.is_demo = False
        path = resolve_image_input('featured_image', 'image_url', request.form, request.files, 'news')
        if path:
            item.featured_image = path
        db.session.commit()
        flash('News saved.', 'success')
        return redirect(url_for('admin.news_list'))
    return render_template('admin/news_form.html', item=item)

@admin_bp.route('/news/<int:id>/delete', methods=['POST'])
@admin_required
def news_delete(id):
    item = News.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('admin.news_list'))

# ---------- Matches CRUD ----------
@admin_bp.route('/matches')
@admin_required
def matches_list():
    items = Match.query.order_by(Match.match_date.desc()).all()
    return render_template('admin/matches_list.html', items=items)

@admin_bp.route('/matches/new', methods=['GET', 'POST'])
@admin_bp.route('/matches/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def match_edit(id=None):
    item = Match.query.get(id) if id else None
    if request.method == 'POST':
        if not item:
            item = Match(opponent='')
            db.session.add(item)
        item.opponent = request.form.get('opponent', '').strip()
        item.competition = request.form.get('competition', 'Nepal Super League')
        item.venue = request.form.get('venue', '')
        dt_str = request.form.get('match_date')
        if dt_str:
            item.match_date = datetime.fromisoformat(dt_str)
        item.is_home = request.form.get('is_home') == 'on'
        item.status = request.form.get('status', 'upcoming')
        hs = request.form.get('home_score')
        as_ = request.form.get('away_score')
        item.home_score = int(hs) if hs not in (None, '') else None
        item.away_score = int(as_) if as_ not in (None, '') else None
        item.is_demo = False
        item.is_published = request.form.get('is_published') == 'on'
        db.session.commit()
        flash('Match saved.', 'success')
        return redirect(url_for('admin.matches_list'))
    return render_template('admin/match_form.html', item=item)

@admin_bp.route('/matches/<int:id>/delete', methods=['POST'])
@admin_required
def match_delete(id):
    item = Match.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('admin.matches_list'))

# ---------- Products ----------
@admin_bp.route('/products')
@admin_required
def products_list():
    items = Product.query.order_by(Product.name).all()
    return render_template('admin/products_list.html', items=items)

@admin_bp.route('/products/new', methods=['GET', 'POST'])
@admin_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def product_edit(id=None):
    item = Product.query.get(id) if id else None
    categories = ProductCategory.query.all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Name required.', 'error')
            return render_template('admin/product_form.html', item=item, categories=categories)
        if not item:
            item = Product(name=name, slug=slugify(name), price=0)
            db.session.add(item)
        item.name = name
        item.slug = slugify(name)
        item.description = request.form.get('description', '')
        item.price = request.form.get('price', 0)
        cp = request.form.get('compare_price')
        item.compare_price = float(cp) if cp not in (None, '') else None
        item.stock = request.form.get('stock', 0, type=int)
        item.category_id = request.form.get('category_id', type=int) or None
        item.is_active = request.form.get('is_active') == 'on'
        item.is_featured = request.form.get('is_featured') == 'on'
        item.is_limited_offer = request.form.get('is_limited_offer') == 'on'
        item.is_demo = False
        path = resolve_image_input('image', 'image_url', request.form, request.files, 'products')
        if path:
            item.image = path
        db.session.commit()
        flash('Product saved.', 'success')
        return redirect(url_for('admin.products_list'))
    return render_template('admin/product_form.html', item=item, categories=categories)

@admin_bp.route('/products/<int:id>/delete', methods=['POST'])
@admin_required
def product_delete(id):
    item = Product.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('admin.products_list'))

# ---------- Players (placeholder ready) ----------
@admin_bp.route('/players')
@admin_required
def players_list():
    items = Player.query.order_by(Player.order).all()
    return render_template('admin/players_list.html', items=items)

@admin_bp.route('/players/new', methods=['GET', 'POST'])
@admin_bp.route('/players/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def player_edit(id=None):
    item = Player.query.get(id) if id else None
    if request.method == 'POST':
        if not item:
            item = Player()
            db.session.add(item)
        item.name = request.form.get('name', '').strip()
        item.number = request.form.get('number', type=int)
        item.position = request.form.get('position', '')
        item.nationality = request.form.get('nationality', '')
        item.height = request.form.get('height', '')
        item.preferred_foot = request.form.get('preferred_foot', '')
        item.appearances = request.form.get('appearances', 0, type=int)
        item.goals = request.form.get('goals', 0, type=int)
        item.assists = request.form.get('assists', 0, type=int)
        item.career = request.form.get('career', '')
        item.is_published = request.form.get('is_published') == 'on'
        item.order = request.form.get('order', 0, type=int)
        dob = request.form.get('date_of_birth')
        if dob:
            item.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
        path = resolve_image_input('photo', 'photo_url', request.form, request.files, 'players')
        if path:
            item.photo = path
        db.session.commit()
        flash('Player saved. Publish when official data is ready.', 'success')
        return redirect(url_for('admin.players_list'))
    return render_template('admin/player_form.html', item=item)

# ---------- Leadership ----------
@admin_bp.route('/leadership')
@admin_required
def leadership_list():
    items = Leadership.query.order_by(Leadership.order).all()
    return render_template('admin/leadership_list.html', items=items)

@admin_bp.route('/leadership/new', methods=['GET', 'POST'])
@admin_bp.route('/leadership/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def leadership_edit(id=None):
    item = Leadership.query.get(id) if id else None
    if request.method == 'POST':
        if not item:
            item = Leadership(name='', position='')
            db.session.add(item)
        item.name = request.form.get('name', '').strip()
        item.position = request.form.get('position', '').strip()
        item.section = request.form.get('section', 'Executive Board')
        item.bio = request.form.get('bio', '')
        item.order = request.form.get('order', 0, type=int)
        item.is_published = request.form.get('is_published') == 'on'
        path = resolve_image_input('photo', 'photo_url', request.form, request.files, 'leadership')
        if path:
            item.photo = path
        db.session.commit()
        flash('Saved. Publish only when official.', 'success')
        return redirect(url_for('admin.leadership_list'))
    return render_template('admin/leadership_form.html', item=item)

# ---------- Orders ----------
@admin_bp.route('/orders')
@admin_required
def orders_list():
    items = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders_list.html', items=items)

@admin_bp.route('/orders/<int:id>')
@admin_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:id>/status', methods=['POST'])
@admin_required
def order_status(id):
    order = Order.query.get_or_404(id)
    old_status = order.status
    new_status = request.form.get('status', order.status)
    order.status = new_status
    # Reduce stock when moving TO Confirmed (once)
    if new_status == 'Confirmed' and old_status != 'Confirmed':
        for oi in order.items:
            if oi.product_id:
                prod = Product.query.get(oi.product_id)
                if prod and prod.stock is not None:
                    prod.stock = max(0, int(prod.stock) - int(oi.quantity or 1))
        flash('Order confirmed. Product stock updated.', 'success')
    else:
        flash('Status updated.', 'success')
    db.session.commit()
    return redirect(url_for('admin.order_detail', id=id))

# ---------- Members ----------
@admin_bp.route('/members')
@admin_required
def members_list():
    items = Member.query.order_by(Member.joined_at.desc()).all()
    return render_template('admin/members_list.html', items=items)

# ---------- Messages ----------
@admin_bp.route('/messages')
@admin_required
def messages_list():
    items = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages_list.html', items=items)

@admin_bp.route('/messages/<int:id>')
@admin_required
def message_detail(id):
    msg = ContactMessage.query.get_or_404(id)
    return render_template('admin/message_detail.html', msg=msg)

@admin_bp.route('/messages/<int:id>/read', methods=['POST'])
@admin_required
def message_read(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    flash('Marked as read.', 'success')
    return redirect(url_for('admin.message_detail', id=id))

@admin_bp.route('/messages/<int:id>/unread', methods=['POST'])
@admin_required
def message_unread(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.is_read = False
    db.session.commit()
    flash('Marked as unread.', 'success')
    return redirect(url_for('admin.messages_list'))

@admin_bp.route('/messages/<int:id>/reply', methods=['POST'])
@admin_required
def message_reply(id):
    msg = ContactMessage.query.get_or_404(id)
    reply = request.form.get('admin_reply', '').strip()
    if reply:
        msg.admin_reply = reply
        msg.is_read = True
        from datetime import datetime
        msg.replied_at = datetime.utcnow()
        db.session.commit()
        flash('Reply saved. (Email sending can be connected later.)', 'success')
    return redirect(url_for('admin.message_detail', id=id))

@admin_bp.route('/messages/<int:id>/delete', methods=['POST'])
@admin_required
def message_delete(id):
    msg = ContactMessage.query.get_or_404(id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin.messages_list'))

# ---------- Gallery ----------
@admin_bp.route('/gallery')
@admin_required
def gallery_list():
    items = GalleryImage.query.order_by(GalleryImage.created_at.desc()).all()
    return render_template('admin/gallery_list.html', items=items)

@admin_bp.route('/gallery/new', methods=['GET', 'POST'])
@admin_required
def gallery_new():
    if request.method == 'POST':
        path = resolve_image_input('image', 'image_url', request.form, request.files, 'gallery')
        if not path:
            flash('Upload failed. Use PNG/JPG/WEBP/GIF file or a direct image URL.', 'error')
            return render_template('admin/gallery_form.html')
        if path:
            img = GalleryImage(
                title=request.form.get('title', ''),
                category=request.form.get('category', 'Matchday'),
                image=path,
                caption=request.form.get('caption', ''),
                is_demo=False,
                is_published=True
            )
            db.session.add(img)
            db.session.commit()
            flash('Image added.', 'success')
            return redirect(url_for('admin.gallery_list'))
    return render_template('admin/gallery_form.html', item=None)

@admin_bp.route('/gallery/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def gallery_edit(id):
    item = GalleryImage.query.get_or_404(id)
    if request.method == 'POST':
        item.title = request.form.get('title', item.title)
        item.category = request.form.get('category', item.category)
        item.caption = request.form.get('caption', item.caption)
        item.is_published = request.form.get('is_published') == 'on'
        path = resolve_image_input('image', 'image_url', request.form, request.files, 'gallery')
        if path:
            item.image = path
        db.session.commit()
        flash('Gallery image updated.', 'success')
        return redirect(url_for('admin.gallery_list'))
    return render_template('admin/gallery_form.html', item=item)

@admin_bp.route('/gallery/<int:id>/delete', methods=['POST'])
@admin_required
def gallery_delete(id):
    item = GalleryImage.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Image deleted.', 'success')
    return redirect(url_for('admin.gallery_list'))

# ---------- Settings ----------
@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        for key in ['site_title', 'site_tagline', 'contact_email', 'contact_phone', 'contact_address',
                    'facebook', 'instagram', 'twitter', 'youtube', 'bam_name', 'bam_url']:
            val = request.form.get(key)
            if val is not None:
                s = SiteSetting.query.filter_by(key=key).first()
                if s:
                    s.value = val
                else:
                    db.session.add(SiteSetting(key=key, value=val))
        path = resolve_image_input('club_logo', 'club_logo_url', request.form, request.files, 'branding')
        if path:
            s = SiteSetting.query.filter_by(key='club_logo').first()
            if s:
                s.value = path
            else:
                db.session.add(SiteSetting(key='club_logo', value=path))
        bam_path = resolve_image_input('bam_logo', 'bam_logo_url', request.form, request.files, 'branding')
        if bam_path:
            s = SiteSetting.query.filter_by(key='bam_logo').first()
            if s:
                s.value = bam_path
            else:
                db.session.add(SiteSetting(key='bam_logo', value=bam_path))
        for field, url_field, key in [
            ('home_bg', 'home_bg_url', 'home_bg'),
            ('loading_bg', 'loading_bg_url', 'loading_bg'),
            ('hero_card', 'hero_card_url', 'hero_card'),
            ('about_card', 'about_card_url', 'about_card'),
        ]:
            path = resolve_image_input(field, url_field, request.form, request.files, 'branding')
            if path:
                s = SiteSetting.query.filter_by(key=key).first()
                if s:
                    s.value = path
                else:
                    db.session.add(SiteSetting(key=key, value=path))
        db.session.commit()
        flash('Settings saved.', 'success')
        return redirect(url_for('admin.settings'))
    settings_dict = {s.key: s.value for s in SiteSetting.query.all()}
    return render_template('admin/settings.html', settings=settings_dict)


# ---------- Sponsors ----------
@admin_bp.route('/sponsors')
@admin_required
def sponsors_list():
    items = Sponsor.query.order_by(Sponsor.order, Sponsor.id).all()
    return render_template('admin/sponsors_list.html', items=items)

@admin_bp.route('/sponsors/new', methods=['GET', 'POST'])
@admin_bp.route('/sponsors/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def sponsor_edit(id=None):
    item = Sponsor.query.get(id) if id else None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Name required.', 'error')
            return render_template('admin/sponsor_form.html', item=item)
        if not item:
            item = Sponsor(name=name)
            db.session.add(item)
        item.name = name
        item.website = request.form.get('website', '').strip() or None
        item.category = request.form.get('category', 'Official Partner')
        item.order = request.form.get('order', 0, type=int) or 0
        item.is_published = request.form.get('is_published') == 'on'
        path = resolve_image_input('logo', 'logo_url', request.form, request.files, 'sponsors')
        if path:
            item.logo = path
        db.session.commit()
        flash('Sponsor saved.', 'success')
        return redirect(url_for('admin.sponsors_list'))
    return render_template('admin/sponsor_form.html', item=item)

@admin_bp.route('/sponsors/<int:id>/delete', methods=['POST'])
@admin_required
def sponsor_delete(id):
    item = Sponsor.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Sponsor deleted.', 'success')
    return redirect(url_for('admin.sponsors_list'))


@admin_bp.route('/members/<int:id>/verify', methods=['POST'])
@admin_required
def member_verify(id):
    member = Member.query.get_or_404(id)
    member.payment_status = 'verified'
    member.status = 'active'
    if member.plan and member.plan.free_tickets:
        member.free_tickets = member.plan.free_tickets
    db.session.commit()
    flash(f'Payment verified for {member.full_name}. Membership active.', 'success')
    return redirect(url_for('admin.members_list'))


# ---------- League Table ----------
@admin_bp.route('/league')
@admin_required
def league_list():
    items = LeagueStanding.query.order_by(LeagueStanding.position).all()
    return render_template('admin/league_list.html', items=items)

@admin_bp.route('/league/new', methods=['GET', 'POST'])
@admin_bp.route('/league/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def league_edit(id=None):
    item = LeagueStanding.query.get(id) if id else None
    if request.method == 'POST':
        if not item:
            item = LeagueStanding(team_name='')
            db.session.add(item)
        item.team_name = request.form.get('team_name', '').strip()
        item.position = request.form.get('position', 1, type=int)
        item.played = request.form.get('played', 0, type=int)
        item.won = request.form.get('won', 0, type=int)
        item.drawn = request.form.get('drawn', 0, type=int)
        item.lost = request.form.get('lost', 0, type=int)
        item.goals_for = request.form.get('goals_for', 0, type=int)
        item.goals_against = request.form.get('goals_against', 0, type=int)
        item.points = request.form.get('points', 0, type=int)
        item.is_jhapa = request.form.get('is_jhapa') == 'on'
        item.season = request.form.get('season', '2025/26')
        item.is_published = request.form.get('is_published') == 'on'
        db.session.commit()
        flash('League row saved.', 'success')
        return redirect(url_for('admin.league_list'))
    return render_template('admin/league_form.html', item=item)

@admin_bp.route('/league/<int:id>/delete', methods=['POST'])
@admin_required
def league_delete(id):
    item = LeagueStanding.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('admin.league_list'))

# ---------- Top Performers ----------
@admin_bp.route('/performers')
@admin_required
def performers_list():
    items = TopPerformer.query.order_by(TopPerformer.order, TopPerformer.id).all()
    return render_template('admin/performers_list.html', items=items)

@admin_bp.route('/performers/new', methods=['GET', 'POST'])
@admin_bp.route('/performers/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def performer_edit(id=None):
    item = TopPerformer.query.get(id) if id else None
    if request.method == 'POST':
        if not item:
            item = TopPerformer(name='')
            db.session.add(item)
        item.name = request.form.get('name', '').strip()
        item.category = request.form.get('category', 'Top Scorer')
        item.value = request.form.get('value', 0, type=int)
        item.team = request.form.get('team', 'Jhapa FC')
        item.order = request.form.get('order', 0, type=int)
        item.season = request.form.get('season', '2025/26')
        item.is_published = request.form.get('is_published') == 'on'
        path = resolve_image_input('photo', 'photo_url', request.form, request.files, 'players')
        if path:
            item.photo = path
        db.session.commit()
        flash('Performer saved.', 'success')
        return redirect(url_for('admin.performers_list'))
    return render_template('admin/performer_form.html', item=item)

@admin_bp.route('/performers/<int:id>/delete', methods=['POST'])
@admin_required
def performer_delete(id):
    item = TopPerformer.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Deleted.', 'success')
    return redirect(url_for('admin.performers_list'))
