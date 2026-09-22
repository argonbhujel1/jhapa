from datetime import datetime, timedelta, date
from models import (
    MuseumItem, ClubLegend, AllTimeXI,
    LeagueStanding,
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

        # NSL Season 3 — official results (kick-off 12:45 PM)
        nsl3_matches = [
            # opponent, date, home, jhapa_goals, opp_goals, report
            ('Butwal Lumbini FC', datetime(2025, 3, 30, 12, 45), True, 0, 0,
             'NSL Season 3 · Goalless draw. Jhapa FC Scorers: None. Opponent Scorers: None.'),
            ('Kathmandu Rayzrs FC', datetime(2025, 4, 3, 12, 45), True, 0, 0,
             'NSL Season 3 · Goalless draw. Jhapa FC Scorers: None. Opponent Scorers: None.'),
            ('FC Chitwan', datetime(2025, 4, 6, 12, 45), True, 1, 1,
             "NSL Season 3 · 1-1. Jhapa FC Scorers: Alhaji Gero (90+4' Pen). Opponent Scorers: Torric Jebrin (27')."),
            ('Pokhara Thunders', datetime(2025, 4, 12, 12, 45), True, 1, 1,
             'NSL Season 3 · 1-1. Jhapa FC Scorers: Lazar Arsic. Opponent Scorers: Stéphane Binong.'),
            ('Dhangadhi FC', datetime(2025, 4, 14, 12, 45), True, 0, 1,
             'NSL Season 3 · Loss 0-1. Jhapa FC Scorers: None. Opponent Scorers: Ahmad Hijazi.'),
            ('Lalitpur City FC', datetime(2025, 4, 16, 12, 45), True, 1, 1,
             "NSL Season 3 · 1-1. Jhapa FC Scorers: Laken Limbu (66'). Opponent Scorers: Nabin Lama (54')."),
        ]
        for opp, dt, home, jg, og, report in nsl3_matches:
            exists = Match.query.filter(
                Match.opponent == opp,
                Match.competition == 'Nepal Super League Season 3',
            ).first()
            if exists:
                exists.match_date = dt
                exists.is_home = home
                exists.status = 'finished'
                exists.home_score = jg if home else og
                exists.away_score = og if home else jg
                exists.venue = 'Dashrath Rangasala, Kathmandu'
                exists.match_report = report
                exists.is_published = True
                exists.is_demo = False
            else:
                db.session.add(Match(
                    opponent=opp,
                    match_date=dt,
                    is_home=home,
                    status='finished',
                    home_score=jg if home else og,
                    away_score=og if home else jg,
                    venue='Dashrath Rangasala, Kathmandu',
                    competition='Nepal Super League Season 3',
                    match_report=report,
                    is_demo=False,
                    is_published=True,
                ))

        # NSL Season 3 final league table
        table_rows = [
            # pos, team, pld, w, d, l, gf, ga, pts, is_jhapa
            (1, 'Lalitpur City FC', 6, 3, 3, 0, 10, 8, 12, False),
            (2, 'Dhangadhi FC', 6, 3, 2, 1, 9, 5, 11, False),
            (3, 'FC Chitwan', 6, 3, 1, 2, 8, 6, 10, False),
            (4, 'Pokhara Thunders', 6, 2, 2, 2, 7, 6, 8, False),
            (5, 'Kathmandu Rayzrs', 6, 2, 2, 2, 6, 7, 8, False),
            (6, 'Jhapa FC', 6, 0, 5, 1, 3, 4, 5, True),
            (7, 'Butwal Lumbini FC', 6, 0, 1, 5, 1, 10, 1, False),
        ]
        for pos, team, pld, w, d, l, gf, ga, pts, is_j in table_rows:
            row = LeagueStanding.query.filter_by(team_name=team, season='NSL S3 2025').first()
            if not row:
                row = LeagueStanding(team_name=team, season='NSL S3 2025')
                db.session.add(row)
            row.position = pos
            row.played = pld
            row.won = w
            row.drawn = d
            row.lost = l
            row.goals_for = gf
            row.goals_against = ga
            row.points = pts
            row.is_jhapa = is_j
            row.is_published = True

        # Fair Play Award setting
        if not SiteSetting.query.filter_by(key='fair_play_award').first():
            db.session.add(SiteSetting(
                key='fair_play_award',
                value='Jhapa FC — NSL Season 3 Fair Play Award Winner'
            ))
        else:
            s = SiteSetting.query.filter_by(key='fair_play_award').first()
            s.value = 'Jhapa FC — NSL Season 3 Fair Play Award Winner'


        # Remove only old is_demo placeholder matches (keep official history)
        try:
            for m in Match.query.filter_by(is_demo=True).all():
                # keep if official competition name
                comp = (m.competition or '')
                if 'Season 3' in comp or 'C Division' in comp or 'NSL' in comp or 'Qualifier' in comp or 'Gold Cup' in comp:
                    m.is_demo = False
                    continue
                db.session.delete(m)
            for row in LeagueStanding.query.all():
                if (row.season or '') not in ('NSL S3 2025', 'NSL 2023', 'C Division 2022'):
                    if not row.is_jhapa and row.season not in ('NSL S3 2025',):
                        # keep NSL S3 only for multi-team table; delete random demo
                        if row.season and 'NSL S3' not in (row.season or ''):
                            db.session.delete(row)
            db.session.flush()
            print('Cleaned demo matches')
        except Exception as e:
            print('cleanup matches:', e)


        # --- Documented club history matches (Nepal90 / RSSSF style records) ---
        history_matches = [
            # 2019 C Division Qualifier
            ('Jorpati FC', datetime(2019, 5, 22, 12, 45), True, 2, 2, 'C Division Qualifier', 'D'),
            ('Dynamite FC', datetime(2019, 5, 24, 12, 45), True, 4, 0, 'C Division Qualifier', 'W'),
            ('Active Sports Council', datetime(2019, 6, 16, 12, 45), True, 8, 1, 'C Division Qualifier', 'W'),
            ('Saraswotinagar SC', datetime(2019, 6, 19, 12, 45), True, 1, 0, 'C Division Qualifier', 'W'),
            # 2023 NSL
            ('Pokhara Thunders', datetime(2023, 12, 2, 12, 45), True, 0, 1, 'Nepal Super League 2023', 'L'),
            ('Kathmandu RayZrs', datetime(2023, 12, 4, 12, 45), True, 0, 0, 'Nepal Super League 2023', 'D'),
            ('Birgunj United', datetime(2023, 12, 8, 12, 45), True, 0, 0, 'Nepal Super League 2023', 'D'),
            ('Butwal Lumbini', datetime(2023, 12, 12, 12, 45), True, 1, 0, 'Nepal Super League 2023', 'W'),
            ('Lalitpur City', datetime(2023, 12, 15, 12, 45), True, 0, 0, 'Nepal Super League 2023', 'D'),
            ('Dhangadhi FC', datetime(2023, 12, 20, 12, 45), True, 2, 0, 'Nepal Super League 2023', 'W'),
            ('FC Chitwan', datetime(2023, 12, 22, 12, 45), True, 0, 2, 'Nepal Super League 2023', 'L'),
        ]
        for opp, dt, home, jg, og, comp, _res in history_matches:
            exists = Match.query.filter(
                Match.opponent == opp,
                Match.competition == comp,
            ).first()
            if not exists:
                exists = Match.query.filter(
                    Match.opponent == opp,
                    Match.match_date == dt,
                ).first()
            if exists:
                exists.home_score = jg if home else og
                exists.away_score = og if home else jg
                exists.status = 'finished'
                exists.competition = comp
                exists.is_demo = False
                exists.is_published = True
            else:
                db.session.add(Match(
                    opponent=opp,
                    match_date=dt,
                    is_home=home,
                    status='finished',
                    home_score=jg if home else og,
                    away_score=og if home else jg,
                    competition=comp,
                    venue='Nepal',
                    is_demo=False,
                    is_published=True,
                ))

        # Club info: trophies, ground, stats (documented)
        club_bits = [
            ('trophy_cabinet', 'Trophy Cabinet',
             'Rajgadh Gold Cup|2019|Champions\nJhapa District Level Knockout Tournament|2019|Champions\nMartyr\'s Memorial C Division League|2022|Champions\nC Division to B Division|2022|Promotion'),
            ('home_ground', 'Home Ground',
             'Domalal Rajbanshi Ground\nLocation: Jhapa, Nepal\nHome venue of Jhapa FC'),
            ('club_stats', 'Club Record 2019–2025',
             '50+|Documented matches\n3|Documented trophies\n2|NSL appearances\n1|National promotion\n1|C Division Championship'),
            ('champions_2022', '2022 C Division Champions',
             '13 Matches · 11 Wins · 1 Draw · 1 Loss · 28 GF · 10 GA · 34 Points · League Champions · Promoted to B Division'),
            ('timeline', 'Club Timeline',
             '2019|Founded / competitive emergence · Rajgadh Gold Cup · Jhapa District Knockout\n2021|C Division Qualifier\n2022|C Division Champions · Promotion to B Division\n2023|NSL Debut\n2025|NSL Campaign · 6th place · Fair Play Award'),
            ('club_records', 'Club Records',
             'Biggest documented win|Jhapa FC 8–1 Active Sports Council|16 June 2019\nBest championship campaign|2022 C Division · 11W 1D 1L|2022\nMost goals in a campaign|28 goals — 2022 C Division|2022'),
            ('season_table', 'Season by Season',
             '2019|C Division Qualifier|4|—|—|—|15|3|—\n2019|Jhapa District Knockout|3|—|—|—|8|2|Champions\n2019|Rajgadh Gold Cup|3|—|—|—|4|2|Champions\n2021|C Division Super Six|—|—|—|—|—|—|Missed promotion (lost 2-1 to Church Boys)\n2022|C Division League|13|11|1|1|28|10|Champions\n2023|NSL|8|2|4|2|4|4|5th\n2025|Martyr Memorial B Division|13|5|3|5|15|13|8th\n2025|NSL Season 3|6|0|5|1|3|4|6th'),
        ]
        for key, title, content in club_bits:
            row = ClubInfo.query.filter_by(key=key).first()
            if row:
                row.title = title
                row.content = content
            else:
                db.session.add(ClubInfo(key=key, title=title, content=content))
        print('Club history content seeded')

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

        # Historical / archive players from public profiles (add if missing)
        archive_players = [
            dict(name='Anjan Bista', number=7, position='Left Winger / Centre-Forward (LW/CF)', nationality='Nepal', order=40,
                 career='First marquee player · Jhapa FC 2022–23 · Nepal national team'),
            dict(name='Stefan Cupic', number=25, position='Goalkeeper (GK)', nationality='Serbia', order=41,
                 career='NSL 2023 · 8 apps · 5 clean sheets · media Best XI'),
            dict(name='Samandar Ochilov', number=20, position='Centre Back (CB)', nationality='Uzbekistan', order=42,
                 career='NSL 2023 foreign centre-back'),
            dict(name='Amit Tamang', number=None, position='Left-Back (LB)', nationality='Nepal', order=43,
                 career='2022 inaugural NSL squad'),
            dict(name='Yogesh Gurung', number=15, position='Centre Back (CB)', nationality='Nepal', order=44,
                 career='NSL 2023 defensive unit'),
            dict(name='Laxman Ruchal', number=None, position='Winger / Midfielder', nationality='Nepal', order=45,
                 career='NSL 2023 attacking unit'),
            dict(name='Utsav Rai', number=None, position='Central Midfielder (CM)', nationality='Nepal', order=46,
                 career='2022 inaugural squad'),
            dict(name='Sesehang Angdembe', number=None, position='Defensive Midfielder (DM)', nationality='Nepal', order=47,
                 career='2022 inaugural squad'),
            dict(name='Aashish Lama', number=None, position='Centre-Forward (ST)', nationality='Nepal', order=48,
                 career='2022 inaugural squad'),
            dict(name='Dev Limbu', number=None, position='Goalkeeper (GK)', nationality='Nepal', order=49,
                 career='2022 inaugural goalkeeper'),
            dict(name='Kamal Shrestha', number=None, position='Right-Back (RB)', nationality='Nepal', order=50,
                 career='2022 auction signing'),
            dict(name='Nishan Khadka', number=None, position='Defender', nationality='Nepal', order=51,
                 career='2022 Golden Buzzer signing'),
            dict(name='Santosh Tamang', number=None, position='Attacking Midfielder (AM)', nationality='Nepal', order=52,
                 career='2022 major auction signing'),
            dict(name='Ranjan Bista', number=None, position='Midfielder', nationality='Nepal', order=53,
                 career='2022 inaugural midfield'),
            dict(name='Bipin Kandel', number=None, position='Midfielder', nationality='Nepal', order=54,
                 career='2022 inaugural midfield'),
            dict(name='Janak Koirala', number=None, position='Defender', nationality='Nepal', order=55,
                 career='2022 inaugural defender'),
            dict(name='Paras Karki', number=None, position='Midfielder / Utility', nationality='Nepal', order=56,
                 career='2022 C Division Player of the Tournament (ANFA)'),
            dict(name='Bishal Khawas', number=None, position='Forward (ST)', nationality='Nepal', order=57,
                 career='2022 C Division final hero · 2 goals in title match'),
            dict(name='Jorge Pelaz Sanchez', number=None, position='Centre-Forward (ST)', nationality='Spain', order=58,
                 career='NSL 2023 · Canillas · foreign striker'),
            dict(name='Nando Cozar', number=None, position='Central Midfielder (CM)', nationality='Spain', order=59,
                 career='NSL 2023 foreign midfielder'),
        ]
        for pl in archive_players:
            if not Player.query.filter_by(name=pl['name']).first():
                db.session.add(Player(
                    name=pl['name'],
                    number=pl.get('number'),
                    position=pl.get('position'),
                    nationality=pl.get('nationality', 'Nepal'),
                    career=pl.get('career', ''),
                    is_published=True,
                    order=pl.get('order', 99),
                ))
        print('Archive players ensured in squad')


        # Top performers till now (documented across eras)
        try:
            from models import TopPerformer
            scorers = [
                ('Alhaji Gero', 'Goals', 1, 'NSL S3 2025'),
                ('Lazar Arsic', 'Goals', 1, 'NSL S3 2025'),
                ('Laken Limbu', 'Goals', 1, 'NSL S3 2025'),
                ('Anjan Bista', 'Goals', 1, 'NSL 2022–23'),
                ('Bishal Khawas', 'Goals', 2, 'C Div Final 2022'),
                ('Stefan Cupic', 'Clean Sheets', 5, 'NSL 2023'),
            ]
            TopPerformer.query.delete()
            db.session.flush()
            for i, (name, cat, val, season) in enumerate(scorers):
                photo = None
                pl = Player.query.filter_by(name=name).first()
                if not pl:
                    last = name.split()[-1]
                    pl = Player.query.filter(Player.name.ilike('%' + last + '%')).first()
                if pl:
                    name = pl.name
                    if pl.photo:
                        photo = pl.photo
                db.session.add(TopPerformer(
                    name=name,
                    category=cat,
                    value=val,
                    team='Jhapa FC',
                    photo=photo,
                    order=i,
                    is_published=True,
                    season=season,
                ))
            print('Top performers till now seeded')
        except Exception as e:
            print('top performers seed:', e)


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
        
        # Digital Museum / Legends / All-Time XI (documented notable names; admin can edit photos)
        try:
            from models import MuseumItem, ClubLegend, AllTimeXI
            if ClubLegend.query.count() == 0:
                legends = [
                    dict(name='Anjan Bista', role='Forward', era='NSL 2023', category='Hall of Fame',
                         achievement='Marquee player / captain for NSL debut campaign (public records).',
                         current_club='', order=1),
                    dict(name='Laken Limbu', role='Midfielder', era='NSL 2025', category='Hall of Fame',
                         achievement='Team captain · Nepal national team · NSL S3 goalscorer.',
                         current_club='Jhapa FC', order=2),
                    dict(name='Paras Karki', role='Player', era='2022 C Division', category='Hall of Fame',
                         achievement='Player of the Tournament — Martyr\'s Memorial C Division League 2022 (ANFA).',
                         current_club='', order=3),
                    dict(name='Bishal Khawas', role='Forward', era='2022 C Division', category='Hall of Fame',
                         achievement='Scored twice in C Division title-clinching final vs Swoyambhu (ANFA).',
                         current_club='', order=4),
                    dict(name='Oriol Mohedano', role='Coach', era='NSL 2023', category='Where Are They Now',
                         achievement='Head coach NSL 2023 (Oct–Dec 2023).',
                         current_club='', order=10),
                    dict(name='Prabesh Katuwal', role='Coach', era='NSL 2025', category='Hall of Fame',
                         achievement='Head coach NSL Season 3 (2025).',
                         current_club='Jhapa FC', order=5),
                ]
                for L in legends:
                    db.session.add(ClubLegend(**L, is_published=True))
            # All-Time XI — best documented names (only seed if empty so admin edits persist)
            xi = [
                # 4-3-3 style notable XI
                ('GK', 1, 'Stefan Cupic', 25, 'NSL 2023 · 8 apps · 5 clean sheets · Best XI'),
                ('RB', 2, 'Chhiring Lama', 4, '2023–25 · two-era defender'),
                ('CB', 3, 'Azamat Abdullaev', 6, 'NSL 2025 · centre-back'),
                ('CB', 4, 'Samandar Ochilov', 20, 'NSL 2023 · foreign CB'),
                ('LB', 5, 'Amit Tamang', None, '2022 inaugural · left-back'),
                ('CM', 6, 'Laken Limbu', 10, 'Captain · 2022–25 · club identity'),
                ('CM', 7, 'Abinash Syangtan', 8, 'NSL midfielder · 2025 regular'),
                ('AM', 8, 'Lazar Arsic', 11, 'NSL S3 · goals + creativity'),
                ('LW', 9, 'Anjan Bista', 7, 'First marquee player · 2022–23'),
                ('ST', 10, 'Alhaji Gero', 9, 'NSL S3 top scorer'),
                ('RW', 11, 'Bishal Khawas', None, '2022 C Div final hero · 2 goals in title match'),
            ]
            if AllTimeXI.query.count() == 0:
                for pos, order, name, num, note in xi:
                    db.session.add(AllTimeXI(
                        position=pos, slot=order, name=name, number=num, note=note,
                        order=order, is_published=True
                    ))
                print('All-Time XI seeded')
            if MuseumItem.query.count() == 0:
                db.session.add(MuseumItem(
                    title='Martyr\'s Memorial C Division Champions 2022',
                    category='Trophy', year='2022',
                    description='Jhapa FC clinched C Division title and promotion (ANFA).',
                    order=1, is_published=True
                ))
                db.session.add(MuseumItem(
                    title='NSL Fair Play Award — Season 3',
                    category='Trophy', year='2025',
                    description='Jhapa FC named Fair Play Award winners in NSL Season 3.',
                    order=2, is_published=True
                ))
            # Stadium capacity note
            hg = ClubInfo.query.filter_by(key='home_ground').first()
            if hg:
                hg.content = 'Domalal Rajbanshi Ground\nLocation: Birtamod, Jhapa, Koshi Province, Nepal\nCapacity: approx. 5,000–10,000 (public listings vary)\nHome venue of Jhapa FC'
            print('Museum / Legends / XI seeded')
        except Exception as e:
            print('museum seed:', e)

        
        # Expand Hall of Fame profiles (documented)
        try:
            from models import ClubLegend
            profiles = [
                dict(name='Anjan Bista', role='Player', position='LW / CF', nationality='Nepal', era='2022, 2023',
                     achievement='Jhapa FC first marquee player', awards='Marquee player NSL debut era',
                     appearances='6*', goals='1*', tags='Players,Club Legends', biography='Inaugural marquee player and major star for Jhapa FC NSL campaigns.', order=1),
                dict(name='Laken Limbu', role='Captain', position='Central Midfielder', nationality='Nepal', era='2022, 2023, 2024/25',
                     achievement='Club captain · long-term Jhapa FC identity', awards='Captain / marquee',
                     appearances='6*', goals='1*', tags='Players,Captains,Club Legends', biography='Consistent Jhapa FC midfielder from inaugural era through 2025 captaincy.', order=2),
                dict(name='Paras Karki', role='Player', position='Player', nationality='Nepal', era='2022 C Division',
                     achievement='2022 Player of the Tournament (ANFA C Division)', awards='Player of the Tournament',
                     tags='Players,Achievements,Club Legends', biography='Named Player of the Tournament as Jhapa won the Martyr\'s Memorial C Division League 2022.', order=3),
                dict(name='Bishal Khawas', role='Player', position='Forward', nationality='Nepal', era='2022 C Division',
                     achievement='2022 Championship final scorer (2 goals vs Swoyambhu)', awards='Final hero',
                     tags='Players,Achievements,Club Legends', biography='Scored twice in the C Division title-clinching final (ANFA).', order=4),
                dict(name='Stefan Cupic', role='Player', position='Goalkeeper', nationality='Serbia', era='2023',
                     achievement='NSL 2023 Best XI goalkeeper (media)', awards='NSL 2023 Best XI · 5 clean sheets',
                     appearances='8', goals='0', tags='Players,International,Club Legends', biography='Serbian goalkeeper with 8 appearances and 5 clean sheets in NSL 2023.', order=5),
                dict(name='Alhaji Gero', role='Player', position='Centre-Forward', nationality='Nigeria', era='2024/25',
                     achievement='NSL Season 3 goalscorer', appearances='6*', goals='1*', tags='Players,International',
                     biography='Nigerian centre-forward, NSL S3 foreign attacking option.', order=6),
                dict(name='Lazar Arsic', role='Player', position='Attacking Midfielder', nationality='Serbia', era='2024/25',
                     achievement='NSL Season 3 goalscorer', appearances='6*', goals='1*', assists='1*', tags='Players,International',
                     biography='Serbian attacking midfielder, key foreign creative player NSL S3.', order=7),
                dict(name='Prabesh Katuwal', role='Coach', position='Head Coach', nationality='Nepal', era='NSL 2025',
                     achievement='Head coach NSL Season 3', tags='Coaches', biography='Appointed head coach for NSL Season 3.', order=8),
            ]
            for p in profiles:
                row = ClubLegend.query.filter_by(name=p['name']).first()
                if not row:
                    row = ClubLegend(name=p['name'])
                    db.session.add(row)
                for k, v in p.items():
                    if k != 'name' and v is not None:
                        setattr(row, k, v)
                row.category = 'Hall of Fame'
                row.is_published = True
            # Always refresh season table content
            st = ClubInfo.query.filter_by(key='season_table').first()
            if st:
                st.content = '2019|C Division Qualifier|4|—|—|—|15|3|—\n2019|Jhapa District Knockout|3|—|—|—|8|2|Champions\n2019|Rajgadh Gold Cup|3|—|—|—|4|2|Champions\n2021|C Division Super Six|—|—|—|—|—|—|Missed promotion (lost 2-1 to Church Boys)\n2022|C Division League|13|11|1|1|28|10|Champions\n2023|NSL|8|2|4|2|4|4|5th\n2025|Martyr Memorial B Division|13|5|3|5|15|13|8th\n2025|NSL Season 3|6|0|5|1|3|4|6th'
            print('Hall of Fame profiles updated')
        except Exception as e:
            print('hof profiles:', e)

        
        # Photo auto-fetch only via Admin → Players → Auto-fetch (avoids Vercel timeout)

        print('Database seeded successfully.')
