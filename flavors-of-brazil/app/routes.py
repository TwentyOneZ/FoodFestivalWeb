import csv
from datetime import datetime
from io import StringIO
from pathlib import Path
from uuid import uuid4

from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from .auth import login_required, login_user, logout_user, validate_csrf, verify_password
from .content import DEFAULT_LANGUAGE, DEFAULT_SETTINGS, LANGUAGES, localize_settings, translate
from .email_utils import notify_application, smtp_configured
from .forms import BUSINESS_TYPES, DISH_CATEGORIES, clean_value, validate_application_form
from .models import (
    APPLICATION_STATUSES,
    VIDEO_STATUSES,
    Application,
    Restaurant,
    Setting,
    User,
    db,
)
from .seo import event_schema, map_url, phone_href, restaurant_schema, unique_slug

bp = Blueprint("main", __name__)


def get_settings():
    return localize_settings(get_stored_settings(), getattr(g, "lang", DEFAULT_LANGUAGE))


def get_stored_settings():
    return {key: Setting.get(key, default) for key, default in DEFAULT_SETTINGS.items()}


def tr(key):
    return translate(getattr(g, "lang", DEFAULT_LANGUAGE), key)


def allowed_file(filename):
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_UPLOAD_EXTENSIONS"]


def save_upload(file_storage, prefix="upload"):
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        abort(400, description="Formato de arquivo nao permitido.")
    ext = secure_filename(file_storage.filename).rsplit(".", 1)[1].lower()
    filename = f"{prefix}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}.{ext}"
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_storage.save(upload_dir / filename)
    return f"uploads/{filename}"


def application_from_form(form, image_path=None):
    return Application(
        responsible_name=clean_value(form, "responsible_name"),
        responsible_role=clean_value(form, "responsible_role"),
        responsible_phone=clean_value(form, "responsible_phone"),
        responsible_email=clean_value(form, "responsible_email"),
        restaurant_name=clean_value(form, "restaurant_name"),
        business_type=clean_value(form, "business_type"),
        address=clean_value(form, "address"),
        city=clean_value(form, "city"),
        state=clean_value(form, "state"),
        zip_code=clean_value(form, "zip_code"),
        business_phone=clean_value(form, "business_phone"),
        website=clean_value(form, "website"),
        instagram=clean_value(form, "instagram"),
        facebook=clean_value(form, "facebook"),
        business_hours=clean_value(form, "business_hours"),
        legal_business=clean_value(form, "legal_business"),
        dish_name=clean_value(form, "dish_name"),
        dish_description=clean_value(form, "dish_description"),
        dish_price=clean_value(form, "dish_price"),
        dish_category=clean_value(form, "dish_category"),
        main_ingredients=clean_value(form, "main_ingredients"),
        allergens=clean_value(form, "allergens"),
        available_full_period=clean_value(form, "available_full_period"),
        dish_image=image_path,
        notes=clean_value(form, "notes"),
        status="Recebida",
        video_status="Nao agendado",
    )


def publish_restaurant(application):
    restaurant = application.restaurant or Restaurant()
    restaurant.name = application.restaurant_name
    restaurant.slug = unique_slug(Restaurant, application.restaurant_name, restaurant.id)
    restaurant.description = application.dish_description
    restaurant.dish_name = application.dish_name
    restaurant.dish_description = application.dish_description
    restaurant.dish_price = application.dish_price
    restaurant.address = application.address
    restaurant.city = application.city
    restaurant.state = application.state
    restaurant.zip_code = application.zip_code
    restaurant.phone = application.business_phone
    restaurant.website = application.website
    restaurant.instagram = application.instagram
    restaurant.business_hours = application.business_hours
    restaurant.image = application.dish_image or "assets/generated/restaurant-placeholder.webp"
    restaurant.is_published = True
    restaurant.application = application
    application.status = "Publicada"
    db.session.add(restaurant)
    return restaurant


def applications_csv_response(applications, filename="inscricoes.csv"):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "restaurante",
            "responsavel",
            "cidade",
            "telefone",
            "email",
            "status",
            "prato",
            "preco",
            "criado_em",
        ]
    )
    for item in applications:
        writer.writerow(
            [
                item.id,
                item.restaurant_name,
                item.responsible_name,
                item.city,
                item.responsible_phone,
                item.responsible_email,
                item.status,
                item.dish_name,
                item.dish_price,
                item.created_at.isoformat(),
            ]
        )
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@bp.route("/set-language/<lang>")
def set_language(lang):
    if lang in LANGUAGES:
        session["lang"] = lang
    next_url = request.args.get("next") or url_for("main.index")
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("main.index")
    return redirect(next_url)


