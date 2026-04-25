import re


BUSINESS_TYPES = [
    "Restaurante",
    "Bar",
    "Cafe",
    "Padaria",
    "Doceria",
    "Food truck",
    "Outro",
]

DISH_CATEGORIES = [
    "Prato principal",
    "Lanche",
    "Sobremesa",
    "Bebida",
    "Combo",
    "Outro",
]

YES_NO = ["Sim", "Nao"]

ACCEPT_FIELDS = [
    "accept_truth",
    "accept_curation",
    "accept_fee",
    "accept_brand",
    "accept_media",
    "accept_responsibilities",
]

REQUIRED_FIELDS = [
    "responsible_name",
    "responsible_role",
    "responsible_phone",
    "responsible_email",
    "restaurant_name",
    "business_type",
    "address",
    "city",
    "state",
    "zip_code",
    "business_phone",
    "business_hours",
    "legal_business",
    "dish_name",
    "dish_description",
    "dish_price",
    "dish_category",
    "main_ingredients",
    "available_full_period",
]


def clean_value(form, key):
    value = form.get(key, "")
    return value.strip() if isinstance(value, str) else value


def validate_application_form(form):
    errors = {}

    for field in REQUIRED_FIELDS:
        if not clean_value(form, field):
            errors[field] = "error_required"

    email = clean_value(form, "responsible_email")
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors["responsible_email"] = "error_email"

    if clean_value(form, "business_type") not in BUSINESS_TYPES:
        errors["business_type"] = "error_business_type"

    if clean_value(form, "dish_category") not in DISH_CATEGORIES:
        errors["dish_category"] = "error_dish_category"

    if clean_value(form, "legal_business") not in YES_NO:
        errors["legal_business"] = "error_yes_no"

    if clean_value(form, "available_full_period") not in YES_NO:
        errors["available_full_period"] = "error_yes_no"

    for field in ACCEPT_FIELDS:
        if form.get(field) != "on":
            errors[field] = "error_accept"

    return errors
