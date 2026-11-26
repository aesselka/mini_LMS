"""
Отправка писем через HTTP API сервиса Resend (https://resend.com).

Используем API, а не SMTP: в некоторых сетях SMTP-порты блокируются
(антивирус или провайдер), а обычный HTTPS работает везде.
Ключ берётся из переменной окружения RESEND_API_KEY (см. settings.py).
"""
import json
import urllib.error
import urllib.request

from django.core.mail.backends.base import BaseEmailBackend

RESEND_URL = 'https://api.resend.com/emails'


class ResendEmailBackend(BaseEmailBackend):
    def __init__(self, *, api_key=None, fail_silently=False, **kwargs):
        # Django 6.1 не принимает fail_silently в базовом классе — храним сами
        super().__init__(**kwargs)
        self.fail_silently = fail_silently
        self.api_key = api_key

    def _payload(self, message):
        data = {
            'from': message.from_email,
            'to': list(message.to),
            'subject': message.subject,
            'text': message.body,
        }
        if message.cc:
            data['cc'] = list(message.cc)
        if message.bcc:
            data['bcc'] = list(message.bcc)
        # HTML-версия письма (send_mail(..., html_message=...))
        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                data['html'] = content
        return data

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            if not message.recipients():
                continue
            request = urllib.request.Request(
                RESEND_URL,
                data=json.dumps(self._payload(message)).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'mini-lms/1.0',
                },
                method='POST',
            )
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    if 200 <= response.status < 300:
                        sent += 1
            except urllib.error.HTTPError as exc:
                if not self.fail_silently:
                    detail = exc.read().decode('utf-8', 'replace')
                    raise RuntimeError(f'Resend error {exc.code}: {detail}') from exc
            except Exception:
                if not self.fail_silently:
                    raise
        return sent
