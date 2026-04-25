import json
import re
import unicodedata
from urllib.parse import quote_plus

from flask import current_app, request, url_for


def slugify(value):
    value = unicodedata.normalize("NFKD", value or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "restaurante"


def unique_slug(model, name, current_id=None):
    base = slugify(name)
    candidate = base
    counter = 2
    while True:
        query = model.query.filter_by(slug=candidate)
        if current_id:
            query = query.filter(model.id != current_id)
        if not query.first():
            return candidate
        candidate = f"{base}-{counter}"
        counter += 1


def external_url(endpoint, **values):
    try:
        return url_for(endpoint, _external=True, **values)
    except RuntimeError:
        base = current_app.config.get("SITE_URL", "").rstrip("/")
        path = url_for(endpoint, **values)
        return f"{base}{path}"


def public_image(path):
    if not path:
        return external_url("static", filename="assets/generated/restaurant-placeholder.webp")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if path.startswith("/static/"):
        return f"{request.url_root.rstrip('/')}{path}"
    return external_url("static", filename=path)


def map_url(restaurant):
    query = f"{restaurant.address}, {restaurant.city}, {restaurant.state} {restaurant.zip_code}"
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"


def phone_href(phone):
    digits = re.sub(r"[^0-9+]", "", phone or "")
    return f"tel:{digits}" if digits else "#"


def event_schema(settings):
    data = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": settings.get("hero_title"),
        "description": settings.get("homepage_description"),
        "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {
            "@type": "Place",
            "name": "Georgia, United States",
            "address": {
                "@type": "PostalAddress",
                "addressRegion": "GA",
                "addressCountry": "US",
            },
        },
        "organizer": [
            {"@type": "Organization", "name": "Business News TV"},
            {"@type": "Organization", "name": "Viver Magazine"},
        ],
    }
    return json.dumps(data, ensure_ascii=False)


def restaurant_schema(restaurant):
    data = {
        "@context": "https://schema.org",
        "@type": "Restaurant",
        "name": restaurant.name,
        "description": restaurant.description,
        "image": public_image(restaurant.image),
        "telephone": restaurant.phone,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": restaurant.address,
            "addressLocality": restaurant.city,
            "addressRegion": restaurant.state,
            "postalCode": restaurant.zip_code,
            "addressCountry": "US",
        },
        "servesCuisine": "Brazilian",
        "url": external_url("main.restaurant_detail", slug=restaurant.slug),
    }
    if restaurant.website:
        data["sameAs"] = [restaurant.website]
    if restaurant.instagram:
        data.setdefault("sameAs", []).append(restaurant.instagram)
    return json.dumps(data, ensure_ascii=False)
