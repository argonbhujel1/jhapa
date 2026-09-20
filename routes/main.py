from flask import render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_required, current_user
from models import (
    db, Match, News, Product, Player, Leadership, GalleryImage, ClubInfo,
    MembershipPlan, Member, ContactMessage, Sponsor, SiteSetting, CartItem, LeagueStanding, TopPerformer
)
from utils.helpers import generate_membership_number, slugify
from datetime import datetime, timedelta
from . import main_bp
import uuid

def get_setting(key, default=''):
    s = SiteSetting.query.filter_by(key=key).first()
    return s.value if s else default

@main_bp.route('/')
def index():
    next_match = Match.query.filter(
        Match.status == 'upcoming',
        Match.is_published == True
    ).order_by(Match.match_date.asc()).first()

    recent_results = Match.query.filter(
        Match.status == 'finished',
        Match.is_published == True
    ).order_by(Match.match_date.desc()).limit(4).all()

    upcoming = Match.query.filter(
        Match.status == 'upcoming',
        Match.is_published == True
    ).order_by(Match.match_date.asc()).limit(4).all()

    latest_news = News.query.filter_by(status='published').order_by(News.publish_date.desc()).limit(4).all()

    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(4).all()
    if not featured_products:
        featured_products = Product.query.filter_by(is_active=True).order_by(Product.id.desc()).limit(4).all()

    about = ClubInfo.query.filter_by(key='about_story').first()
    vision = ClubInfo.query.filter_by(key='vision').first()
    mission = ClubInfo.query.filter_by(key='mission').first()
    values = ClubInfo.query.filter_by(key='values').first()

    sponsors = Sponsor.query.filter(
        Sponsor.is_published == True,
        Sponsor.category != 'Web & Technology Partner'
    ).order_by(Sponsor.order, Sponsor.id).all()

    standings = LeagueStanding.query.filter_by(is_published=True).order_by(LeagueStanding.position).limit(10).all()
    performers = TopPerformer.query.filter_by(is_published=True).order_by(TopPerformer.order, TopPerformer.id).limit(6).all()
    squad_preview = Player.query.filter_by(is_published=True).order_by(Player.order, Player.number).limit(8).all()

    return render_template('index.html',
        next_match=next_match,
        recent_results=recent_results,
        upcoming=upcoming,
        latest_news=latest_news,
        featured_products=featured_products,
        about=about,
        vision=vision,
        mission=mission,
        values=values,
        sponsors=sponsors,
        standings=standings,
        performers=performers,
        squad_preview=squad_preview
    )

@main_bp.route('/club')
def club():
    about = ClubInfo.query.filter_by(key='about_story').first()
    vision = ClubInfo.query.filter_by(key='vision').first()
    mission = ClubInfo.query.filter_by(key='mission').first()
    values = ClubInfo.query.filter_by(key='values').first()
    established = ClubInfo.query.filter_by(key='established').first()
    return render_template('club.html', about=about, vision=vision, mission=mission, values=values, established=established)

@main_bp.route('/leadership/<int:id>')
def leadership_detail(id):
    person = Leadership.query.get_or_404(id)
    if not person.is_published:
        flash('Official information coming soon.', 'info')
        return redirect(url_for('main.leadership'))
    return render_template('leadership_detail.html', person=person)

@main_bp.route('/leadership')
def leadership():
    section = request.args.get('section')
    q = Leadership.query.filter_by(is_published=True)
    if section and section != 'All':
        q = q.filter_by(section=section)
    leaders = q.order_by(Leadership.order, Leadership.id).all()
    sections = ['All', 'Committee', 'Executive Board', 'Coordination & PR', 'Advisory Council', 'Technical Team']
    return render_template('leadership.html', leaders=leaders, sections=sections, current_section=section or 'All')

@main_bp.route('/squad')
def squad():
    players = Player.query.filter_by(is_published=True).order_by(Player.order, Player.number).all()
    return render_template('squad.html', players=players)

@main_bp.route('/player/<int:id>')
def player(id):
    p = Player.query.get_or_404(id)
    if not p.is_published:
        flash('Player profile not available yet.', 'info')
        return redirect(url_for('main.squad'))
    return render_template('player.html', player=p)

@main_bp.route('/matches')
def matches():
    tab = request.args.get('tab', 'upcoming')
    upcoming = Match.query.filter_by(status='upcoming', is_published=True).order_by(Match.match_date.asc()).all()
    results = Match.query.filter_by(status='finished', is_published=True).order_by(Match.match_date.desc()).all()
    standings = LeagueStanding.query.filter_by(is_published=True).order_by(LeagueStanding.position).all()
    performers = TopPerformer.query.filter_by(is_published=True).order_by(TopPerformer.order, TopPerformer.id).all()
    return render_template('matches.html', upcoming=upcoming, results=results, tab=tab,
                           standings=standings, performers=performers)

