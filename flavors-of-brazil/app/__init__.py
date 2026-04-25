from pathlib import Path

from flask import Flask, g, request, session, url_for
from werkzeug.security import generate_password_hash

from .auth import csrf_token, current_user
from .content import DEFAULT_LANGUAGE, DEFAULT_SETTINGS, LANGUAGES, localize_settings, option_label, translate
from .models import Application, Restaurant, Setting, User, db
from .seo import public_image


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object("config.Config")

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
    Path(Path(__file__).resolve().parent.parent / "instance").mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from .routes import bp

    app.register_blueprint(bp)

    @app.before_request
    def load_language():
        requested = request.args.get("lang")
        if requested in LANGUAGES:
            session["lang"] = requested
        g.lang = session.get("lang", DEFAULT_LANGUAGE)

    @app.context_processor
    def inject_globals():
        try:
            stored_settings = {key: Setting.get(key, default) for key, default in DEFAULT_SETTINGS.items()}
        except Exception:
            stored_settings = DEFAULT_SETTINGS.copy()
        active_language = getattr(g, "lang", DEFAULT_LANGUAGE)
        site_settings = localize_settings(stored_settings, active_language)
        return {
            "current_user": current_user(),
            "csrf_token": csrf_token,
            "languages": LANGUAGES,
            "active_lang": active_language,
            "t": lambda key: translate(active_language, key),
            "option_label": lambda value: option_label(active_language, value),
            "asset_url": public_image,
            "site_settings": site_settings,
            "url_for": url_for,
        }

    return app


def seed_database(app):
    with app.app_context():
        db.create_all()

        for key, value in DEFAULT_SETTINGS.items():
            if Setting.query.filter_by(key=key).first() is None:
                db.session.add(Setting(key=key, value=value))

        if User.query.filter_by(email="admin@flavorsofbrazil.com").first() is None:
            db.session.add(
                User(
                    name="Festival Admin",
                    email="admin@flavorsofbrazil.com",
                    password_hash=generate_password_hash("ChangeMe123!"),
                    role="admin",
                )
            )

        examples = [
            {
                "name": "Casa Verde Brasil",
                "city": "Marietta",
                "dish": "Moqueca Georgia Edition",
                "price": "US$34",
                "image": "assets/generated/restaurant-1.webp",
                "description": "Cozinha brasileira acolhedora com pratos de peixe, leite de coco, pimentoes e ervas frescas.",
                "dish_description": "Moqueca cremosa de peixe com arroz de coco, farofa crocante e vinagrete de manga.",
            },
            {
                "name": "Sabor da Serra Cafe",
                "city": "Atlanta",
                "dish": "Picanha Executive Bowl",
                "price": "US$29",
                "image": "assets/generated/restaurant-2.webp",
                "description": "Cafe e restaurante casual com sabores brasileiros de almoco, paes e doces artesanais.",
                "dish_description": "Picanha grelhada com arroz, feijao tropeiro, mandioca dourada e molho da casa.",
            },
            {
                "name": "Doce Bahia Bakery",
                "city": "Sandy Springs",
                "dish": "Trio Tropical de Sobremesas",
                "price": "US$18",
                "image": "assets/generated/restaurant-3.webp",
                "description": "Padaria e doceria brasileira com sobremesas tropicais, cafes e salgados de forno.",
                "dish_description": "Mini quindim, brigadeiro de castanha e mousse de maracuja com crocante de coco.",
            },
        ]

        for item in examples:
            if Restaurant.query.filter_by(slug=item["name"].lower().replace(" ", "-")).first():
                continue
            restaurant = Restaurant(
                name=item["name"],
                slug=item["name"].lower().replace(" ", "-"),
                description=item["description"],
                dish_name=item["dish"],
                dish_description=item["dish_description"],
                dish_price=item["price"],
                address="123 Peachtree Market Road",
                city=item["city"],
                state="GA",
                zip_code="30060",
                phone="(770) 000-2026",
                website="https://flavorsofbrazil.com",
                instagram="https://instagram.com/businessbrazil.usa",
                business_hours="Segunda a sabado, 11am - 9pm",
                image=item["image"],
                is_published=True,
            )
            db.session.add(restaurant)

            application = Application(
                responsible_name="Contato Exemplo",
                responsible_role="Owner",
                responsible_phone="(770) 000-2026",
                responsible_email="example@flavorsofbrazil.com",
                restaurant_name=item["name"],
                business_type="Restaurante",
                address=restaurant.address,
                city=item["city"],
                state="GA",
                zip_code=restaurant.zip_code,
                business_phone=restaurant.phone,
                website=restaurant.website,
                instagram=restaurant.instagram,
                facebook="",
                business_hours=restaurant.business_hours,
                legal_business="Sim",
                dish_name=item["dish"],
                dish_description=item["dish_description"],
                dish_price=item["price"],
                dish_category="Prato principal",
                main_ingredients="Ingredientes brasileiros selecionados",
                allergens="Consulte a equipe do restaurante.",
                available_full_period="Sim",
                dish_image=item["image"],
                notes="Cadastro ficticio para demonstracao.",
                status="Publicada",
                video_status="Publicado",
            )
            restaurant.application = application
            db.session.add(application)

        db.session.commit()