@bp.route("/")
def index():
    settings = get_settings()
    restaurants = (
        Restaurant.query.filter_by(is_published=True)
        .order_by(Restaurant.created_at.desc())
        .limit(6)
        .all()
    )
    seo = {
        "title": settings["homepage_title"],
        "description": settings["homepage_description"],
        "image": url_for("static", filename="assets/generated/hero-brazil.webp", _external=True),
    }
    return render_template(
        "index.html",
        settings=settings,
        restaurants=restaurants,
        seo=seo,
        schema=event_schema(settings),
    )


@bp.route("/restaurantes")
def restaurants():
    settings = get_settings()
    restaurants_list = (
        Restaurant.query.filter_by(is_published=True)
        .order_by(Restaurant.name.asc())
        .all()
    )
    seo = {
        "title": f"{tr('restaurants_title')} | Flavors of Brazil Food Festival",
        "description": tr("restaurants_page_text"),
        "image": url_for("static", filename="assets/generated/gastronomy-bg.webp", _external=True),
    }
    return render_template(
        "restaurants.html",
        settings=settings,
        restaurants=restaurants_list,
        seo=seo,
    )


@bp.route("/restaurantes/<slug>")
def restaurant_detail(slug):
    restaurant = Restaurant.query.filter_by(slug=slug, is_published=True).first_or_404()
    seo = {
        "title": f"{restaurant.name} | Flavors of Brazil Food Festival",
        "description": restaurant.dish_description[:155],
        "image": url_for("static", filename=restaurant.image or "assets/generated/restaurant-placeholder.webp", _external=True),
    }
    return render_template(
        "restaurant_detail.html",
        restaurant=restaurant,
        seo=seo,
        schema=restaurant_schema(restaurant),
        map_link=map_url(restaurant),
        phone_link=phone_href(restaurant.phone),
    )


@bp.route("/inscricao", methods=["GET", "POST"])
def apply():
    settings = get_settings()
    errors = {}
    form_data = request.form if request.method == "POST" else {}

    if request.method == "POST":
        validate_csrf()
        errors = validate_application_form(request.form)
        dish_file = request.files.get("dish_image")
        if dish_file and dish_file.filename and not allowed_file(dish_file.filename):
            errors["dish_image"] = "error_upload_image"

        if not errors:
            image_path = save_upload(dish_file, "dish") if dish_file and dish_file.filename else None
            application = application_from_form(request.form, image_path=image_path)
            db.session.add(application)
            db.session.commit()
            notify_application(application)
            return redirect(url_for("main.thank_you"))

    seo = {
        "title": f"{tr('apply_title')} | Flavors of Brazil Food Festival",
        "description": tr("apply_intro"),
        "image": url_for("static", filename="assets/generated/media.webp", _external=True),
    }
    return render_template(
        "apply.html",
        settings=settings,
        seo=seo,
        errors=errors,
        form_data=form_data,
        business_types=BUSINESS_TYPES,
        dish_categories=DISH_CATEGORIES,
    )


@bp.route("/obrigado")
def thank_you():
    seo = {
        "title": f"{tr('thank_you_title')} | Flavors of Brazil Food Festival",
        "description": tr("thank_you_text"),
    }
    return render_template("thank_you.html", seo=seo)


@bp.route("/termos")
def terms():
    seo = {
        "title": f"{tr('terms')} | Flavors of Brazil Food Festival",
        "description": tr("terms_title"),
    }
    return render_template("terms.html", seo=seo)


@bp.route("/privacidade")
def privacy():
    seo = {
        "title": f"{tr('privacy')} | Flavors of Brazil Food Festival",
        "description": tr("privacy_title"),
    }
    return render_template("privacy.html", seo=seo)


@bp.route("/sitemap.xml")
def sitemap():
    restaurants_list = Restaurant.query.filter_by(is_published=True).all()
    urls = [
        url_for("main.index", _external=True),
        url_for("main.restaurants", _external=True),
        url_for("main.apply", _external=True),
        url_for("main.terms", _external=True),
        url_for("main.privacy", _external=True),
    ]
    urls.extend(
        url_for("main.restaurant_detail", slug=restaurant.slug, _external=True)
        for restaurant in restaurants_list
    )
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for item in urls:
        xml.append(f"<url><loc>{item}</loc></url>")
    xml.append("</urlset>")
    return Response("\n".join(xml), mimetype="application/xml")


@bp.route("/robots.txt")
def robots():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /admin\n"
        f"Sitemap: {url_for('main.sitemap', _external=True)}\n"
    )
    return Response(body, mimetype="text/plain")


@bp.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        validate_csrf()
        email = clean_value(request.form, "email").lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if verify_password(user, password):
            login_user(user)
            return redirect(request.args.get("next") or url_for("main.admin_dashboard"))
        flash("Login invalido.", "error")
    seo = {"title": "Admin | Flavors of Brazil Food Festival", "description": "Painel administrativo."}
    return render_template("admin_login.html", seo=seo)


@bp.route("/admin/logout")
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for("main.admin_login"))


