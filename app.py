"""
Flask Application for "Echoes of Music by Tanu Harode"
Contains database models, frontend routes, form handling, and a simple dashboard for checking submissions.
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)

# Security configuration (Secret key is required for session-based Flash messages)
app.config['SECRET_KEY'] = 'echoes_of_music_tanu_harode_secret_key_2026'

# Configure local upload directory (used as fallback when Cloudinary is not configured)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# ==============================================================================
# CLOUDINARY CONFIGURATION (for permanent image storage on Vercel)
# Set CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME + CLOUDINARY_API_KEY +
# CLOUDINARY_API_SECRET in your Vercel environment variables.
# ==============================================================================
try:
    import cloudinary
    import cloudinary.uploader
    _cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
    _api_key    = os.environ.get('CLOUDINARY_API_KEY')
    _api_secret = os.environ.get('CLOUDINARY_API_SECRET')
    _cloud_url  = os.environ.get('CLOUDINARY_URL')  # alternative: full URL form
    if _cloud_url or (_cloud_name and _api_key and _api_secret):
        cloudinary.config(
            cloud_name = _cloud_name,
            api_key    = _api_key,
            api_secret = _api_secret,
        )
        CLOUDINARY_ENABLED = True
        print("[INFO] Cloudinary configured — uploads will be stored permanently on Cloudinary CDN.")
    else:
        CLOUDINARY_ENABLED = False
        print("[INFO] Cloudinary not configured — falling back to local file storage.")
except ImportError:
    CLOUDINARY_ENABLED = False
    print("[WARNING] cloudinary package not installed. Run: pip install cloudinary")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Please log in to access this page.", "error")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

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


class GalleryImage(db.Model):
    """
    Database model to store gallery images dynamically.
    """
    __tablename__ = 'gallery_images'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    alt_text = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False)  # concerts, classes, mehfils
    date_text = db.Column(db.String(100), nullable=True)  # e.g., "Bhopal - Oct 2025"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<GalleryImage {self.title} ({self.category})>'


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
    Loads dynamic images from the database.
    """
    images = GalleryImage.query.order_by(GalleryImage.created_at.desc()).all()
    return render_template('gallery.html', title="Media Gallery", images=images)


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
    Also exposes Cloudinary status so templates can show the correct storage mode.
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
        'bio_brief': 'Tanu Harode is a distinguished vocalist and educator with 6+ years of experience cultivating the classical and semi-classical music traditions of India.',
        'bio_specializations': 'Ghazals, Light Music, Voice Culture, Bollywood Music, Riyaz Sessions, Karaoke Music, Ornamentation, Stage Performance, Raga Improvisation',
        # Class Prices
        'price_group_classes': '3,500',
        'price_individual_classes': '7,000',
        'price_single_session': '1,200',
        'price_quarterly_pack': '9,500',
        'price_quarterly_pack_note': 'Save ₹1000',
        # Show / Concert Prices
        'price_show_ghazal_india': '25,000',
        'price_show_ghazal_intl': 'Custom Quote',
        'price_show_bollywood_india': '30,000',
        'price_show_bollywood_intl': 'Custom Quote',
        'price_show_light_india': '20,000',
        'price_show_light_intl': 'Custom Quote',
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

    # Expose Cloudinary status for templates
    cloudinary_status = 'active' if CLOUDINARY_ENABLED else 'local'
        
    return dict(site_settings=final_settings, cloudinary_status=cloudinary_status)


@app.route('/admin')
def admin_redirect():
    """Redirect to the admin dashboard (will trigger login if not authenticated)."""
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """
    Renders login screen and handles credentials verification.
    """
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verify credentials
        expected_password = os.environ.get('ADMIN_PASSWORD', 'tanu@123')
        if username == 'admin' and password == expected_password:
            session['admin_logged_in'] = True
            flash("Welcome to the Admin Dashboard!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid username or password. Please try again.", "error")
            
    return render_template('login.html', title="Admin Login")


