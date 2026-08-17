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

def build_gimmie_knowledge():
    """Build Gimmie's current knowledge from Digital Hub's database."""

    seed_services()

    services = Service.query.filter_by(active=True).all()
    products = Product.query.order_by(Product.created_at.desc()).limit(30).all()

    service_text = "\n".join(
        f"- {x.name}: {x.description} Price: {x.price}"
        for x in services
    )

    product_text = "\n".join(
        f"- {x.title}: {x.description} Category: {x.category}"
        for x in products
    )

    if not product_text:
        product_text = "- No digital products are currently listed."

    return services, products, f"""
DIGITAL HUB

Digital Hub is a digital services platform.

CURRENT SERVICES:
{service_text}

CURRENT DIGITAL PRODUCTS:
{product_text}

CUSTOMER PHOTO EDITING WORKFLOW:
1. Customer opens Send a Photo.
2. Customer uploads their image.
3. Customer describes the requested changes.
4. Digital Hub receives the editing job.
5. The team edits the image.
6. Customer can track the job using the tracking link.
7. When completed, the customer can download the result.

ADMIN WORKFLOW:
Admins can manage photo-editing jobs, customer orders, services and digital products.

IMPORTANT BUSINESS RULES:
- Never invent services that Digital Hub does not offer.
- Never invent prices.
- Prices shown are starting prices unless explicitly stated otherwise.
- Do not promise an exact delivery time unless the system provides one.
- Do not claim a payment was received unless the system confirms it.
- Do not expose private customer information.
- Do not expose admin information to normal customers.
- Do not reveal passwords, API keys, environment variables or internal secrets.
- Do not tell customers that you performed an action unless the action actually succeeded.
- If a request requires a human, tell the customer that a Digital Hub team member can assist.
- For photo editing, direct customers to Send a Photo.
- For general service requests, direct customers to Order.
"""

