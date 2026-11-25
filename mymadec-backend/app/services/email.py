from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Any

from app.core.config import settings

logger = logging.getLogger("mymadec.email")

BRAND_COLOR = "#00578F"


def is_email_enabled() -> bool:
    return not settings.DISABLE_EMAIL and bool(settings.SMTP_USER and settings.SMTP_PASSWORD)


def email_health_summary(*, test_connection: bool = False) -> dict[str, Any]:
    """Safe summary for /health — no secrets."""
    summary: dict[str, Any] = {
        "enabled": is_email_enabled(),
        "disabled_flag": settings.DISABLE_EMAIL,
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "user_configured": bool(settings.SMTP_USER),
        "password_configured": bool(settings.SMTP_PASSWORD),
    }
    if is_email_enabled() and test_connection:
        status = smtp_status(test_connection=True)
        summary["connection"] = status.get("connection")
        if status.get("error"):
            summary["error"] = status["error"]
    elif is_email_enabled():
        summary["connection"] = "not_tested"
    else:
        summary["connection"] = "disabled"
    return summary


def smtp_status(*, test_connection: bool = False) -> dict[str, Any]:
    if not is_email_enabled():
        return {"connection": "disabled"}

    if not test_connection:
        return {"connection": "not_tested"}

    try:
        with _smtp_connect():
            pass
        return {"connection": "ok"}
    except Exception as exc:
        logger.exception("SMTP connection test failed")
        return {"connection": "failed", "error": str(exc)}


def _smtp_connect() -> smtplib.SMTP:
    # Keep timeout short so request handlers / startup never hang indefinitely.
    timeout = 12
    if settings.SMTP_TLS:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
        server.starttls()
    else:
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
    return server


def _wrap_html(title: str, inner_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>{escape(title)}</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:Inter,Arial,sans-serif;color:#1e293b;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc;padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="100%" style="max-width:520px;background:#fff;border-radius:16px;border:1px solid #e2e8f0;overflow:hidden;">
        <tr><td style="background:{BRAND_COLOR};padding:20px 28px;">
          <p style="margin:0;color:#fff;font-size:18px;font-weight:700;">My Madec</p>
          <p style="margin:4px 0 0;color:#d1e9f5;font-size:13px;">Plateforme de commande professionnelle</p>
        </td></tr>
        <tr><td style="padding:28px;font-size:15px;line-height:1.6;">{inner_html}</td></tr>
        <tr><td style="padding:16px 28px 24px;border-top:1px solid #f1f5f9;font-size:12px;color:#94a3b8;">
          Cet email a été envoyé automatiquement — ne répondez pas directement.
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _button(href: str, label: str) -> str:
    return (
        f'<p style="margin:24px 0 8px;">'
        f'<a href="{escape(href)}" style="display:inline-block;background:{BRAND_COLOR};color:#fff;'
        f'text-decoration:none;padding:12px 24px;border-radius:10px;font-weight:600;">{escape(label)}</a>'
        f"</p>"
    )


def _build_message(to: str, subject: str, html: str, plain: str | None = None) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to
    text = plain if plain is not None else "Consultez la version HTML de cet email."
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


def send_email(to: str, subject: str, html: str, *, plain: str | None = None) -> bool:
    if not is_email_enabled():
        logger.warning("Email disabled — skipped: %s — %s", to, subject)
        return False
    msg = _build_message(to, subject, html, plain)
    last_exc: Exception | None = None
    # One retry: first SSL handshake to mail.madec.ma can be flaky.
    for attempt in (1, 2):
        try:
            with _smtp_connect() as server:
                refused = server.send_message(msg)
            if refused:
                logger.error("SMTP refused recipients for %s: %s", to, refused)
                return False
            logger.info("Email sent to %s — %s (attempt %s)", to, subject, attempt)
            return True
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "SMTP send attempt %s failed for %s: %s",
                attempt, to, exc,
            )
    logger.error("Failed to send email to %s after retries: %s", to, last_exc, exc_info=True)
    return False