@bp.route("/admin/dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if request.method == "POST":
        validate_csrf()
        for key in DEFAULT_SETTINGS:
            if key in request.form:
                Setting.set(key, clean_value(request.form, key))
        db.session.commit()
        flash("Conteudo atualizado.", "success")
        return redirect(url_for("main.admin_dashboard"))

    counts = {"Total": Application.query.count()}
    for status in APPLICATION_STATUSES:
        counts[status] = Application.query.filter_by(status=status).count()

    seo = {"title": "Dashboard | Flavors of Brazil Food Festival", "description": "Resumo administrativo."}
    return render_template(
        "admin_dashboard.html",
        seo=seo,
        counts=counts,
        settings=get_stored_settings(),
        smtp_ready=smtp_configured(),
        statuses=APPLICATION_STATUSES,
    )


@bp.route("/admin/inscricoes")
@login_required
def admin_applications():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    query = Application.query

    if search:
        like = f"%{search}%"
        query = query.filter(Application.restaurant_name.ilike(like))
    if status in APPLICATION_STATUSES:
        query = query.filter_by(status=status)

    applications = query.order_by(Application.created_at.desc()).all()

    if request.args.get("export") == "csv":
        return applications_csv_response(applications)

    seo = {"title": "Inscricoes | Flavors of Brazil Food Festival", "description": "Lista de inscricoes."}
    return render_template(
        "admin_applications.html",
        seo=seo,
        applications=applications,
        statuses=APPLICATION_STATUSES,
        search=search,
        active_status=status,
    )


@bp.route("/admin/inscricoes/<int:application_id>", methods=["GET", "POST"])
@login_required
def admin_application_detail(application_id):
    application = Application.query.get_or_404(application_id)

    if request.args.get("export") == "csv":
        return applications_csv_response([application], filename=f"inscricao-{application.id}.csv")

    if request.method == "POST":
        validate_csrf()
        action = request.form.get("action")

        if action == "save":
            status = clean_value(request.form, "status")
            video_status = clean_value(request.form, "video_status")
            if status in APPLICATION_STATUSES:
                application.status = status
            if video_status in VIDEO_STATUSES:
                application.video_status = video_status
            application.internal_notes = clean_value(request.form, "internal_notes")
            application.filming_date = clean_value(request.form, "filming_date")

            uploaded = save_upload(request.files.get("admin_dish_image"), "dish-admin")
            if uploaded:
                application.dish_image = uploaded
            db.session.commit()
            flash("Inscricao atualizada.", "success")

        elif action == "publish":
            uploaded = save_upload(request.files.get("admin_dish_image"), "dish-admin")
            if uploaded:
                application.dish_image = uploaded
            publish_restaurant(application)
            db.session.commit()
            flash("Restaurante publicado.", "success")

        elif action == "unpublish":
            if application.restaurant:
                application.restaurant.is_published = False
                db.session.commit()
                flash("Restaurante removido da pagina publica.", "success")

        return redirect(url_for("main.admin_application_detail", application_id=application.id))

    seo = {"title": f"Inscricao {application.id} | Flavors of Brazil", "description": "Detalhe da inscricao."}
    return render_template(
        "admin_application_detail.html",
        seo=seo,
        application=application,
        statuses=APPLICATION_STATUSES,
        video_statuses=VIDEO_STATUSES,
    )


@bp.route("/admin/restaurantes", methods=["GET", "POST"])
@login_required
def admin_restaurants():
    if request.method == "POST":
        validate_csrf()
        restaurant = Restaurant.query.get_or_404(int(request.form.get("restaurant_id")))
        restaurant.name = clean_value(request.form, "name")
        restaurant.slug = unique_slug(Restaurant, restaurant.name, restaurant.id)
        restaurant.description = clean_value(request.form, "description")
        restaurant.dish_name = clean_value(request.form, "dish_name")
        restaurant.dish_description = clean_value(request.form, "dish_description")
        restaurant.dish_price = clean_value(request.form, "dish_price")
        restaurant.address = clean_value(request.form, "address")
        restaurant.city = clean_value(request.form, "city")
        restaurant.state = clean_value(request.form, "state")
        restaurant.zip_code = clean_value(request.form, "zip_code")
        restaurant.phone = clean_value(request.form, "phone")
        restaurant.website = clean_value(request.form, "website")
        restaurant.instagram = clean_value(request.form, "instagram")
        restaurant.business_hours = clean_value(request.form, "business_hours")
        restaurant.is_published = request.form.get("is_published") == "on"

        uploaded = save_upload(request.files.get("image"), "restaurant")
        if uploaded:
            restaurant.image = uploaded

        db.session.commit()
        flash("Restaurante atualizado.", "success")
        return redirect(url_for("main.admin_restaurants"))

    restaurants_list = Restaurant.query.order_by(Restaurant.created_at.desc()).all()
    seo = {"title": "Restaurantes | Flavors of Brazil", "description": "Gerenciar restaurantes publicados."}
    return render_template(
        "admin_restaurants.html",
        seo=seo,
        restaurants=restaurants_list,
    )