def ai_reply(message):
    """
    Gimmie customer assistant.

    Uses live Digital Hub database information and a safe local
    knowledge layer. No API key is required for this mode.
    """

    services, products, knowledge = build_gimmie_knowledge()

    q = " ".join((message or "").lower().strip().split())

    if not q:
        return "Hi! I'm Gimmie 👋 How can I help you today?"

    # Greetings
    if any(x in q for x in [
        "hello", "hi", "hey", "habari", "mambo", "sasa"
    ]):
        return (
            "Hey! 👋 I'm Gimmie, the Digital Hub assistant. "
            "I can help you with photo editing, design, websites, "
            "software, music, digital products and orders. "
            "What would you like to do?"
        )

    # Identity
    if any(x in q for x in [
        "who are you", "what are you", "your name", "gimmie"
    ]):
        return (
            "I'm Gimmie 🤖, Digital Hub's digital assistant. "
            "I can help customers understand our services, "
            "start requests, find products and navigate Digital Hub."
        )

    # Photo editing
    if any(x in q for x in [
        "photo", "picture", "pic", "image",
        "photo edit", "edit photo", "edit picture",
        "background", "retouch"
    ]):
        return (
            "📸 Yes, Digital Hub offers professional photo editing. "
            "You can send a JPG, PNG, WEBP or other supported image, "
            "then tell us exactly what you want changed — for example "
            "background removal, retouching or social-media graphics. "
            "Tap **Send a Photo** to start."
        )

    # Services
    if any(x in q for x in [
        "services", "what do you offer",
        "what can you do", "service list"
    ]):
        names = ", ".join(x.name for x in services)

        return (
            f"✨ Digital Hub currently offers: {names}. "
            "I can also help you choose the right service."
        )

    # Pricing
    if any(x in q for x in [
        "price", "prices", "cost", "how much",
        "pricing", "rates", "fee", "charge"
    ]):
        lines = [
            f"• {x.name}: {x.price}"
            for x in services
        ]

        return (
            "💰 Here are our current starting prices:\n\n"
            + "\n".join(lines)
            + "\n\nFinal pricing can depend on the exact requirements."
        )

    # Design
    if any(x in q for x in [
        "logo", "flyer", "poster", "banner",
        "thumbnail", "invitation", "graphic design"
    ]):
        return (
            "🎨 Digital Hub provides digital design such as logos, "
            "flyers, posters, banners, thumbnails and invitations. "
            "Tell me what you want designed and I can guide you to the order."
        )

    # Websites/software
    if any(x in q for x in [
        "website", "web site", "software",
        "app", "application", "coding", "developer"
    ]):
        return (
            "💻 We build websites and custom digital software. "
            "For a quote, tell me what you want to build, who will use it "
            "and the main features you need."
        )

    # Music
    if any(x in q for x in [
        "music", "audio", "song",
        "sound", "cover art", "podcast"
    ]):
        return (
            "🎵 Digital Hub offers music and audio-related services, "
            "including audio cleanup, cover art and promotional assets. "
            "Tell me what you're working on."
        )

    # Products
    if any(x in q for x in [
        "product", "products", "store", "shop",
        "download", "template", "digital product"
    ]):
        if products:
            names = ", ".join(x.title for x in products[:10])
            return (
                f"🛒 Our Digital Store currently has: {names}. "
                "Open the Store to see the available products."
            )

        return (
            "🛒 The Digital Store is available, but there are currently "
            "no products listed."
        )

    # Ordering
    if any(x in q for x in [
        "order", "place an order", "book",
        "hire", "request", "buy"
    ]):
        return (
            "📝 You can start an order by choosing the service you need "
            "and describing your requirements. I'll help you get to the "
            "Order page."
        )

    # Tracking
    if any(x in q for x in [
        "track", "tracking", "status",
        "where is my job", "editing status"
    ]):
        return (
            "📦 If you submitted a photo-editing request, use the tracking "
            "link you received after submitting it. That link shows the "
            "current job status and the finished file when it is available."
        )

    # Human support
    if any(x in q for x in [
        "human", "person", "agent",
        "support", "talk to someone"
    ]):
        return (
            "👨‍💻 Of course. If you need a Digital Hub team member, "
            "start an Order request and explain what you need."
        )

    # General fallback
    return (
        "I'm Gimmie 🤖. I can help with Digital Hub's current services, "
        "prices, photo editing, graphic design, websites/software, "
        "music/audio, digital products, orders and tracking. "
        "Tell me what you're trying to accomplish and I'll guide you."
    )

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
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify(
            answer="Tell me what you would like help with.",
            action=None
        ), 400

    answer = ai_reply(message)

    # Safe customer actions.
    q = " ".join(message.lower().split())
    action = None

    if any(x in q for x in [
        "send photo", "send a photo", "upload photo", "upload a photo",
        "edit photo", "edit a photo", "photo editing", "picture edit",
        "edit my picture"
    ]):
        action = {
            "type": "navigate",
            "url": url_for("main.edit_request")
        }

    elif any(x in q for x in [
        "services", "show services", "what do you offer",
        "your services", "service list"
    ]):
        action = {
            "type": "navigate",
            "url": url_for("main.services")
        }

    elif any(x in q for x in [
        "store", "shop", "digital products", "products",
        "downloads", "show products"
    ]):
        action = {
            "type": "navigate",
            "url": url_for("main.shop")
        }

    elif any(x in q for x in [
        "order", "place an order", "make an order",
        "start an order", "hire you", "request a service"
    ]):
        action = {
            "type": "navigate",
            "url": url_for("main.order")
        }

    elif any(x in q for x in [
        "home", "homepage", "go home", "main page"
    ]):
        action = {
            "type": "navigate",
            "url": url_for("main.home")
        }

    if answer is None:
        answer = (
            "I'm Gimmie 🤖. I can help you with Digital Hub services, "
            "photo editing, design, websites, software, music, products "
            "and orders."
        )

    return jsonify(
        answer=answer,
        action=action
    )

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