@main_bp.route('/match/<int:id>')
def match_detail(id):
    m = Match.query.get_or_404(id)
    return render_template('match.html', match=m)

@main_bp.route('/news')
def news():
    category = request.args.get('category')
    q = News.query.filter_by(status='published')
    if category:
        q = q.filter_by(category=category)
    articles = q.order_by(News.publish_date.desc()).all()
    categories = db.session.query(News.category).distinct().all()
    return render_template('news.html', articles=articles, categories=[c[0] for c in categories], current_cat=category)

@main_bp.route('/news/<slug>')
def news_detail(slug):
    article = News.query.filter_by(slug=slug, status='published').first_or_404()
    article.views = (article.views or 0) + 1
    db.session.commit()
    related = News.query.filter(News.id != article.id, News.status=='published').order_by(News.publish_date.desc()).limit(3).all()
    return render_template('news_detail.html', article=article, related=related)

@main_bp.route('/gallery')
def gallery():
    category = request.args.get('category')
    q = GalleryImage.query.filter_by(is_published=True)
    if category:
        q = q.filter_by(category=category)
    images = q.order_by(GalleryImage.order, GalleryImage.created_at.desc()).all()
    cats = ['Matchday', 'Training', 'Players', 'Fans', 'Events', 'Behind the Scenes']
    return render_template('gallery.html', images=images, categories=cats, current_cat=category)

@main_bp.route('/membership')
def membership():
    plans = MembershipPlan.query.filter_by(is_active=True).order_by(MembershipPlan.order).all()
    return render_template('membership.html', plans=plans)

