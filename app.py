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

# SQLite Database path configuration
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

@app.route('/admin/dashboard')
def admin_dashboard():
    """
    A simple backend review console for checking database integrity.
    Displays all submitted contact queries and booking entries.
    """
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    bookings = BookingRequest.query.order_by(BookingRequest.created_at.desc()).all()
    return render_template('admin.html', messages=messages, bookings=bookings, title="Admin Dashboard")


# ==============================================================================
# DATABASE INITIALIZATION & RUN
# ==============================================================================

# Create database tables inside app context
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Run the server on port 5000 in debug mode
    app.run(debug=True, host='0.0.0.0', port=5000)
