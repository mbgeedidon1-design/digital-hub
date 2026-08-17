import os, uuid
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, jsonify
from flask_login import login_user, logout_user, login_required
from werkzeug.utils import secure_filename
from . import db
from .models import Admin, Service, Product, Order, EditJob

main = Blueprint("main", __name__)
ALLOWED = {"png","jpg","jpeg","webp","gif","pdf","zip","mp3","wav","mp4","apk","exe","dmg"}
IMAGE_EXTS = {"png","jpg","jpeg","webp","gif"}

def save_upload(file):
    if not file or not file.filename: return None
    ext = file.filename.rsplit(".",1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED: return None
    name = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], name))
    return name

def seed_services():
    if Service.query.count() == 0:
        items = [
            ("Photo Editing","Professional retouching, background removal, posters and social graphics.","From KSh 200","✦"),
            ("Website & Software","Business websites, landing pages and custom digital tools.","From KSh 2,500","⌘"),
            ("Music & Audio","Audio cleanup, cover art, promo assets and digital music support.","From KSh 500","♫"),
            ("Digital Design","Logos, flyers, banners, thumbnails, invitations and brand graphics.","From KSh 300","◆"),
            ("Digital Products","Templates, graphics, software tools and useful downloads.","Various","⬡")]
        db.session.add_all([Service(name=a,description=b,price=c,icon=d) for a,b,c,d in items]); db.session.commit()

def ai_reply(message):
    """Free built-in Digital Hub assistant (Gimmie)."""
    q = " ".join((message or "").lower().strip().split())

    if not q:
        return "Hi! I'm Gimmie 👋 How can I help you today?"

    if any(x in q for x in ["hello", "hi", "hey", "habari", "mambo", "sasa", "greet"]):
        return ("Hey! 👋 I'm Gimmie, Digital Hub's assistant. "
                "I can help with photo editing, graphics, websites, software, music, "
                "digital products, orders and general questions. What do you need?")

    if any(x in q for x in ["photo", "picture", "pic", "image", "edit", "editing", "background", "retouch"]):
        return ("Yes 📸 We can edit your photos. We can help with background removal, "
                "retouching, social-media graphics and other edits. "
                "Use **Send a Photo** to upload your picture and tell us exactly what you want changed.")

    if any(x in q for x in ["logo", "flyer", "poster", "banner", "thumbnail", "graphic", "design", "invitation"]):
        return ("🎨 Digital Hub offers logo and graphic design, including flyers, posters, "
                "banners, thumbnails and invitations. Tell us what you want designed and "
                "we can help you start an order.")

    if any(x in q for x in ["website", "web site", "software", "app", "application", "coding", "developer"]):
        return ("💻 We build websites and custom digital software. "
                "For a quote, tell us what the website or software should do, "
                "who will use it, and any important features you need.")

    if any(x in q for x in ["music", "audio", "song", "sound", "cover art", "podcast"]):
        return ("🎵 We offer music and audio-related digital services, including audio cleanup, "
                "cover art and promotional assets. Tell us what you need and we'll guide you.")

    if any(x in q for x in ["price", "cost", "how much", "charge", "fee", "rates", "pricing"]):
        return ("💰 Our listed starting prices include photo editing from KSh 200, "
                "digital design from KSh 300, music/audio from KSh 500, "
                "and websites/software from KSh 2,500. "
                "The final price depends on the job, so contact us with your requirements for a quote.")

    if any(x in q for x in ["order", "book", "request", "hire", "buy", "purchase"]):
        return ("📝 You can place a request through the Order page. "
                "Choose the service, describe what you need and provide your contact details. "
                "A Digital Hub team member can then follow up with you.")

    if any(x in q for x in ["track", "tracking", "status", "job number", "request number"]):
        return ("📦 If you've submitted a photo-editing job, use the tracking link provided after submission "
                "to check its status and, when ready, access the finished result.")

    if any(x in q for x in ["digital product", "template", "download", "software product"]):
        return ("🛒 Check the Digital Store for available digital products such as templates, "
                "graphics, software tools and other useful downloads.")

    if any(x in q for x in ["human", "person", "support", "agent", "contact", "help me"]):
        return ("👨‍💻 Of course. If you need a human team member, use the Order page and describe "
                "what you need, or use the contact information provided by Digital Hub.")

    if any(x in q for x in ["who are you", "what are you", "your name", "gimmie"]):
        return ("I'm Gimmie 🤖, the Digital Hub assistant. "
                "I'm here to help customers understand our services and start their requests.")

    return ("I'm Gimmie 🤖. I can help with photo editing, graphic design, "
            "websites/software, music/audio, digital products, prices and orders. "
            "Tell me what you need and I'll point you in the right direction.")

@main.route("/")
def home():
    seed_services(); return render_template("home.html", services=Service.query.filter_by(active=True).all(), products=Product.query.order_by(Product.created_at.desc()).limit(6).all())