def send_startup_test_email(to: str) -> bool:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    plain = (
        f"Test SMTP My Madec — démarrage API\n"
        f"Horodatage: {now}\n"
        f"Expéditeur SMTP: {settings.SMTP_USER}\n"
        f"Si vous recevez cet email, l'envoi fonctionne."
    )
    body = f"""
    <h2 style="margin:0 0 12px;font-size:20px;color:#0f172a;">Test SMTP — démarrage</h2>
    <p>Ceci est un email de test envoyé automatiquement au démarrage de l'API My Madec.</p>
    <p style="margin:12px 0;padding:12px 16px;background:#f1f5f9;border-radius:8px;font-family:monospace;font-size:13px;">
      Horodatage : {escape(now)}<br>
      Expéditeur SMTP : {escape(settings.SMTP_USER)}
    </p>
    <p>Si vous recevez ce message, la livraison SMTP fonctionne. Vérifiez aussi le dossier spam.</p>
    """
    return send_email(
        to,
        "My Madec — Test SMTP au démarrage",
        _wrap_html("Test SMTP", body),
        plain=plain,
    )


def send_welcome_email(to: str, full_name: str, password: str) -> bool:
    login_url = f"{settings.frontend_base_url}/login"
    plain = (
        f"Bienvenue sur My Madec, {full_name} !\n\n"
        f"Votre compte a été créé. Vos identifiants :\n"
        f"  Email       : {to}\n"
        f"  Mot de passe: {password}\n\n"
        f"Changez votre mot de passe dès votre première connexion.\n"
        f"Connexion : {login_url}"
    )
    body = f"""
    <h2 style="margin:0 0 12px;font-size:20px;color:#0f172a;">Bienvenue, {escape(full_name)} !</h2>
    <p>Votre compte My Madec a été créé. Voici vos identifiants de connexion :</p>
    <table style="margin:16px 0;background:#f8fafc;border-radius:12px;padding:16px;width:100%;">
      <tr><td style="padding:4px 0;color:#64748b;">Email</td>
          <td style="padding:4px 0;font-weight:600;">{escape(to)}</td></tr>
      <tr><td style="padding:4px 0;color:#64748b;">Mot de passe</td>
          <td style="padding:4px 0;font-family:monospace;font-weight:600;">{escape(password)}</td></tr>
    </table>
    <p style="color:#64748b;font-size:14px;">Changez votre mot de passe dès votre première connexion.</p>
    {_button(login_url, "Se connecter")}
    """
    return send_email(
        to, "Bienvenue sur My Madec — vos identifiants",
        _wrap_html("Bienvenue", body), plain=plain,
    )


def send_admin_password_reset_email(to: str, full_name: str, password: str) -> bool:
    """Used when an admin resets a user's password — framed as a reset, not account creation."""
    login_url = f"{settings.frontend_base_url}/login"
    plain = (
        f"Bonjour {full_name},\n\n"
        f"Un administrateur a réinitialisé votre mot de passe My Madec.\n\n"
        f"Vos nouveaux identifiants :\n"
        f"  Email       : {to}\n"
        f"  Mot de passe: {password}\n\n"
        f"Changez votre mot de passe dès votre prochaine connexion.\n"
        f"Connexion : {login_url}\n\n"
        f"Si vous n'attendiez pas ce changement, contactez votre administrateur."
    )
    body = f"""
    <h2 style="margin:0 0 12px;font-size:20px;color:#0f172a;">Mot de passe réinitialisé</h2>
    <p>Bonjour {escape(full_name)},</p>
    <p>Un administrateur a réinitialisé votre mot de passe My Madec. Voici vos nouveaux identifiants :</p>
    <table style="margin:16px 0;background:#f8fafc;border-radius:12px;padding:16px;width:100%;">
      <tr><td style="padding:4px 0;color:#64748b;">Email</td>
          <td style="padding:4px 0;font-weight:600;">{escape(to)}</td></tr>
      <tr><td style="padding:4px 0;color:#64748b;">Mot de passe</td>
          <td style="padding:4px 0;font-family:monospace;font-weight:600;">{escape(password)}</td></tr>
    </table>
    <p style="color:#64748b;font-size:14px;">Changez votre mot de passe dès votre prochaine connexion.</p>
    {_button(login_url, "Se connecter")}
    <p style="color:#94a3b8;font-size:13px;">Si vous n'attendiez pas ce changement, contactez votre administrateur immédiatement.</p>
    """
    return send_email(
        to, "My Madec — Votre mot de passe a été réinitialisé",
        _wrap_html("Mot de passe réinitialisé", body), plain=plain,
    )


