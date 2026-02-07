from flask import Flask, render_template, request, redirect, url_for, session, flash,make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from xhtml2pdf import pisa
from io import BytesIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pharmasync-secret-key-change-in-production-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharmasync.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

db = SQLAlchemy(app)

# ==================== CONTEXT PROCESSOR ====================

@app.context_processor
def utility_processor():
    return dict(now=datetime.now())

# ==================== DATABASE MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='staff')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200))
    category = db.Column(db.String(100))
    manufacturer = db.Column(db.String(200))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.Date)
    batch_number = db.Column(db.String(100))
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    reorder_level = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact_person = db.Column(db.String(200))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, completed, cancelled
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    supplier = db.relationship('Supplier', backref='purchase_orders')
    medicine = db.relationship('Medicine', backref='purchase_orders')

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow)
    customer_name = db.Column(db.String(200))
    medicine = db.relationship('Medicine', backref='sales')

# ==================== DECORATORS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROUTES ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email
            session['role'] = user.role
            if remember:
                session.permanent = True
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return render_template('register.html')
        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics
    total_medicines = Medicine.query.count()
    low_stock_count = Medicine.query.filter(Medicine.quantity <= Medicine.reorder_level).count()
    expired_count = Medicine.query.filter(Medicine.expiry_date < datetime.now().date()).count()
    
    # Get recent stock changes (last 7 days of sales)
    today = datetime.now().date()
    last_7_days = [(today - timedelta(days=i)).strftime('%d %b') for i in range(6, -1, -1)]
    
    # Get low stock medicines
    low_stock_medicines = Medicine.query.filter(
        Medicine.quantity <= Medicine.reorder_level
    ).order_by(Medicine.quantity).limit(5).all()
    
    # Get expiring soon medicines (next 30 days)
    expiring_soon = Medicine.query.filter(
        Medicine.expiry_date.between(today, today + timedelta(days=30))
    ).order_by(Medicine.expiry_date).limit(5).all()
    
    # Get category distribution
    categories = db.session.query(
        Medicine.category, 
        db.func.count(Medicine.id)
    ).group_by(Medicine.category).all()
    
    # Monthly revenue (current month sales)
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    monthly_revenue = db.session.query(
        db.func.sum(Sale.total_amount)
    ).filter(Sale.sale_date >= current_month_start).scalar() or 0
    
    return render_template('dashboard.html',
                         total_medicines=total_medicines,
                         low_stock_count=low_stock_count,
                         expired_count=expired_count,
                         monthly_revenue=monthly_revenue,
                         low_stock_medicines=low_stock_medicines,
                         expiring_soon=expiring_soon,
                         categories=categories,
                         last_7_days=last_7_days)

@app.route('/inventory')
@login_required
def inventory():
    # Get filter parameters
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    stock_status = request.args.get('stock', '')
    sort = request.args.get('sort', 'name')
    
    # Build query
    query = Medicine.query
    
    if search:
        query = query.filter(
            (Medicine.name.contains(search)) | 
            (Medicine.generic_name.contains(search)) |
            (Medicine.manufacturer.contains(search))
        )
    
    if category and category != 'all':
        query = query.filter(Medicine.category == category)
    
    if stock_status == 'low':
        query = query.filter(Medicine.quantity <= Medicine.reorder_level)
    elif stock_status == 'out':
        query = query.filter(Medicine.quantity == 0)
    elif stock_status == 'expired':
        query = query.filter(Medicine.expiry_date < datetime.now().date())
    
    # Apply sorting
    if sort == 'name':
        query = query.order_by(Medicine.name)
    elif sort == 'quantity':
        query = query.order_by(Medicine.quantity.desc())
    elif sort == 'expiry':
        query = query.order_by(Medicine.expiry_date)
    elif sort == 'price':
        query = query.order_by(Medicine.price.desc())
    
    medicines = query.all()
    
    # Get all categories for filter
    categories = db.session.query(Medicine.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]
    
    return render_template('inventory.html', 
                         medicines=medicines, 
                         categories=categories,
                         search=search,
                         selected_category=category,
                         stock_status=stock_status,
                         sort=sort)

@app.route('/medicine/<int:id>')
@login_required
def medicine_details(id):
    medicine = Medicine.query.get_or_404(id)
    
    # Get recent purchase orders for this medicine
    recent_purchases = PurchaseOrder.query.filter_by(medicine_id=id).order_by(
        PurchaseOrder.order_date.desc()
    ).limit(5).all()
    
    # Get recent sales for this medicine
    recent_sales = Sale.query.filter_by(medicine_id=id).order_by(
        Sale.sale_date.desc()
    ).limit(5).all()
    
    return render_template('medicine_details.html', 
                         medicine=medicine,
                         recent_purchases=recent_purchases,
                         recent_sales=recent_sales)