@main.route("/services")
def services():
    seed_services(); return render_template("services.html", services=Service.query.filter_by(active=True).all())

@main.route("/shop")
def shop(): return render_template("shop.html", products=Product.query.order_by(Product.created_at.desc()).all())

@main.route("/order", methods=["GET","POST"])
def order():
    seed_services()
    if request.method == "POST":
        db.session.add(Order(customer_name=request.form["customer_name"].strip(), contact=request.form["contact"].strip(), service=request.form["service"].strip(), message=request.form.get("message","").strip()))
        db.session.commit(); flash("Request received. A Digital Hub team member will contact you.","success"); return redirect(url_for("main.order"))
    return render_template("order.html", services=Service.query.filter_by(active=True).all())

@main.route("/edit", methods=["GET","POST"])
def edit_request():
    if request.method == "POST":
        file=request.files.get("photo"); saved=save_upload(file)
        if not saved or saved.rsplit(".",1)[-1].split("_")[-1].lower() not in IMAGE_EXTS:
            flash("Please upload a supported image: JPG, PNG or WEBP.","error"); return redirect(url_for("main.edit_request"))
        token=uuid.uuid4().hex + uuid.uuid4().hex
        job=EditJob(customer_name=request.form["customer_name"].strip(), contact=request.form["contact"].strip(), notes=request.form.get("notes","").strip(), original_file=saved, public_token=token)
        db.session.add(job); db.session.commit()
        return render_template("edit_success.html", job=job)
    return render_template("edit.html")

@main.route("/track/<token>")
def track(token):
    job=EditJob.query.filter_by(public_token=token).first_or_404()
    return render_template("track.html", job=job)

@main.route("/download/<path:filename>")
def download(filename): return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@main.route("/api/ai", methods=["POST"])
def ai_chat():
    data=request.get_json(silent=True) or {}; message=(data.get("message") or "").strip()
    if not message: return jsonify(error="Message is required"),400
    answer=ai_reply(message)
    if answer is None:
        answer=("Hi! I'm Digital Hub's assistant. I can help with photo editing, graphic design, websites/software, "
                "music/audio and digital products. For a quote, tell me what you need. To send a photo, use the Send a Photo page.")
    return jsonify(answer=answer)

@main.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method=="POST":
        admin=Admin.query.filter_by(username=request.form["username"].strip()).first()
        if admin and admin.check_password(request.form["password"]): login_user(admin); return redirect(url_for("main.dashboard"))
        flash("Invalid admin login.","error")
    return render_template("admin_login.html")

@main.route("/admin/logout")
@login_required
def admin_logout(): logout_user(); return redirect(url_for("main.home"))

@main.route("/admin")
@login_required
def dashboard():
    return render_template("admin_dashboard.html", orders=Order.query.order_by(Order.created_at.desc()).all(), jobs=EditJob.query.order_by(EditJob.created_at.desc()).all(), products=Product.query.order_by(Product.created_at.desc()).all(), services=Service.query.order_by(Service.id).all())

@main.route("/admin/edit/<int:job_id>/status", methods=["POST"])
@login_required
def edit_status(job_id):
    job=EditJob.query.get_or_404(job_id); job.status=request.form["status"]; db.session.commit(); return redirect(url_for("main.dashboard"))

@main.route("/admin/service", methods=["POST"])
@login_required
def add_service():
    db.session.add(Service(name=request.form["name"],description=request.form["description"],price=request.form.get("price","Get a quote"),icon=request.form.get("icon","✦"))); db.session.commit(); return redirect(url_for("main.dashboard"))

@main.route("/admin/service/<int:service_id>/toggle", methods=["POST"])
@login_required
def toggle_service(service_id):
    service=Service.query.get_or_404(service_id); service.active=not service.active; db.session.commit(); return redirect(url_for("main.dashboard"))

@main.route("/admin/product", methods=["POST"])
@login_required
def add_product():
    saved=save_upload(request.files.get("file"))
    if not saved: flash("Unsupported or missing product file.","error"); return redirect(url_for("main.dashboard"))
    db.session.add(Product(title=request.form["title"],description=request.form.get("description",""),category=request.form["category"],file_name=saved)); db.session.commit(); flash("Product uploaded.","success"); return redirect(url_for("main.dashboard"))

@main.route("/admin/order/<int:order_id>/status", methods=["POST"])
@login_required
def order_status(order_id):
    order=Order.query.get_or_404(order_id); order.status=request.form["status"]; db.session.commit(); return redirect(url_for("main.dashboard"))

@main.route("/admin/edit/<int:job_id>", methods=["POST"])
@login_required
def complete_edit(job_id):
    job=EditJob.query.get_or_404(job_id); saved=save_upload(request.files.get("result"))
    if not saved: flash("Upload the edited result file.","error"); return redirect(url_for("main.dashboard"))
    job.result_file=saved; job.status="Completed"; db.session.commit(); flash("Edited photo uploaded and customer tracking page updated.","success"); return redirect(url_for("main.dashboard"))
