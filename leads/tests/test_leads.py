import json
import unittest
from pathlib import Path

from aiohttp.test_utils import TestClient, TestServer

from hav_bot.api import create_app
from hav_bot.keyboards import lead_keyboard, main_menu
from hav_bot.leads import build_text, origin_allowed, rate_limited, reset_limits, validate, with_status


class LeadTests(unittest.TestCase):
    def setUp(self):
        reset_limits()

    def test_validate_and_escape(self):
        lead, error = validate(
            {"name": "Іван", "email": "ivan@example.com", "phone": "+380 00", "message": "Привіт <b>"}
        )
        self.assertIsNone(error)
        text = build_text(lead)
        self.assertIn("&lt;b&gt;", text)
        self.assertNotIn("<b>Привіт", text)
        self.assertIn("Статус:", text)
        lead, error = validate({"name": "Іван", "email": "ivan@example.com", "topic": "BAS"})
        self.assertEqual(lead["topic"], "BAS")
        self.assertIn("BAS", build_text(lead))
        lead, error = validate({"name": "Іван", "email": "ivan@example.com", "topic": "<b>"})
        self.assertEqual(lead["topic"], "")

    def test_status_replace(self):
        lead, _ = validate({"name": "Іван", "email": "ivan@example.com"})
        updated = with_status(build_text(lead), "Закрито")
        self.assertIn("<b>Статус:</b> Закрито", updated)
        self.assertNotIn("<b>Статус:</b> Нова", updated)
        self.assertIn("Нова заявка", updated)

    def test_honeypot_and_bad_email(self):
        lead, error = validate({"name": "Іван", "email": "ivan@example.com", "hp": "spam"})
        self.assertIsNone(error)
        self.assertTrue(lead["honeypot"])
        lead, error = validate({"name": "Іван", "email": "not-an-email"})
        self.assertIsNone(lead)
        self.assertIn("email", error)

    def test_rate_limit(self):
        for _ in range(5):
            self.assertFalse(rate_limited("10.0.0.8"))
        self.assertTrue(rate_limited("10.0.0.8"))

    def test_origin(self):
        self.assertTrue(origin_allowed(None, "hav.com.ua"))
        self.assertTrue(origin_allowed("https://hav.com.ua", "hav.com.ua"))
        self.assertFalse(origin_allowed("https://evil.example", "hav.com.ua"))

    def test_keyboards(self):
        menu = main_menu("https://hav.com.ua")
        callbacks = [button.callback_data for row in menu.inline_keyboard for button in row]
        self.assertIn("menu:apply", callbacks)
        keyboard = lead_keyboard({"topic": "Odoo"}, "https://hav.com.ua")
        datas = [button.callback_data or button.url for row in keyboard.inline_keyboard for button in row]
        self.assertIn("lead:work", datas)
        self.assertIn("lead:done", datas)
        self.assertTrue(all(len(item or "") <= 64 for item in datas))

    def test_content_file(self):
        content = json.loads((Path(__file__).resolve().parents[2] / "content.json").read_text(encoding="utf-8"))
        for key in ("hero", "stats", "services", "tech", "process", "cases", "contact", "footer"):
            self.assertIn(key, content)
        self.assertEqual([item["title"] for item in content["systems"]["items"]], ["ERP", "BAS", "Odoo"])
        self.assertEqual(
            [item["title"] for item in content["products"]["items"]],
            ["Avocado Trade", "Avocado Inventory", "Лояльність"],
        )


class HttpTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        reset_limits()
        self.sent = []

        async def publish(lead):
            self.sent.append(lead)

        self.publish = publish

    async def _client(self, configured: bool) -> TestClient:
        app = create_app(self.publish, configured=configured)
        client = TestClient(TestServer(app))
        await client.start_server()
        self.addAsyncCleanup(client.close)
        return client

    async def test_http_flow(self):
        closed = await self._client(False)
        honeypot = await closed.post(
            "/api/lead",
            json={"name": "Іван", "email": "ivan@example.com", "hp": "bot"},
            headers={"X-Real-IP": "10.1.1.1"},
        )
        self.assertEqual(honeypot.status, 200)
        self.assertEqual(self.sent, [])

        missing = await closed.post(
            "/api/lead",
            json={"name": "Іван", "email": "ivan@example.com"},
            headers={"X-Real-IP": "10.1.1.1"},
        )
        self.assertEqual(missing.status, 503)

        opened = await self._client(True)
        ok = await opened.post(
            "/api/lead",
            json={"name": "Марія", "email": "maria@example.com", "message": "Міграція"},
            headers={"X-Real-IP": "10.2.2.2"},
        )
        self.assertEqual(ok.status, 200)
        self.assertEqual(self.sent[-1]["email"], "maria@example.com")

        denied = await opened.post(
            "/api/lead",
            json={"name": "Марія", "email": "maria@example.com"},
            headers={"Origin": "https://evil.example", "X-Real-IP": "10.3.3.3"},
        )
        self.assertEqual(denied.status, 403)


if __name__ == "__main__":
    unittest.main()
