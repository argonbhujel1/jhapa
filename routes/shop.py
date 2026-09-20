from flask import render_template, request, redirect, url_for, flash, session, jsonify
from models import db, Product, ProductCategory, ProductVariant, CartItem, Order, OrderItem
from utils.helpers import generate_order_number, format_currency
from . import shop_bp
import uuid
from decimal import Decimal

def get_or_create_cart_id():
    if 'cart_id' not in session:
        session['cart_id'] = str(uuid.uuid4())
    return session['cart_id']

def get_cart_items():
    sid = session.get('cart_id')
    if not sid:
        return []
    return CartItem.query.filter_by(session_id=sid).all()

def cart_totals(items):
    subtotal = sum(Decimal(str(item.product.price)) * item.quantity for item in items if item.product)
    delivery = Decimal('150') if subtotal > 0 else Decimal('0')
    if subtotal >= 5000:
        delivery = Decimal('0')
    total = subtotal + delivery
    return subtotal, delivery, total

@shop_bp.route('/shop')
def shop():
    category = request.args.get('category')
    q = Product.query.filter_by(is_active=True)
    if category:
        cat = ProductCategory.query.filter_by(slug=category).first()
        if cat:
            q = q.filter_by(category_id=cat.id)
    products = q.order_by(Product.is_featured.desc(), Product.name).all()
    categories = ProductCategory.query.order_by(ProductCategory.order).all()
    return render_template('shop.html', products=products, categories=categories, current_cat=category)

@shop_bp.route('/product/<slug>')
def product(slug):
    p = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    variants = ProductVariant.query.filter_by(product_id=p.id).all()
    related = Product.query.filter(Product.id != p.id, Product.is_active==True, Product.category_id==p.category_id).limit(4).all()
    return render_template('product.html', product=p, variants=variants, related=related)

@shop_bp.route('/custom-jersey', methods=['GET', 'POST'])
def custom_jersey():
    base_price = Decimal('3499')  # higher for custom
    if request.method == 'POST':
        jersey_type = request.form.get('jersey_type', 'Home')
        size = request.form.get('size', 'M')
        name = request.form.get('player_name', '').strip()[:12]
        number = request.form.get('jersey_number', '').strip()[:2]
        qty = int(request.form.get('quantity', 1) or 1)
        qty = max(1, min(qty, 5))

        # Find or create a custom product concept – we use a special product
        custom_prod = Product.query.filter_by(slug='custom-jhapa-fc-jersey').first()
        if not custom_prod:
            from models import ProductCategory
            cat = ProductCategory.query.filter_by(name='Jerseys').first()
            custom_prod = Product(
                name='Custom Jhapa FC Jersey',
                slug='custom-jhapa-fc-jersey',
                description='Personalised official-style jersey with your name and number.',
                price=base_price,
                is_demo=True,
                is_active=True,
                stock=999
            )
            if cat:
                custom_prod.category_id = cat.id
            db.session.add(custom_prod)
            db.session.commit()

        sid = get_or_create_cart_id()
        item = CartItem(
            session_id=sid,
            product_id=custom_prod.id,
            quantity=qty,
            custom_name=name,
            custom_number=number,
            is_custom=True
        )
        db.session.add(item)
        db.session.commit()
        flash('Custom jersey added to cart!', 'success')
        return redirect(url_for('shop.cart'))

    jersey_imgs = {'Home': '', 'Away': '', 'Third': ''}
    try:
        for p in Product.query.filter(Product.is_active == True).order_by(Product.id).all():
            n = (p.name or '').lower()
            src = getattr(p, 'image_back', None) or p.image
            if not src:
                continue
            if 'third' in n or '3rd' in n:
                jersey_imgs['Third'] = src
            elif 'away' in n:
                jersey_imgs['Away'] = src
            elif 'home' in n:
                jersey_imgs['Home'] = src
            elif 'jersey' in n or 'kit' in n:
                if not jersey_imgs['Home']:
                    jersey_imgs['Home'] = src
        if not any(jersey_imgs.values()):
            anyj = Product.query.filter(Product.name.ilike('%jersey%'), Product.is_active == True).first()
            if not anyj:
                anyj = Product.query.filter(Product.is_active == True).first()
            if anyj:
                src = getattr(anyj, 'image_back', None) or anyj.image
                if src:
                    jersey_imgs['Home'] = jersey_imgs['Away'] = jersey_imgs['Third'] = src
    except Exception as e:
        print('custom_jersey image load:', e)
    return render_template('custom-jersey.html', base_price=base_price, jersey_imgs=jersey_imgs)