@app.route('/medicine/add', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        try:
            expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date() if request.form.get('expiry_date') else None
            
            medicine = Medicine(
                name=request.form.get('name'),
                generic_name=request.form.get('generic_name'),
                category=request.form.get('category'),
                manufacturer=request.form.get('manufacturer'),
                quantity=int(request.form.get('quantity', 0)),
                price=float(request.form.get('price')),
                expiry_date=expiry_date,
                batch_number=request.form.get('batch_number'),
                description=request.form.get('description'),
                location=request.form.get('location'),
                reorder_level=int(request.form.get('reorder_level', 10))
            )
            
            db.session.add(medicine)
            db.session.commit()
            
            flash('Medicine added successfully!', 'success')
            return redirect(url_for('inventory')) # Goes back to list after saving
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    return render_template('add_medicine.html')

@app.route('/medicine/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            medicine.name = request.form.get('name')
            medicine.generic_name = request.form.get('generic_name')
            medicine.category = request.form.get('category')
            medicine.manufacturer = request.form.get('manufacturer')
            medicine.quantity = int(request.form.get('quantity', 0))
            medicine.price = float(request.form.get('price'))
            medicine.batch_number = request.form.get('batch_number')
            medicine.description = request.form.get('description')
            medicine.location = request.form.get('location')
            medicine.reorder_level = int(request.form.get('reorder_level', 10))
            
            if request.form.get('expiry_date'):
                medicine.expiry_date = datetime.strptime(request.form.get('expiry_date'), '%Y-%m-%d').date()
            
            medicine.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Medicine updated successfully!', 'success')
            return redirect(url_for('medicine_details', id=id))
        except Exception as e:
            flash(f'Error updating medicine: {str(e)}', 'error')
    
    return render_template('edit_medicine.html', medicine=medicine)

@app.route('/medicine/<int:id>/delete', methods=['POST'])
@login_required
def delete_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    try:
        db.session.delete(medicine)
        db.session.commit()
        flash('Medicine deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting medicine: {str(e)}', 'error')
    return redirect(url_for('inventory'))

@app.route('/purchase-orders')
@login_required
def purchase_orders():
    status_filter = request.args.get('status', '')
    
    query = PurchaseOrder.query
    
    if status_filter and status_filter != 'all':
        query = query.filter(PurchaseOrder.status == status_filter)
    
    orders = query.order_by(PurchaseOrder.order_date.desc()).all()
    suppliers = Supplier.query.all()
    medicines = Medicine.query.all()
    
    return render_template('purchase_orders.html', 
                         orders=orders, 
                         suppliers=suppliers,
                         medicines=medicines,
                         status_filter=status_filter)

@app.route('/purchase-order/add', methods=['POST'])
@login_required
def add_purchase_order():
    try:
        supplier_id = int(request.form.get('supplier_id'))
        medicine_id = int(request.form.get('medicine_id'))
        quantity = int(request.form.get('quantity'))
        unit_price = float(request.form.get('unit_price'))
        total_amount = quantity * unit_price
        
        order = PurchaseOrder(
            supplier_id=supplier_id,
            medicine_id=medicine_id,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            notes=request.form.get('notes')
        )
        
        db.session.add(order)
        db.session.commit()
        
        flash('Purchase order created successfully!', 'success')
    except Exception as e:
        flash(f'Error creating purchase order: {str(e)}', 'error')
    
    return redirect(url_for('purchase_orders'))

@app.route('/purchase-order/<int:id>/complete', methods=['POST'])
@login_required
def complete_purchase_order(id):
    order = PurchaseOrder.query.get_or_404(id)
    
    try:
        # Update order status
        order.status = 'completed'
        order.delivery_date = datetime.utcnow()
        
        # Update medicine quantity
        medicine = Medicine.query.get(order.medicine_id)
        medicine.quantity += order.quantity
        medicine.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Purchase order completed and stock updated!', 'success')
    except Exception as e:
        flash(f'Error completing purchase order: {str(e)}', 'error')
    
    return redirect(url_for('purchase_orders'))

@app.route('/purchase-order/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_purchase_order(id):
    order = PurchaseOrder.query.get_or_404(id)
    
    try:
        order.status = 'cancelled'
        db.session.commit()
        flash('Purchase order cancelled!', 'success')
    except Exception as e:
        flash(f'Error cancelling purchase order: {str(e)}', 'error')
    
    return redirect(url_for('purchase_orders'))

@app.route('/suppliers')
@login_required
def suppliers():
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact_person')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        
        new_supplier = Supplier(
            name=name,
            contact_person=contact,
            phone=phone,
            email=email,
            address=address
        )
        
        db.session.add(new_supplier)
        db.session.commit()
        flash('Supplier added successfully!', 'success')
        return redirect(url_for('suppliers'))
        
    return render_template('add_supplier.html')
@app.route('/reports')
@login_required
def reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    
    # 1. Total Sales Revenue
    total_sales = db.session.query(db.func.sum(Sale.total_amount))\
        .filter(Sale.sale_date >= start, Sale.sale_date <= end).scalar() or 0
    
    # 2. Count total number of sales
    sales_count = Sale.query.filter(Sale.sale_date >= start, Sale.sale_date <= end).count()
    
    # 3. Top 10 Selling Medicines
    # We use .group_by(Medicine.id) to be more precise
    top_medicines = db.session.query(
        Medicine.name,
        db.func.sum(Sale.quantity),
        db.func.sum(Sale.total_amount)
    ).join(Sale, Medicine.id == Sale.medicine_id)\
     .filter(Sale.sale_date >= start, Sale.sale_date <= end)\
     .group_by(Medicine.id)\
     .order_by(db.func.sum(Sale.quantity).desc()).limit(10).all()

    # 4. Calculate Current Stock Value
    # FIXED: We pull the data first, then do the math in Python to avoid OperationalError
    inventory_items = db.session.query(Medicine.quantity, Medicine.price).all()
    stock_value = sum(item.quantity * item.price for item in inventory_items)
    
    return render_template('reports.html', 
                           start_date=start_date, 
                           end_date=end_date,
                           total_sales=total_sales, 
                           sales_count=sales_count,
                           top_medicines=top_medicines, 
                           stock_value=stock_value)

@app.route('/sales')
@login_required
def sales_orders():
    # Fetch all sales joined with medicine names
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('sales_orders.html', sales=sales)

@app.route('/sales/new', methods=['GET', 'POST'])
@login_required
def new_sales_order():
    if request.method == 'POST':
        try:
            med_id = int(request.form.get('medicine_id'))
            qty = int(request.form.get('quantity'))
            
            medicine = Medicine.query.get(med_id)
            
            if medicine.quantity < qty:
                flash(f'Insufficient stock! Only {medicine.quantity} left.', 'error')
                return redirect(url_for('new_sales_order'))

            # Process the Sale
            total = qty * medicine.price
            
            # Create the sale record (This drives your Revenue up)
            order = Sale(
                medicine_id=med_id,
                quantity=qty,
                unit_price=medicine.price,
                total_amount=total,
                customer_name=request.form.get('customer_name')
            )
            
            # Deduct from Inventory
            medicine.quantity -= qty
            
            db.session.add(order)
            db.session.commit()
            
            flash('Sales order completed! Revenue updated.', 'success')
            return redirect(url_for('sales_orders'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing order: {str(e)}', 'error')

    # GET: Show the form to create an order
    medicines = Medicine.query.filter(Medicine.quantity > 0).all()
    return render_template('add_sales_order.html', medicines=medicines)

@app.route('/reports/download')
@login_required
def download_report():
    # 1. Get dates from URL
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Fallback to last 30 days if dates are missing
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)

    # 2. Gather Data for the Report
    # CREDITS: All Sales in period
    sales = Sale.query.filter(Sale.sale_date >= start, Sale.sale_date <= end).all()
    total_credit = sum(s.total_amount for s in sales) or 0

    # DEBITS: All Completed Purchases in period
    # Change 'PurchaseOrder' to match your model name if different
    purchases = PurchaseOrder.query.filter(
        PurchaseOrder.order_date >= start, 
        PurchaseOrder.order_date <= end,
        PurchaseOrder.status == 'completed'
    ).all()
    total_debit = sum(p.total_amount for p in purchases) or 0

    # Summary
    net_balance = total_credit - total_debit

    # 3. Render HTML for PDF
    # This uses a specific template designed for PDF layouts
    rendered = render_template('pdf_report.html', 
                               sales=sales, 
                               purchases=purchases,
                               total_credit=total_credit,
                               total_debit=total_debit,
                               net_balance=net_balance,
                               start_date=start_date,
                               end_date=end_date)

    # 4. Generate PDF in Memory
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(rendered, dest=pdf_buffer)

    if pisa_status.err:
        return f"Error generating PDF: {pisa_status.err}", 500

    # 5. Prepare Response
    pdf_buffer.seek(0)
    response = make_response(pdf_buffer.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=PharmaSync_Report_{start_date}.pdf'
    
    return response
# ==================== INITIALIZATION ====================

def init_db():
    with app.app_context():
        # This creates the .db file and tables if they don't exist
        db.create_all()
        
        # We keep the default admin check so you can actually log in 
        # to the dashboard to start adding your own data.
        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@pharmasync.com',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Database initialized. Default admin created: admin@pharmasync.com / admin123")
        else:
            print("Database already exists. No sample data added.")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