@app.route('/admin/logout')
def admin_logout():
    """Logs out the admin user."""
    session.pop('admin_logged_in', None)
    flash("You have logged out successfully.", "success")
    return redirect(url_for('index'))


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """
    A simple backend review console for checking database integrity.
    Displays all submitted contact queries, booking entries, and gallery images.
    """
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    bookings = BookingRequest.query.order_by(BookingRequest.created_at.desc()).all()
    images = GalleryImage.query.order_by(GalleryImage.created_at.desc()).all()
    return render_template('admin.html', messages=messages, bookings=bookings, images=images, title="Admin Dashboard")


@app.route('/admin/settings', methods=['POST'])
@login_required
def update_settings():
    """
    Handle update of site settings from the admin dashboard.
    """
    try:
        keys = [
            'phone', 'whatsapp', 'email', 'address', 'classes_timing',
            'individual_classes_timing', 'instagram', 'youtube', 'facebook',
            'bio_brief', 'bio_specializations',
            # Class prices
            'price_group_classes', 'price_individual_classes',
            'price_single_session', 'price_quarterly_pack', 'price_quarterly_pack_note',
            # Show / concert prices
            'price_show_ghazal_india', 'price_show_ghazal_intl',
            'price_show_bollywood_india', 'price_show_bollywood_intl',
            'price_show_light_india', 'price_show_light_intl',
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
        flash("Settings updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while updating settings: {str(e)}", "error")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/gallery/add', methods=['POST'])
@login_required
def add_gallery_image():
    """
    Endpoint to add a new image to the gallery database.
    Upload priority:
      1. File upload  -> Cloudinary CDN (permanent) if configured, else local /static/uploads/
      2. External URL -> stored as-is
    """
    try:
        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        alt_text = request.form.get('alt_text', '').strip()
        date_text = request.form.get('date_text', '').strip()
        image_url = request.form.get('image_url', '').strip()

        if not title or not category:
            flash("Title and Category are required.", "error")
            return redirect(url_for('admin_dashboard'))

        file = request.files.get('image_file')
        final_url = ""

        if file and file.filename != '':
            if not allowed_file(file.filename):
                flash("Invalid file type. Allowed: png, jpg, jpeg, gif, webp", "error")
                return redirect(url_for('admin_dashboard'))

            if CLOUDINARY_ENABLED:
                # Upload to Cloudinary — permanent storage, CDN-delivered
                upload_result = cloudinary.uploader.upload(
                    file,
                    folder="ghazal_room_gallery",
                    resource_type="image"
                )
                final_url = upload_result.get('secure_url', '')
            else:
                # Local storage fallback (development only)
                filename = secure_filename(file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                final_url = f"/static/uploads/{filename}"

        elif image_url:
            final_url = image_url
        else:
            flash("Please provide either an Image URL or upload an Image File.", "error")
            return redirect(url_for('admin_dashboard'))

        new_image = GalleryImage(
            url=final_url,
            title=title,
            alt_text=alt_text or title,
            category=category,
            date_text=date_text
        )
        db.session.add(new_image)
        db.session.commit()
        flash(f"Gallery image '{title}' added successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while adding the image: {str(e)}", "error")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/gallery/delete/<int:image_id>', methods=['POST'])
@login_required
def delete_gallery_image(image_id):
    """
    Endpoint to delete an image record from the database.
    Also removes the asset from Cloudinary (if it was uploaded there)
    or from local storage (if it was a local upload).
    """
    try:
        image = db.session.get(GalleryImage, image_id)
        if not image:
            flash("Image not found.", "error")
            return redirect(url_for('admin_dashboard'))

        # Delete from Cloudinary if it's a Cloudinary URL
        if CLOUDINARY_ENABLED and 'res.cloudinary.com' in (image.url or ''):
            try:
                # Extract public_id from Cloudinary URL
                # URL format: https://res.cloudinary.com/<cloud>/image/upload/v123/<folder>/<public_id>.<ext>
                parts = image.url.split('/')
                # public_id is folder/filename_without_extension
                upload_idx = parts.index('upload') if 'upload' in parts else -1
                if upload_idx != -1:
                    # Skip version segment (starts with 'v' followed by digits)
                    after_upload = parts[upload_idx + 1:]
                    if after_upload and after_upload[0].startswith('v') and after_upload[0][1:].isdigit():
                        after_upload = after_upload[1:]
                    public_id_with_ext = '/'.join(after_upload)
                    public_id = public_id_with_ext.rsplit('.', 1)[0]  # strip extension
                    cloudinary.uploader.destroy(public_id)
            except Exception as e:
                print(f"[WARNING] Could not delete from Cloudinary: {e}")

        # Delete local file if it was stored locally
        elif image.url.startswith('/static/uploads/'):
            filename = image.url.split('/')[-1]
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting local file: {e}")

        db.session.delete(image)
        db.session.commit()
        flash("Gallery image deleted successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the image: {str(e)}", "error")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/gallery/edit/<int:image_id>', methods=['POST'])
@login_required
def edit_gallery_image(image_id):
    """
    Endpoint to update an existing gallery image's metadata and optionally
    replace the image with a new file upload (via Cloudinary or local) or URL.
    """
    try:
        image = db.session.get(GalleryImage, image_id)
        if not image:
            flash("Image not found.", "error")
            return redirect(url_for('admin_dashboard'))

        title = request.form.get('title', '').strip()
        category = request.form.get('category', '').strip()
        alt_text = request.form.get('alt_text', '').strip()
        date_text = request.form.get('date_text', '').strip()
        new_image_url = request.form.get('image_url', '').strip()

        if not title or not category:
            flash("Title and Category are required.", "error")
            return redirect(url_for('admin_dashboard'))

        # Update metadata
        image.title = title
        image.category = category
        image.alt_text = alt_text or title
        image.date_text = date_text

        # Replace image if a new file or URL provided
        file = request.files.get('image_file')
        if file and file.filename != '':
            if not allowed_file(file.filename):
                flash("Invalid file type. Allowed: png, jpg, jpeg, gif, webp", "error")
                return redirect(url_for('admin_dashboard'))

            old_url = image.url

            if CLOUDINARY_ENABLED:
                # Upload new image to Cloudinary
                upload_result = cloudinary.uploader.upload(
                    file,
                    folder="ghazal_room_gallery",
                    resource_type="image"
                )
                image.url = upload_result.get('secure_url', '')
                # Delete old Cloudinary asset if applicable
                if 'res.cloudinary.com' in (old_url or ''):
                    try:
                        parts = old_url.split('/')
                        upload_idx = parts.index('upload') if 'upload' in parts else -1
                        if upload_idx != -1:
                            after_upload = parts[upload_idx + 1:]
                            if after_upload and after_upload[0].startswith('v') and after_upload[0][1:].isdigit():
                                after_upload = after_upload[1:]
                            public_id = '/'.join(after_upload).rsplit('.', 1)[0]
                            cloudinary.uploader.destroy(public_id)
                    except Exception as e:
                        print(f"[WARNING] Could not delete old Cloudinary asset: {e}")
            else:
                # Local fallback
                if old_url.startswith('/static/uploads/'):
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_url.split('/')[-1])
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except Exception as e:
                            print(f"Could not delete old local file: {e}")
                filename = secure_filename(file.filename)
                timestamp = int(datetime.utcnow().timestamp())
                filename = f"{timestamp}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                image.url = f"/static/uploads/{filename}"

        elif new_image_url:
            image.url = new_image_url

        db.session.commit()
        flash(f"Gallery image '{title}' updated successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while updating the image: {str(e)}", "error")

    return redirect(url_for('admin_dashboard'))


# ==============================================================================
# DATABASE INITIALIZATION & RUN
# ==============================================================================

# Create database tables inside app context
startup_error = None
try:
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
                'bio_brief': 'Tanu Harode is a distinguished vocalist and educator with 6+ years of experience cultivating the classical and semi-classical music traditions of India.',
                'bio_specializations': 'Ghazals, Light Music, Voice Culture, Bollywood Music, Riyaz Sessions, Karaoke Music, Ornamentation, Stage Performance, Raga Improvisation'
            }
            for key, value in defaults.items():
                setting = db.session.get(SiteSetting, key)
                if not setting:
                    db.session.add(SiteSetting(key=key, value=value))
            db.session.commit()
        except Exception as e:
            print(f"Error seeding default settings: {e}")

        # Seed default gallery images if empty
        try:
            if not GalleryImage.query.first():
                default_images = [
                    {
                        'url': '/static/images/gallery_1.png',
                        'title': 'Concert Hall Performance',
                        'alt_text': 'Live Performance at Concert Hall',
                        'category': 'concerts',
                        'date_text': 'Bhopal - Oct 2025'
                    },
                    {
                        'url': '/static/images/gallery_2.png',
                        'title': 'Classical Voice Practice',
                        'alt_text': 'Vocal Class Session',
                        'category': 'classes',
                        'date_text': 'Studio - Nov 2025'
                    },
                    {
                        'url': '/static/images/gallery_3.png',
                        'title': 'Sham-e-Ghazal Soiree',
                        'alt_text': 'Intimate Sham-e-Ghazal Session',
                        'category': 'mehfils',
                        'date_text': 'Private Lounge - Dec 2025'
                    },
                    {
                        'url': '/static/images/gallery_4.png',
                        'title': 'Stage Setup & Harmonium',
                        'alt_text': 'Accompanist Team on Stage',
                        'category': 'concerts',
                        'date_text': 'Mumbai - Jan 2026'
                    },
                    {
                        'url': '/static/images/gallery_5.png',
                        'title': 'School Choir Training',
                        'alt_text': 'Tanu Harode teaching school students',
                        'category': 'classes',
                        'date_text': "People's International - Feb 2026"
                    },
                    {
                        'url': '/static/images/gallery_6.png',
                        'title': 'Light Classical Mehfil',
                        'alt_text': 'Light Classical Evening Setup',
                        'category': 'mehfils',
                        'date_text': 'Outdoor Lawn - March 2026'
                    }
                ]
                for img_data in default_images:
                    db.session.add(GalleryImage(**img_data))
                db.session.commit()
        except Exception as e:
            print(f"Error seeding default gallery images: {e}")
