import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import app


class LeadTests(unittest.TestCase):
    def setUp(self):
        app.reset_limits()
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)
        os.environ.pop("TELEGRAM_CHAT_ID", None)

    def test_validate_and_escape(self):
        lead, error = app.validate(
            {"name": "Іван", "email": "ivan@example.com", "phone": "+380 00", "message": "Привіт <b>"}
        )
        self.assertIsNone(error)
        self.assertIn("&lt;b&gt;", app.build_text(lead))
        self.assertNotIn("<b>Привіт", app.build_text(lead))
        lead, error = app.validate(
            {"name": "Іван", "email": "ivan@example.com", "topic": "BAS"}
        )
        self.assertEqual(lead["topic"], "BAS")
        self.assertIn("BAS", app.build_text(lead))
        lead, error = app.validate(
            {"name": "Іван", "email": "ivan@example.com", "topic": "<b>"}
        )
        self.assertEqual(lead["topic"], "")

    def test_honeypot_and_bad_email(self):
        lead, error = app.validate({"name": "Іван", "email": "ivan@example.com", "hp": "spam"})
        self.assertIsNone(error)
        self.assertTrue(lead["honeypot"])
        lead, error = app.validate({"name": "Іван", "email": "not-an-email"})
        self.assertIsNone(lead)
        self.assertIn("email", error)

    def test_rate_limit(self):
        for _ in range(5):
            self.assertFalse(app.rate_limited("10.0.0.8"))
        self.assertTrue(app.rate_limited("10.0.0.8"))

    def test_origin(self):
        self.assertTrue(app.origin_allowed(None, "hav.com.ua"))
        self.assertTrue(app.origin_allowed("https://hav.com.ua", "hav.com.ua"))
        self.assertFalse(app.origin_allowed("https://evil.example", "hav.com.ua"))

    def test_content_file(self):
        content = json.loads((Path(__file__).resolve().parents[1] / "content.json").read_text(encoding="utf-8"))
        for key in ("hero", "stats", "services", "tech", "process", "cases", "contact", "footer"):
            self.assertIn(key, content)
        self.assertGreaterEqual(len(content["services"]["items"]), 1)
        self.assertEqual([item["title"] for item in content["systems"]["items"]], ["ERP", "BAS", "Odoo"])
        self.assertIn("@", content["contact"]["email"])

    def test_http_flow(self):
        sent = []
        original = app.send_to_telegram
        app.send_to_telegram = lambda lead: sent.append(lead)
        self.addCleanup(lambda: setattr(app, "send_to_telegram", original))
        server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        port = server.server_address[1]

        def post(payload, headers=None):
            body = json.dumps(payload).encode()
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)
            request = urllib.request.Request(
                f"http://127.0.0.1:{port}/api/lead",
                data=body,
                headers=request_headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(request) as response:
                    return response.status, json.loads(response.read().decode())
            except urllib.error.HTTPError as exc:
                return exc.code, json.loads(exc.read().decode())

        status, body = post({"name": "Іван", "email": "ivan@example.com", "hp": "bot"})
        self.assertEqual(status, 200)
        self.assertEqual(sent, [])

        status, body = post({"name": "Іван", "email": "ivan@example.com"})
        self.assertEqual(status, 503)

        os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ["TELEGRAM_CHAT_ID"] = "1"
        status, body = post(
            {"name": "Марія", "email": "maria@example.com", "message": "Міграція"},
            {"Origin": "https://hav.com.ua", "Host": "hav.com.ua"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(sent[-1]["email"], "maria@example.com")

        status, body = post(
            {"name": "Марія", "email": "maria@example.com"},
            {"Origin": "https://evil.example", "Host": "hav.com.ua"},
        )
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
