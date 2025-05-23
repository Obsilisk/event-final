from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # Set your MySQL password here
    'database': 'event_mang'
}

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'events')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM events WHERE date >= CURDATE() ORDER BY date ASC LIMIT 3")
    events = cursor.fetchall()
    
    for event in events:
        cursor.execute("SELECT * FROM ticket_types WHERE event_id = %s", (event['event_id'],))
        event['ticket_types'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('index.html', events=events)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        phone = request.form.get('phone', '')
        
        hashed_password = generate_password_hash(password)
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password, full_name, phone) VALUES (%s, %s, %s, %s, %s)",
                (username, email, hashed_password, full_name, phone)
            )
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash('Username or email already exists!', 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['user_type'] = 'user'
            flash('Login successful!', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('auth/login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM admin WHERE username = %s", (username,))
        admin = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['admin_id']
            session['username'] = admin['username']
            session['user_type'] = 'admin'
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password!', 'danger')
    
    return render_template('auth/login.html', admin=True)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM events ORDER BY date DESC")
    events = cursor.fetchall()
    
    cursor.execute("SELECT COUNT(*) as total FROM user_events")
    total_registrations = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as upcoming FROM events WHERE date >= CURDATE()")
    upcoming_events = cursor.fetchone()['upcoming']
    
    cursor.close()
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         events=events, 
                         total_registrations=total_registrations,
                         upcoming_events=upcoming_events)

@app.route('/admin/events/add', methods=['GET', 'POST'])
@admin_required
def add_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        time = request.form['time']
        location = request.form['location']
        
        image = request.files['image']
        image_url = ''
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            image_url = filename
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO events (title, description, date, time, location, image_url) VALUES (%s, %s, %s, %s, %s, %s)",
                (title, description, date, time, location, image_url)
            )
            event_id = cursor.lastrowid
            
            ticket_types = request.form.getlist('ticket_name[]')
            ticket_prices = request.form.getlist('ticket_price[]')
            ticket_quantities = request.form.getlist('ticket_quantity[]')
            
            for name, price, quantity in zip(ticket_types, ticket_prices, ticket_quantities):
                if name and price and quantity:
                    cursor.execute(
                        "INSERT INTO ticket_types (event_id, name, price, quantity) VALUES (%s, %s, %s, %s)",
                        (event_id, name, float(price), int(quantity))
                    )
            
            conn.commit()
            flash('Event added successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except mysql.connector.Error as err:
            conn.rollback()
            flash('Error adding event: ' + str(err), 'danger')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('admin/add_event.html')

@app.route('/admin/events/manage')
@admin_required
def manage_events():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT e.*, COUNT(ue.registration_id) as registrations
        FROM events e
        LEFT JOIN user_events ue ON e.event_id = ue.event_id
        GROUP BY e.event_id
        ORDER BY e.date DESC
    """)
    events = cursor.fetchall()
        
    cursor.close()
    conn.close()
    return render_template('admin/manage_events.html', events=events)

@app.route('/admin/events/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
        conn.commit()
        flash('Event deleted successfully!', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash('Error deleting event: ' + str(err), 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('manage_events'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT e.*, ue.registration_date, tt.name as ticket_type, tt.price, ue.quantity
        FROM user_events ue
        JOIN events e ON ue.event_id = e.event_id
        JOIN ticket_types tt ON ue.ticket_type_id = tt.ticket_type_id
        WHERE ue.user_id = %s AND e.date >= CURDATE()
        ORDER BY e.date ASC
    """, (session['user_id'],))
    upcoming_events = cursor.fetchall()
    
    cursor.execute("SELECT * FROM events WHERE date >= CURDATE() ORDER BY date ASC")
    all_events = cursor.fetchall()
    
    for event in all_events:
        cursor.execute("SELECT * FROM ticket_types WHERE event_id = %s", (event['event_id'],))
        event['ticket_types'] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('user/dashboard.html', upcoming_events=upcoming_events, all_events=all_events)

@app.route('/events/register/<int:event_id>', methods=['GET', 'POST'])
@login_required
def register_event(event_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get event details
        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found!', 'danger')
            return redirect(url_for('user_dashboard'))
        
        if request.method == 'POST':
            ticket_type_id = request.form.get('ticket_type')
            quantity = int(request.form.get('quantity', 1))
            
            # Verify ticket availability
            cursor.execute("""
                SELECT * FROM ticket_types 
                WHERE ticket_type_id = %s AND quantity >= %s
            """, (ticket_type_id, quantity))
            ticket = cursor.fetchone()
            
            if not ticket:
                flash('Selected tickets are not available!', 'danger')
                return redirect(url_for('register_event', event_id=event_id))
            
            # Create registration
            cursor.execute("""
                INSERT INTO user_events (user_id, event_id, ticket_type_id, quantity) 
                VALUES (%s, %s, %s, %s)
            """, (session['user_id'], event_id, ticket_type_id, quantity))
            registration_id = cursor.lastrowid
            
            # Update ticket quantity
            cursor.execute("""
                UPDATE ticket_types 
                SET quantity = quantity - %s 
                WHERE ticket_type_id = %s
            """, (quantity, ticket_type_id))
            
            # Create payment record
            total_amount = ticket['price'] * quantity
            cursor.execute("""
                INSERT INTO payments (registration_id, amount, status) 
                VALUES (%s, %s, 'completed')
            """, (registration_id, total_amount))
            
            conn.commit()
            flash('Successfully registered for the event!', 'success')
            return redirect(url_for('my_events'))
        
        # Get available ticket types for the event
        cursor.execute("""
            SELECT * FROM ticket_types 
            WHERE event_id = %s AND quantity > 0
        """, (event_id,))
        ticket_types = cursor.fetchall()
        
        return render_template('user/events.html', 
                            event=event, 
                            ticket_types=ticket_types)
                            
    except mysql.connector.Error as err:
        conn.rollback()
        flash(f'Database error: {str(err)}', 'danger')
        return redirect(url_for('user_dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/user/events')
@login_required
def my_events():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT e.*, e.image_url, ue.registration_date, tt.name as ticket_type, tt.price, ue.quantity, p.status
        FROM user_events ue
        JOIN events e ON ue.event_id = e.event_id
        JOIN ticket_types tt ON ue.ticket_type_id = tt.ticket_type_id
        LEFT JOIN payments p ON ue.registration_id = p.registration_id
        WHERE ue.user_id = %s
        ORDER BY e.date DESC
    """, (session['user_id'],))
    registrations = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('user/my_events.html', registrations=registrations)

@app.route('/user/events/cancel/<int:registration_id>', methods=['POST'])
@login_required
def cancel_registration(registration_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT ue.*, tt.ticket_type_id, tt.event_id
            FROM user_events ue
            JOIN ticket_types tt ON ue.ticket_type_id = tt.ticket_type_id
            WHERE ue.registration_id = %s AND ue.user_id = %s
        """, (registration_id, session['user_id']))
        registration = cursor.fetchone()
                
        if not registration:
            flash('Registration not found!', 'danger')
            return redirect(url_for('my_events'))
        
        cursor.execute(
            "UPDATE ticket_types SET quantity = quantity + %s WHERE ticket_type_id = %s",
            (registration['quantity'], registration['ticket_type_id'])
        )
        
        cursor.execute("DELETE FROM user_events WHERE registration_id = %s", (registration_id,))
        cursor.execute("DELETE FROM payments WHERE registration_id = %s", (registration_id,))
        
        conn.commit()
        flash('Registration canceled successfully!', 'success')
    except mysql.connector.Error as err:
        conn.rollback()
        flash('Error canceling registration: ' + str(err), 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('my_events'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Temporary admin creation route (REMOVE AFTER USE)
@app.route('/create-admin')
def create_admin():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    hashed_pw = generate_password_hash('admin123')
    
    try:
        cursor.execute("DELETE FROM admin")
        cursor.execute(
            "INSERT INTO admin (username, password, email) VALUES (%s, %s, %s)",
            ('admin', hashed_pw, 'admin@example.com')
        )
        conn.commit()
        return "Admin created: username=admin, password=admin123"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()

@app.route('/reset-admin', methods=['GET'])
def reset_admin():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Create a new hashed password for 'admin123'
    hashed_password = generate_password_hash('admin123')
    
    try:
        cursor.execute("UPDATE admin SET password = %s WHERE username = 'admin'", (hashed_password,))
        conn.commit()
        flash('Admin password reset successful!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('admin_login'))

@app.route('/setup-admin-account')
def setup_admin_account():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Create new admin with simple password hash
        cursor.execute("DELETE FROM admin")
        password = 'admin123'
        hashed_password = generate_password_hash(password)
        
        cursor.execute(
            "INSERT INTO admin (username, password, email) VALUES (%s, %s, %s)",
            ('admin', hashed_password, 'admin@example.com')
        )
        conn.commit()
        return "Admin account created. Username: admin, Password: admin123"
    except mysql.connector.Error as err:
        return f"Error: {err}"
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)