except Exception as e:
    import traceback
    startup_error = traceback.format_exc()
    print(f"[ERROR] Startup database initialization failed:\n{startup_error}")


@app.before_request
def check_startup_error():
    if startup_error:
        return f"""
        <html>
        <head>
            <title>Application Startup Error</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 40px; background: #fff5f5; color: #900; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-top: 5px solid #d9534f; }}
                h1 {{ font-size: 24px; margin-top: 0; color: #d9534f; }}
                pre {{ background: #f8f8f8; padding: 15px; border-radius: 5px; border: 1px solid #ddd; overflow-x: auto; font-family: monospace; font-size: 14px; color: #333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Application Initialization Failed (500 Internal Server Error)</h1>
                <p>An error occurred while connecting to or initializing the database. This typically happens when the database credentials/URLs are incorrect, the database service is unavailable, or a driver (like psycopg2) has installation issues on this platform.</p>
                <h3>Error Traceback:</h3>
                <pre>{startup_error}</pre>
                <p>Please check your environment variables (like <code>DATABASE_URL</code> or <code>POSTGRES_URL</code>) and configuration.</p>
            </div>
        </body>
        </html>
        """, 500

# -------------------------------------------------
# Misspelling redirects for SEO robustness
# -------------------------------------------------

@app.route('/echoes-of-muzik')
@app.route('/echoes-of-musics')
@app.route('/echoes-of-music')
@app.route('/echoes_of_music')
def redirect_misspell():
    """Redirect common misspelled URLs to the home page."""
    return redirect(url_for('index'), code=301)

if __name__ == '__main__':
    # Run the server on port 5000 in debug mode
    app.run(debug=True, host='0.0.0.0', port=5000)
