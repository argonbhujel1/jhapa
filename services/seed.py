from datetime import datetime, timedelta, date
from models import (
    db, User, ClubInfo, Match, News, ProductCategory, Product, ProductVariant,
    MembershipPlan, Sponsor, SiteSetting, GalleryImage, Player, Leadership
)
from utils.helpers import slugify
from werkzeug.security import generate_password_hash

def seed_all(app):
    with app.app_context():
        # Admin user
        if not User.query.filter_by(email=app.config['ADMIN_EMAIL']).first():
            admin = User(
                email=app.config['ADMIN_EMAIL'],
                name='Jhapa FC Admin',
                role='admin'
            )
            admin.set_password(app.config['ADMIN_PASSWORD'])
            db.session.add(admin)

        # Club Info
        club_defaults = [
            ('about_title', 'More Than A Club', 'The Pride of Jhapa'),
            ('about_story', 'Our Story', 
             'Jhapa FC represents the passion, pride and unity of the people of Jhapa. '
             'Founded with a vision to elevate football in the region, the club stands as a symbol of local talent, '
             'community spirit and the pursuit of excellence on and off the pitch. '
             'We are building a future where every fan can be proud of The Elephants of Jhapa.'),
            ('vision', 'Vision', 'To become a leading football club in Nepal that inspires generations through excellence, integrity and community impact.'),
            ('mission', 'Mission', 'To develop local talent, compete at the highest level and create a sustainable football ecosystem that unites the people of Jhapa.'),
            ('values', 'Values', 'Pride • Unity • Excellence • Respect • Community'),
            ('established', 'Established', '2021'),
        ]
        for key, title, content in club_defaults:
            if not ClubInfo.query.filter_by(key=key).first():
                db.session.add(ClubInfo(key=key, title=title, content=content))

        # Site settings
        settings = [
            ('site_title', 'Jhapa FC | Official Football Club'),
            ('site_tagline', 'ONE CLUB. ONE PRIDE.'),
            ('contact_email', '[Official email coming soon]'),
            ('contact_phone', '[Official phone coming soon]'),
            ('contact_address', 'Jhapa, Nepal'),
            ('facebook', '#'),
            ('instagram', '#'),
            ('twitter', '#'),
            ('youtube', '#'),
            ('tiktok', '#'),
        ]
        for key, value in settings:
            if not SiteSetting.query.filter_by(key=key).first():
                db.session.add(SiteSetting(key=key, value=value))

        # Demo Matches
        if Match.query.count() == 0:
            base = datetime.utcnow().replace(hour=16, minute=0, second=0, microsecond=0)
            matches = [
                # Upcoming
                ('Pokhara Thunders', base + timedelta(days=12), True, 'upcoming', None, None, 'Dashrath Stadium'),
                ('Lalitpur City FC', base + timedelta(days=26), False, 'upcoming', None, None, 'ANFA Complex'),
                ('Butwal Lumbini FC', base + timedelta(days=40), True, 'upcoming', None, None, 'Jhapa Stadium'),
                ('Kathmandu Rayzrs', base + timedelta(days=54), False, 'upcoming', None, None, 'Dashrath Stadium'),
                # Results
                ('Dharan FC', base - timedelta(days=7), True, 'finished', 2, 1, 'Jhapa Stadium'),
                ('Biratnagar City', base - timedelta(days=21), False, 'finished', 1, 1, 'Sahid Rangsala'),
                ('Chitwan Rhinos', base - timedelta(days=35), True, 'finished', 3, 0, 'Jhapa Stadium'),
                ('Pokhara Thunders', base - timedelta(days=49), False, 'finished', 0, 2, 'Pokhara Stadium'),
            ]
            for opp, dt, home, status, hs, as_, venue in matches:
                db.session.add(Match(
                    opponent=opp,
                    match_date=dt,
                    is_home=home,
                    status=status,
                    home_score=hs if home else as_,
                    away_score=as_ if home else hs,
                    venue=venue,
                    competition='Nepal Super League',
                    is_demo=True,
                    is_published=True
                ))

        # Demo News
        if News.query.count() == 0:
            news_items = [
                ('Jhapa FC Secures Important Win in Nepal Super League', 'Match Report',
                 'A dominant performance at home sees The Elephants claim all three points in a crucial fixture.',
                 '''Jhapa FC delivered an impressive performance to secure a vital victory in the Nepal Super League. 
The team showed great character and tactical discipline throughout the ninety minutes.
Goals from open play and a well-worked set piece sealed the result in front of a passionate home crowd.
Head Coach praised the squad for their work rate and unity: "We played as a team and this win is for our amazing fans."
The result strengthens our position as we continue the campaign with renewed confidence.
Support continues to grow across Jhapa as the club builds momentum both on and off the pitch.'''),
                ('Matchday Preview: Ready for the Next Challenge', 'Matchday Preview',
                 'Everything you need to know ahead of Jhapa FC\'s upcoming fixture.',
                 '''The squad is fully focused ahead of the next Nepal Super League encounter.
Training sessions have been intense with emphasis on shape, transitions and set-piece routines.
Fans are encouraged to arrive early and create the famous wall of blue support.
Tickets and membership benefits remain available through the official channels.
One Club. One Pride. Let\'s get behind the team.'''),
                ('Training Update: Squad Sharpens Ahead of Busy Schedule', 'Training Update',
                 'Behind the scenes as the team prepares for a demanding run of fixtures.',
                 '''This week\'s training has focused on recovery, tactical refinement and individual development.
The coaching staff continue to monitor player workloads carefully.
Community training sessions remain popular with young players from across the district.
Stay tuned for more updates from the training ground.'''),
                ('Club Announcement: Fan Membership Drive Opens', 'Announcement',
                 'Join the Jhapa FC family and unlock exclusive benefits for the season.',
                 '''Jhapa FC is proud to launch the official Fan Membership programme.
Four tiers are available – Fan, Silver, Gold and Premium – each offering unique privileges.
Members receive digital membership cards, priority access and exclusive merchandise discounts.
Register now through the official website and become part of The Elephants of Jhapa.'''),
                ('Fan Community Spotlight: The Blue Wall of Jhapa', 'Fan Community',
                 'Celebrating the passion and loyalty of our incredible supporters.',
                 '''From the stands to the streets, Jhapa FC fans continue to inspire the team.
The organised support groups create an atmosphere that makes every home match special.
We thank every supporter who travels, sings and stands with the club through every moment.
Together we are stronger. One Club. One Pride.'''),
            ]
            for i, (title, cat, excerpt, content) in enumerate(news_items):
                slug = slugify(title)
                if not News.query.filter_by(slug=slug).first():
                    db.session.add(News(
                        title=title,
                        slug=slug,
                        category=cat,
                        excerpt=excerpt,
                        content=content,
                        author='Jhapa FC Media',
                        publish_date=datetime.utcnow() - timedelta(days=i*3),
                        status='published',
                        is_demo=True
                    ))

        # Product Categories
        cats = ['Jerseys', 'Training', 'Tracksuits', 'T-Shirts', 'Hoodies', 'Caps', 'Scarves', 'Accessories']
        for i, name in enumerate(cats):
            if not ProductCategory.query.filter_by(name=name).first():
                db.session.add(ProductCategory(name=name, slug=slugify(name), order=i))

        db.session.flush()

        # Demo Products
        if Product.query.count() == 0:
            products_data = [
                ('Jhapa FC Home Jersey', 'Jerseys', 2999, 'Official home kit in classic light blue. Premium fabric, embroidered crest placeholder.', True),
                ('Jhapa FC Away Jersey', 'Jerseys', 2999, 'Official away kit. Clean design for the road.', True),
                ('Jhapa FC Goalkeeper Jersey', 'Jerseys', 2799, 'Specialist goalkeeper shirt with enhanced padding areas.', False),
                ('Training Kit Top', 'Training', 1899, 'Breathable training top for daily sessions.', False),
                ('Training Shorts', 'Training', 999, 'Lightweight training shorts with club branding.', False),
                ('Full Tracksuit', 'Tracksuits', 4499, 'Premium tracksuit jacket and pants set.', True),
                ('Club T-Shirt', 'T-Shirts', 1299, 'Everyday cotton t-shirt with elephant motif.', True),
                ('Hoodie – The Elephants', 'Hoodies', 2499, 'Warm hoodie featuring The Elephants of Jhapa design.', True),
                ('Official Cap', 'Caps', 799, 'Adjustable cap with embroidered logo placeholder.', False),
                ('Supporters Scarf', 'Scarves', 999, 'Classic woven scarf in club colours.', False),
            ]
            for name, cat_name, price, desc, featured in products_data:
                cat = ProductCategory.query.filter_by(name=cat_name).first()
                p = Product(
                    name=name,
                    slug=slugify(name),
                    description=desc,
                    price=price,
                    category_id=cat.id if cat else None,
                    stock=50,
                    is_demo=True,
                    is_active=True,
                    is_featured=featured
                )
                db.session.add(p)
                db.session.flush()
                for size in ['S', 'M', 'L', 'XL', 'XXL']:
                    db.session.add(ProductVariant(product_id=p.id, size=size, stock=15, sku=f"{p.slug[:10]}-{size}"))

        # Membership Plans
        if MembershipPlan.query.count() == 0:
            plans = [
                ('Fan', 0, 'FREE membership\nDigital membership card\nMatchday updates\nExclusive content access\nFan community access', 0),
                ('Silver', 1500, 'All Fan benefits\n10% shop discount\nPriority ticket info\nMember-only newsletters', 0),
                ('Gold', 3000, 'All Silver benefits\n15% shop discount\n1 FREE match ticket per season\nExclusive member events\nSigned digital memorabilia', 1),
                ('Premium', 5000, 'All Gold benefits\n20% shop discount\n2 FREE match tickets per season\nMeet & greet opportunities\nVIP matchday experience (limited)\nPersonalised digital card', 2),
            ]
            for i, (name, price, benefits, tickets) in enumerate(plans):
                db.session.add(MembershipPlan(
                    name=name,
                    slug=slugify(name),
                    price=price,
                    benefits=benefits,
                    free_tickets=tickets,
                    order=i,
                    is_active=True
                ))

        # Tech Partner – BAM Studio only published
        if not Sponsor.query.filter_by(name='BAM Studio').first():
            db.session.add(Sponsor(
                name='BAM Studio',
                category='Web & Technology Partner',
                website='https://argan.com.np/',
                is_published=True,
                order=0
            ))

        # Gallery placeholders (no real images, just records)
        if GalleryImage.query.count() == 0:
            for cat in ['Matchday', 'Training', 'Fans', 'Events', 'Behind the Scenes']:
                for i in range(3):
                    db.session.add(GalleryImage(
                        title=f'{cat} Moment {i+1}',
                        category=cat,
                        image='',  # placeholder – admin will upload
                        caption=f'Demo gallery item – {cat}',
                        is_demo=True,
                        is_published=True
                    ))


        # Update existing membership plans (Fan free, tickets)
        for name, price, tickets in [('Fan', 0, 0), ('Silver', 1500, 0), ('Gold', 3000, 1), ('Premium', 5000, 2)]:
            plan = MembershipPlan.query.filter_by(name=name).first()
            if plan:
                plan.price = price
                if hasattr(plan, 'free_tickets'):
                    plan.free_tickets = tickets


        # --- Official public NSL squad (name/number/position from public sources) ---
        if Player.query.filter_by(is_published=True).count() < 5:
            nsl_players = [
                # GK
                dict(name='Nemanja Lemajic', number=1, position='Goalkeeper (GK)', nationality='Montenegro', order=1),
                dict(name='Anjal Shrestha', number=25, position='Goalkeeper (GK)', nationality='Nepal', order=2),
                dict(name='Rubin Bogati', number=None, position='Goalkeeper (GK)', nationality='Nepal', order=3),
                # DF
                dict(name='Chhiring Lama', number=4, position='Centre Back (CB)', nationality='Nepal', order=10),
                dict(name='Ashish Gurung', number=5, position='Centre Back (CB)', nationality='Nepal', order=11),
                dict(name='Azamat Abdullaev', number=6, position='Centre Back (CB)', nationality='Uzbekistan', order=12),
                dict(name='Srijan Dani', number=16, position='Defender', nationality='Nepal', order=13),
                dict(name='Roshan Pahari', number=23, position='Defender', nationality='Nepal', order=14),
                dict(name='Dipesh Dhimal', number=34, position='Defender', nationality='Nepal', order=15),
                dict(name='Dipendra BK', number=21, position='Defender', nationality='Nepal', order=16),
                # MF
                dict(name='Laken Limbu', number=10, position='Central Midfielder (CM)', nationality='Nepal', order=20, career='Team Captain · Nepal national team'),
                dict(name='Lazar Arsic', number=11, position='Attacking Midfielder (AM)', nationality='Serbia', order=21),
                dict(name='Abinash Syangtan', number=8, position='Central Midfielder (CM)', nationality='Nepal', order=22),
                dict(name='Mukhammad Isaev', number=77, position='Attacking Midfielder (AM)', nationality='Uzbekistan', order=23),
                dict(name='Aron Thapa', number=80, position='Midfielder', nationality='Nepal', order=24),
                dict(name='John Bista', number=13, position='Midfielder', nationality='Nepal', order=25),
                dict(name='Saurav Limbu', number=19, position='Left Winger (WG)', nationality='Nepal', order=26),
                dict(name='Ritik Kumar Khadka', number=17, position='Midfielder', nationality='Nepal', order=27),
                dict(name='Shyamu Murmu', number=18, position='Midfielder', nationality='Nepal', order=28),
                # FW
                dict(name='Alhaji Gero', number=9, position='Striker (ST)', nationality='Nigeria', order=30),
                dict(name='Aryan Rai', number=7, position='Forward (FW)', nationality='Nepal', order=31),
                dict(name='Prabin Khulal Basnet', number=14, position='Winger (WG)', nationality='Nepal', order=32),
                dict(name='Ujwal Rai', number=37, position='Forward (FW)', nationality='Nepal', order=33),
            ]
            for i, pl in enumerate(nsl_players):
                if not Player.query.filter_by(name=pl['name']).first():
                    db.session.add(Player(
                        name=pl['name'],
                        number=pl.get('number'),
                        position=pl.get('position'),
                        nationality=pl.get('nationality', 'Nepal'),
                        career=pl.get('career', 'NSL squad (public roster)'),
                        is_published=True,
                        order=pl.get('order', i),
                    ))
            print('NSL players seeded')

        # Leadership — publicly named roles only
        if Leadership.query.filter_by(section='Technical Team', position='Full Stack Engineer').first() is None:
            leaders = [
                dict(name='Arpan Bikram Khadka', position='President', section='Executive Board', order=1,
                     bio='President of Jhapa FC.'),
                dict(name='Sujan Gautam', position='General Secretary', section='Executive Board', order=2,
                     bio='General Secretary of Jhapa FC.'),
                dict(name='Bikram Thapa', position='CEO', section='Executive Board', order=3,
                     bio='Chief Executive Officer.'),
                # Club technical (coaching)
                dict(name='Prabesh Katuwal', position='Head Coach', section='Advisory Council', order=10,
                     bio='Head Coach · Jhapa FC.'),
                dict(name='Kumar Giri', position='Assistant Coach', section='Advisory Council', order=11,
                     bio='Assistant Coach · Jhapa FC.'),
                dict(name='Min Basnet', position='Goalkeeper Coach', section='Advisory Council', order=12,
                     bio='Goalkeeper Coach · Jhapa FC.'),
                # BAM Developers — Technical Team (4 roles)
                dict(name='BAM Developers', position='Video Editor', section='Technical Team', order=20,
                     bio='Creates match highlights, fan videos and official club media for Jhapa FC.'),
                dict(name='BAM Developers', position='UI/UX Designer', section='Technical Team', order=21,
                     bio='Designs the look and feel of the Jhapa FC website, app screens and fan experience.'),
                dict(name='BAM Developers', position='Full Stack Developer', section='Technical Team', order=22,
                     bio='Builds website features: shop, membership, news, gallery and admin tools.'),
                dict(name='BAM Developers', position='Full Stack Engineer', section='Technical Team', order=23,
                     bio='Owns platform architecture, performance, security and deployments (Neon, Cloudinary, Vercel).'),
            ]
            for L in leaders:
                existing = Leadership.query.filter_by(name=L['name'], position=L['position']).first()
                if existing:
                    existing.is_published = True
                    existing.section = L['section']
                    existing.order = L['order']
                    if L.get('bio'):
                        existing.bio = L['bio']
                else:
                    db.session.add(Leadership(
                        name=L['name'], position=L['position'], section=L['section'],
                        order=L['order'], is_published=True,
                        bio=L.get('bio', '')
                    ))
            print('Leadership seeded')

        # Ensure coaches are Advisory Council; BAM stays Technical Team
        for coach_name, pos in [
            ('Prabesh Katuwal', 'Head Coach'),
            ('Kumar Giri', 'Assistant Coach'),
            ('Min Basnet', 'Goalkeeper Coach'),
        ]:
            c = Leadership.query.filter_by(name=coach_name).first()
            if c:
                c.section = 'Advisory Council'
                c.position = pos
                c.is_published = True
        # Keep only 4 BAM technical roles
        for extra in Leadership.query.filter_by(section='Technical Team', position='Assistant Editor').all():
            db.session.delete(extra)


        db.session.commit()
        print('Database seeded successfully.')
