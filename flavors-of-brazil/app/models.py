from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


APPLICATION_STATUSES = [
    "Recebida",
    "Em curadoria",
    "Aprovada",
    "Recusada",
    "Aguardando pagamento",
    "Pagamento recebido",
    "Confirmada",
    "Publicada",
]

VIDEO_STATUSES = [
    "Nao agendado",
    "Agendado",
    "Gravado",
    "Publicado",
]


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(60), default="admin", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Application(db.Model, TimestampMixin):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    responsible_name = db.Column(db.String(160), nullable=False)
    responsible_role = db.Column(db.String(120), nullable=False)
    responsible_phone = db.Column(db.String(80), nullable=False)
    responsible_email = db.Column(db.String(255), nullable=False)
    restaurant_name = db.Column(db.String(180), nullable=False)
    business_type = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(40), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    business_phone = db.Column(db.String(80), nullable=False)
    website = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    facebook = db.Column(db.String(255))
    business_hours = db.Column(db.Text, nullable=False)
    legal_business = db.Column(db.String(10), nullable=False)
    dish_name = db.Column(db.String(180), nullable=False)
    dish_description = db.Column(db.Text, nullable=False)
    dish_price = db.Column(db.String(40), nullable=False)
    dish_category = db.Column(db.String(80), nullable=False)
    main_ingredients = db.Column(db.Text, nullable=False)
    allergens = db.Column(db.Text)
    available_full_period = db.Column(db.String(10), nullable=False)
    dish_image = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status = db.Column(db.String(80), default="Recebida", nullable=False, index=True)
    internal_notes = db.Column(db.Text)
    filming_date = db.Column(db.String(40))
    video_status = db.Column(db.String(80), default="Nao agendado", nullable=False)

    restaurant = db.relationship(
        "Restaurant",
        back_populates="application",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Restaurant(db.Model, TimestampMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=True)
    name = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(220), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)
    dish_name = db.Column(db.String(180), nullable=False)
    dish_description = db.Column(db.Text, nullable=False)
    dish_price = db.Column(db.String(40), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(40), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(80), nullable=False)
    website = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    business_hours = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=False, nullable=False, index=True)

    application = db.relationship("Application", back_populates="restaurant")


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False)

    @classmethod
    def get(cls, key, default=""):
        item = cls.query.filter_by(key=key).first()
        return item.value if item else default

    @classmethod
    def set(cls, key, value):
        item = cls.query.filter_by(key=key).first()
        if item is None:
            item = cls(key=key, value=value or "")
            db.session.add(item)
        else:
            item.value = value or ""
        return item