def send_password_reset_email(to: str, full_name: str, reset_token: str) -> bool:
    # Mobile deep link — opens the app reset screen (not the admin web panel).
    reset_url = settings.mobile_password_reset_url(reset_token)
    plain = (
        f"Bonjour {full_name},\n\n"
        f"Voici votre code de réinitialisation My Madec :\n\n"
        f"  {reset_token}\n\n"
        f"Ou ouvrez ce lien dans l'application : {reset_url}\n\n"
        f"Ce code est valable {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} heures.\n"
        f"Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
    )
    body = f"""
    <h2 style="margin:0 0 12px;font-size:20px;color:#0f172a;">Réinitialisation du mot de passe</h2>
    <p>Bonjour {escape(full_name)},</p>
    <p>Vous avez demandé à réinitialiser votre mot de passe My Madec.</p>
    {_button(reset_url, "Réinitialiser mon mot de passe")}
    <p>Ou copiez ce code sur la page de réinitialisation :</p>
    <p style="margin:12px 0;padding:12px 16px;background:#f1f5f9;border-radius:8px;font-family:monospace;
       font-size:14px;word-break:break-all;">{escape(reset_token)}</p>
    <p style="color:#64748b;font-size:13px;">Ce lien est valable {settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS} heures.
    Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.</p>
    """
    return send_email(
        to, "My Madec — Réinitialisation de mot de passe",
        _wrap_html("Réinitialisation", body), plain=plain,
    )


def send_order_status_email(
    to: str,
    full_name: str,
    order_code: str,
    status_label: str,
    *,
    ready: bool = False,
) -> bool:
    login_url = f"{settings.frontend_base_url}/login"
    if ready:
        subject = f"My Madec — Commande {order_code} prête à récupérer"
        plain = (
            f"Bonjour {full_name},\n\n"
            f"Votre commande {order_code} est prête.\n"
            f"Présentez-vous pour la récupérer ou procédez au paiement par carte.\n\n"
            f"Connexion : {login_url}"
        )
        body = f"""
        <h2 style="margin:0 0 12px;font-size:20px;color:#0f172a;">Commande prête à récupérer</h2>
        <p>Bonjour {escape(full_name)},</p>
        <p>Votre commande <strong>{escape(order_code)}</strong> est prête.</p>
        <p>Présentez-vous pour la récupérer ou procédez au paiement par carte.</p>
        {_button(login_url, "Voir ma commande")}
        """
    else:
        subject = f"My Madec — Commande {order_code} : {status_label}"
        plain = (
            f"Bonjour {full_name},\n\n"
            f"Le statut de votre commande {order_code} a été mis à jour : {status_label}.\n\n"
            f"Connexion : {login_url}"
        )
        body = f"""
        <h2 style="margin:0 0 12px;font-size:20px;color:#0f172a;">Mise à jour de commande</h2>
        <p>Bonjour {escape(full_name)},</p>
        <p>Le statut de votre commande <strong>{escape(order_code)}</strong> est maintenant :
           <strong>{escape(status_label)}</strong>.</p>
        {_button(login_url, "Voir ma commande")}
        """
    return send_email(
        to, subject, _wrap_html("Mise à jour de commande", body), plain=plain,
    )


def send_password_changed_email(to: str, full_name: str) -> bool:
    login_url = f"{settings.frontend_base_url}/login"
    plain = (
        f"Bonjour {full_name},\n\n"
        f"Votre mot de passe My Madec a été modifié avec succès.\n\n"
        f"Si vous n'êtes pas à l'origine de ce changement, contactez votre administrateur immédiatement.\n"
        f"Connexion : {login_url}"
    )
    body = f"""
    <h2 style="margin:0 0 12px;font-size:20px;color:#0f172a;">Mot de passe modifié</h2>
    <p>Bonjour {escape(full_name)},</p>
    <p>Votre mot de passe My Madec a été modifié avec succès.</p>
    <p style="color:#64748b;font-size:14px;">Si vous n'êtes pas à l'origine de ce changement,
    contactez votre administrateur immédiatement.</p>
    {_button(login_url, "Se connecter")}
    """
    return send_email(
        to, "My Madec — Mot de passe modifié",
        _wrap_html("Mot de passe modifié", body), plain=plain,
    )
