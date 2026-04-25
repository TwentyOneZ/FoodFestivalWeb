import smtplib
from email.message import EmailMessage

from flask import current_app


def smtp_configured():
    required = ["SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM"]
    return all(current_app.config.get(key) for key in required)


def send_email(subject, recipients, body):
    if not smtp_configured():
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["SMTP_FROM"]
    message["To"] = ", ".join(recipients)
    message.set_content(body)

    try:
        with smtplib.SMTP(current_app.config["SMTP_HOST"], current_app.config["SMTP_PORT"]) as smtp:
            smtp.starttls()
            smtp.login(current_app.config["SMTP_USER"], current_app.config["SMTP_PASSWORD"])
            smtp.send_message(message)
        return True
    except Exception as exc:  # pragma: no cover - depends on live SMTP.
        current_app.logger.warning("SMTP email failed: %s", exc)
        return False


def notify_application(application):
    restaurant_body = (
        "Inscricao recebida com sucesso.\n\n"
        "A organizacao do Flavors of Brazil Food Festival - Georgia Edition 2026 "
        "entrara em contato apos a curadoria.\n\n"
        f"Restaurante: {application.restaurant_name}\n"
        f"Prato/Menu: {application.dish_name}\n"
    )
    sent_to_restaurant = send_email(
        "Inscricao recebida - Flavors of Brazil Food Festival",
        [application.responsible_email],
        restaurant_body,
    )

    admin_email = current_app.config.get("ADMIN_NOTIFICATION_EMAIL")
    sent_to_admin = False
    if admin_email:
        admin_body = (
            "Nova inscricao recebida.\n\n"
            f"Restaurante: {application.restaurant_name}\n"
            f"Responsavel: {application.responsible_name}\n"
            f"Cidade: {application.city}\n"
            f"Telefone: {application.responsible_phone}\n"
            f"E-mail: {application.responsible_email}\n"
        )
        sent_to_admin = send_email(
            "Nova inscricao - Flavors of Brazil Food Festival",
            [admin_email],
            admin_body,
        )

    return sent_to_restaurant or sent_to_admin
