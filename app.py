"""
Flask Application for "Echoes of Music by Tanu Harode"
Contains database models, frontend routes, form handling, and a simple dashboard for checking submissions.
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Security configuration (Secret key is required for session-based Flash messages)
app.config['SECRET_KEY'] = 'echoes_of_music_tanu_harode_secret_key_2026'

# Database configuration (support PostgreSQL via env vars or SQLite fallback)
postgres_url = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
if postgres_url:
    # SQLAlchemy requires 'postgresql://' instead of 'postgres://'
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
else:
    import shutil
    import tempfile
    # Check if running in Vercel serverless environment
    if os.environ.get('VERCEL'):
        db_path = os.path.join(tempfile.gettempdir(), 'database.db')
        local_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
        # Copy the pre-existing database to temp if it exists and hasn't been copied yet
        if os.path.exists(local_db_path) and not os.path.exists(db_path):
            try:
                shutil.copy2(local_db_path, db_path)
            except Exception as e:
                print(f"Error copying database to temp: {e}")
    else:
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==============================================================================
# DATABASE MODELS
# ==============================================================================

class ContactMessage(db.Model):
    """
    Database model to store messages sent via the contact form.
    """
    __tablename__ = 'contact_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContactMessage {self.name} - {self.email}>'


class BookingRequest(db.Model):
    """
    Database model to store class and live performance booking requests.
    """
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    booking_type = db.Column(db.String(50), nullable=False)  # 'Class' or 'Show'
    event_name = db.Column(db.String(100), nullable=False)  # Name of the class or show
    preferred_date = db.Column(db.String(50), nullable=False)  # Preferred date/time (stored as string for flexible scheduling)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<BookingRequest {self.name} - {self.booking_type} ({self.event_name})>'


class SiteSetting(db.Model):
    """
    Database model to store key-value configurations for the site (e.g., contact info, social links, class timings).
    """
    __tablename__ = 'site_settings'
    
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<SiteSetting {self.key}: {self.value}>'


# ==============================================================================
# ROUTES & CONTROLLERS
# ==============================================================================

@app.route('/')
def index():
    """
    Home page. Renders standard dashboard with quick highlights.
    """
    return render_template('index.html', title="Home")


@app.route('/about')
def about():
    """
    About page containing Tanu Harode's credentials, qualifications and bio.
    """
    return render_template('about.html', title="About Tanu")


@app.route('/classes')
def classes():
    """
    Classes page detailing Vocal and Ghazal classes, scheduling and price cards.
    """
    return render_template('classes.html', title="Music Classes")


@app.route('/shows')
def shows():
    """
    Curated performance profiles page. Shows pricing, duration, suitability.
    """
    return render_template('shows.html', title="Live Performance Shows")


@app.route('/gallery')
def gallery():
    """
    Performance gallery grid page. Integrates JavaScript lightbox viewer.
    """
    return render_template('gallery.html', title="Media Gallery")


@app.route('/contact')
def contact():
    """
    Contact page displaying address, map hooks and active message/booking forms.
    """
    return render_template('contact.html', title="Contact & Bookings")


# ==============================================================================
# API ENDPOINTS & FORM SUBMISSIONS
# ==============================================================================

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    """
    Handle contact form submissions.
    Saves details in SQLite database and notifies user via Flash message.
    """
    try:
        # Check if requested as JSON or typical Form Post
        is_json = request.is_json
        
        if is_json:
            data = request.get_json()
            name = data.get('name')
            email = data.get('email')
            message = data.get('message')
        else:
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')
            
        # Basic validation
        if not name or not email or not message:
            error_msg = "Please fill out all fields."
            if is_json:
                return jsonify({"status": "error", "message": error_msg}), 400
            flash(error_msg, "error")
            return redirect(url_for('contact'))
            
        # Create DB record
        new_msg = ContactMessage(name=name, email=email, message=message)
        db.session.add(new_msg)
        db.session.commit()
        
        success_msg = f"Thank you, {name}! Your message has been sent successfully. We will get back to you shortly."
        if is_json:
            return jsonify({"status": "success", "message": success_msg})
        flash(success_msg, "success")
        return redirect(url_for('contact'))
        
    except Exception as e:
        db.session.rollback()
        err_msg = f"An error occurred while saving your message: {str(e)}"
        if request.is_json:
            return jsonify({"status": "error", "message": err_msg}), 500
        flash(err_msg, "error")
        return redirect(url_for('contact'))


@app.route('/api/book', methods=['POST'])
def submit_booking():
    """
    Handle booking requests (for classes and shows).
    Saves details in database and sets flash messages.
    """
    try:
        is_json = request.is_json
        
        if is_json:
            data = request.get_json()
            name = data.get('name')
            phone = data.get('phone')
            email = data.get('email')
            booking_type = data.get('booking_type')  # 'Class' or 'Show'
            event_name = data.get('event_name')
            preferred_date = data.get('preferred_date')
            message = data.get('message', '')
        else:
            name = request.form.get('name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            booking_type = request.form.get('booking_type')
            event_name = request.form.get('event_name')
            preferred_date = request.form.get('preferred_date')
            message = request.form.get('message', '')
            
        # Basic Validation
        if not name or not phone or not booking_type or not event_name or not preferred_date:
            error_msg = "Please fill out all required fields: Name, Phone, Type, Selection, and Date."
            if is_json:
                return jsonify({"status": "error", "message": error_msg}), 400
            flash(error_msg, "error")
            return redirect(url_for('contact'))
            
        # Create DB record
        new_booking = BookingRequest(
            name=name,
            phone=phone,
            email=email,
            booking_type=booking_type,
            event_name=event_name,
            preferred_date=preferred_date,
            message=message
        )
        db.session.add(new_booking)
        db.session.commit()
        
        success_msg = f"Dear {name}, your booking request for the {booking_type} '{event_name}' on {preferred_date} has been submitted! We will contact you at {phone} to finalize the arrangements."
        if is_json:
            return jsonify({"status": "success", "message": success_msg})
        
        flash(success_msg, "success")
        # If user submits from standard pages, redirect back to referrer if possible or to contact
        return redirect(request.referrer or url_for('contact'))
        
    except Exception as e:
        db.session.rollback()
        err_msg = f"An error occurred while placing your booking: {str(e)}"
        if request.is_json:
            return jsonify({"status": "error", "message": err_msg}), 500
        flash(err_msg, "error")
        return redirect(url_for('contact'))


# ==============================================================================
# ADMIN VIEW (FOR EASY VERIFICATION OF FORM ENTRIES)
# ==============================================================================

@app.context_processor
def inject_site_settings():
    """
    Injects site settings dynamically into all templates.
    """
    defaults = {
        'phone': '+91 62613 16204',
        'whatsapp': '916261316204',
        'email': 'tanuharode6@gmail.com',
        'address': 'H.N.-9, Indraprasth Colony, Hinotiya Chandbad, Bhopal - 462010',
        'classes_timing': 'Classes: Mon - Sat (4:00 PM - 8:00 PM)',
        'individual_classes_timing': 'By Appointment (4:00 PM - 8:00 PM)',
        'instagram': 'https://www.instagram.com/tanuharode22?igsh=ZWw2ZGU0YnZtaHE0&utm_source=qr',
        'youtube': 'https://youtube.com/@tanusinger4291?si=TycISPb_y-fcl17v',
        'facebook': 'https://facebook.com',
        'bio_brief': 'Tanu Harode is a distinguished vocalist and educator who has spent over two decades cultivating the classical and semi-classical music traditions of India.',
        'bio_specializations': 'Ghazals, Light Music, Voice Culture, Bollywood Music, Riyaz Sessions, Karaoke Music, Ornamentation, Stage Performance, Raga Improvisation'
    }
    
    settings = {}
    try:
        db_settings = SiteSetting.query.all()
        settings = {s.key: s.value for s in db_settings}
    except Exception as e:
        print(f"Error loading settings from DB: {e}")
        
    final_settings = {}
    for key, def_val in defaults.items():
        final_settings[key] = settings.get(key, def_val)
        
    return dict(site_settings=final_settings)


@app.route('/admin/dashboard')
def admin_dashboard():
    """
    A simple backend review console for checking database integrity.
    Displays all submitted contact queries and booking entries.
    """
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    bookings = BookingRequest.query.order_by(BookingRequest.created_at.desc()).all()
    return render_template('admin.html', messages=messages, bookings=bookings, title="Admin Dashboard")


@app.route('/admin/settings', methods=['POST'])
def update_settings():
    """
    Handle update of site settings from the admin dashboard.
    """
    try:
        keys = [
            'phone', 'whatsapp', 'email', 'address', 'classes_timing', 
            'individual_classes_timing', 'instagram', 'youtube', 'facebook', 
            'bio_brief', 'bio_specializations'
        ]
        
        for key in keys:
            val = request.form.get(key)
            if val is not None:
                setting = db.session.get(SiteSetting, key)
                if not setting:
                    setting = SiteSetting(key=key, value=val)
                    db.session.add(setting)
                else:
                    setting.value = val
                    
        db.session.commit()
        flash("Site settings updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while updating settings: {str(e)}", "error")
        
    return redirect(url_for('admin_dashboard'))


# ==============================================================================
# DATABASE INITIALIZATION & RUN
# ==============================================================================

# Create database tables inside app context
with app.app_context():
    db.create_all()
    
    # Seed default site settings if empty
    try:
        defaults = {
            'phone': '+91 62613 16204',
            'whatsapp': '916261316204',
            'email': 'tanuharode6@gmail.com',
            'address': 'H.N.-9, Indraprasth Colony, Hinotiya Chandbad, Bhopal - 462010',
            'classes_timing': 'Classes: Mon - Sat (4:00 PM - 8:00 PM)',
            'individual_classes_timing': 'By Appointment (4:00 PM - 8:00 PM)',
            'instagram': 'https://www.instagram.com/tanuharode22?igsh=ZWw2ZGU0YnZtaHE0&utm_source=qr',
            'youtube': 'https://youtube.com/@tanusinger4291?si=TycISPb_y-fcl17v',
            'facebook': 'https://facebook.com',
            'bio_brief': 'Tanu Harode is a distinguished vocalist and educator who has spent over two decades cultivating the classical and semi-classical music traditions of India.',
            'bio_specializations': 'Ghazals, Light Music, Voice Culture, Bollywood Music, Riyaz Sessions, Karaoke Music, Ornamentation, Stage Performance, Raga Improvisation'
        }
        for key, value in defaults.items():
            setting = db.session.get(SiteSetting, key)
            if not setting:
                db.session.add(SiteSetting(key=key, value=value))
        db.session.commit()
    except Exception as e:
        print(f"Error seeding default settings: {e}")

if __name__ == '__main__':
    # Run the server on port 5000 in debug mode
    app.run(debug=True, host='0.0.0.0', port=5000)