@main_bp.route('/membership/register', methods=['GET', 'POST'])
def membership_register():
    plans = MembershipPlan.query.filter_by(is_active=True).order_by(MembershipPlan.order).all()
    plan_id = request.args.get('plan') or request.form.get('plan_id')
    selected = MembershipPlan.query.get(plan_id) if plan_id else (plans[0] if plans else None)

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        dob = request.form.get('date_of_birth')
        address = request.form.get('address', '').strip()
        plan_id = request.form.get('plan_id')

        if not full_name or not phone or not plan_id:
            flash('Please fill all required fields.', 'error')
            return render_template('membership-register.html', plans=plans, selected=selected)

        plan = MembershipPlan.query.get(plan_id)
        if not plan:
            flash('Invalid plan selected.', 'error')
            return redirect(url_for('main.membership'))

        is_free = float(plan.price or 0) == 0
        payment_method = request.form.get('payment_method', '')
        payment_reference = request.form.get('payment_reference', '').strip()

        member = Member(
            membership_number=generate_membership_number(),
            plan_id=plan.id,
            full_name=full_name,
            phone=phone,
            email=email or None,
            date_of_birth=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
            address=address,
            status='active' if is_free else 'pending',
            payment_status='free' if is_free else 'submitted',
            payment_method=payment_method or ('Free' if is_free else None),
            payment_reference=payment_reference or None,
            free_tickets=plan.free_tickets or 0,
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
        if 'payment_proof' in request.files and request.files['payment_proof'].filename:
            from utils.helpers import save_upload
            path = save_upload(request.files['payment_proof'], 'members')
            if path:
                member.payment_proof = path
        db.session.add(member)
        db.session.commit()
        session['member_id'] = member.id
        if is_free:
            flash('Welcome! Your FREE Fan membership is active.', 'success')
        else:
            flash('Registration received. Admin will verify your payment shortly.', 'success')
        return redirect(url_for('main.membership_card'))

    return render_template('membership-register.html', plans=plans, selected=selected)

@main_bp.route('/membership/card')
def membership_card():
    mid = session.get('member_id')
    if not mid:
        flash('Please complete registration first.', 'info')
        return redirect(url_for('main.membership'))
    member = Member.query.get(mid)
    if not member:
        return redirect(url_for('main.membership'))
    return render_template('membership-card.html', member=member)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        message = request.form.get('message', '').strip()
        if name and email and message:
            msg = ContactMessage(name=name, email=email, phone=phone, message=message)
            db.session.add(msg)
            db.session.commit()
            flash('Thank you! Your message has been received. We will get back to you soon.', 'success')
            return redirect(url_for('main.contact'))
        flash('Please fill in all required fields.', 'error')
    return render_template('contact.html')

@main_bp.route('/api/chat', methods=['POST'])
def chat_api():
    """Jhapali (I$H) — Jhapa FC fan assistant"""
    data = request.get_json(silent=True) or {}
    raw = (data.get('message') or '').strip()
    message = raw.lower()

    if not message:
        return jsonify({'reply': 'Namaste! I am Jhapali (I$H), your Jhapa FC assistant. Ask about matches, shop, membership or the squad.', 'bot': 'Jhapali'})

    # Shortcut identity
    if message in ('who are you', 'your name', 'i$h', 'jhapali', 'bot'):
        return jsonify({'reply': 'I am Jhapali — shortcut I$H. Official fan assistant of Jhapa FC. Aayo Jhapali! Elephants are marching!', 'bot': 'Jhapali'})

    if ('next' in message and 'match' in message) or message == 'next match':
        nm = Match.query.filter_by(status='upcoming', is_published=True).order_by(Match.match_date.asc()).first()
        if nm:
            return jsonify({'reply': f"Next match: Jhapa FC vs {nm.opponent} on {nm.match_date.strftime('%d %b %Y at %H:%M')} at {nm.venue or 'TBC'} ({nm.competition}).", 'bot': 'Jhapali'})
        return jsonify({'reply': 'Season starts at the end of March. Official fixtures will be published soon. Aayo Jhapali!', 'bot': 'Jhapali'})

    if 'fixture' in message or 'upcoming' in message:
        ups = Match.query.filter_by(status='upcoming', is_published=True).order_by(Match.match_date.asc()).limit(5).all()
        if ups:
            lines = [f"• {m.match_date.strftime('%d %b')} vs {m.opponent}" for m in ups]
            return jsonify({'reply': 'Upcoming fixtures:\n' + '\n'.join(lines), 'bot': 'Jhapali'})
        return jsonify({'reply': 'Fixtures will open when the season begins (end of March).', 'bot': 'Jhapali'})

    if 'result' in message:
        res = Match.query.filter_by(status='finished', is_published=True).order_by(Match.match_date.desc()).limit(5).all()
        if res:
            lines = [f"• vs {m.opponent}: {m.home_score if m.home_score is not None else '—'}-{m.away_score if m.away_score is not None else '—'}" for m in res]
            return jsonify({'reply': 'Recent results:\n' + '\n'.join(lines), 'bot': 'Jhapali'})
        return jsonify({'reply': 'No results published yet.', 'bot': 'Jhapali'})

    if any(w in message for w in ('shop', 'jersey', 'kit', 'store', 'merchandise')):
        return jsonify({'reply': 'Visit the Official Store for jerseys and kits — open Shop from the menu. You can also order a custom jersey!', 'bot': 'Jhapali'})

    if 'member' in message or 'fan club' in message:
        return jsonify({'reply': 'Join the Jhapa FC family! Plans: Fan (free), Silver, Gold (1 free ticket), Premium (2 free tickets). Open Membership to register.', 'bot': 'Jhapali'})

    if any(w in message for w in ('squad', 'player', 'team', 'laken')):
        return jsonify({'reply': 'See Our Squad for the Elephants. Captain Laken Limbu and the full NSL roster are listed there.', 'bot': 'Jhapali'})

    if any(w in message for w in ('contact', 'email', 'phone', 'hello', 'hi', 'namaste', 'aayo')):
        if 'contact' in message or 'email' in message or 'phone' in message:
            return jsonify({'reply': 'Use the Contact page to send a message to the club. Official details are managed from Admin Settings.', 'bot': 'Jhapali'})
        return jsonify({'reply': 'Namaste! I am Jhapali (I$H). Try: Next Match, Fixtures, Shop, Membership, Squad or Contact. Aayo Jhapali!', 'bot': 'Jhapali'})

    return jsonify({'reply': 'I am Jhapali (I$H). Try asking: Next Match, Fixtures, Results, Shop, Membership, Squad or Contact. Elephants are marching!', 'bot': 'Jhapali'})


@main_bp.route('/sitemap.xml')
def sitemap():
    from flask import make_response
    pages = [
        url_for('main.index', _external=True),
        url_for('main.club', _external=True),
        url_for('main.leadership', _external=True),
        url_for('main.squad', _external=True),
        url_for('main.matches', _external=True),
        url_for('main.news', _external=True),
        url_for('main.gallery', _external=True),
        url_for('shop.shop', _external=True),
        url_for('main.membership', _external=True),
        url_for('main.contact', _external=True),
    ]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        xml.append(f'<url><loc>{p}</loc><changefreq>weekly</changefreq></url>')
    xml.append('</urlset>')
    resp = make_response('\n'.join(xml))
    resp.headers['Content-Type'] = 'application/xml'
    return resp


@main_bp.route('/fans-frame')
def fans_frame():
    return render_template('fans-frame.html')
