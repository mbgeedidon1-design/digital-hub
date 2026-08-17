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
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        model = os.environ.get("OPENAI_MODEL", "gpt-5.6")
        instructions = ("You are Digital Hub's helpful customer assistant. Digital Hub offers photo editing, "
                        "graphic design, websites/software, music/audio services and digital downloads. "
                        "Be concise, friendly and transparent. Never invent prices, delivery times, payments, "
                        "or guarantees. If a customer wants a quote, ask for the service, details and contact. "
                        "For photo editing, direct them to the Send a Photo page. For human help, say a team member can assist.")
        response = client.responses.create(model=model, instructions=instructions, input=message)
        return response.output_text
    except Exception:
        return None

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
