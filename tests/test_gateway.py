import unittest
from unittest.mock import patch

import gateway


class GatewayTests(unittest.TestCase):
    def test_build_contact_payload_sets_location_and_defaults(self):
        payload = gateway.build_contact_payload({"email": "a@b.c"}, "loc-1")
        self.assertEqual(payload["locationId"], "loc-1")
        self.assertEqual(payload["email"], "a@b.c")
        self.assertEqual(payload["source"], "api-gateway")

    @patch("gateway.urlopen")
    def test_send_to_ghl_success(self, mock_urlopen):
        class FakeResponse:
            status = 201

            def read(self):
                return b'{"contact": {"id": "123"}}'

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        mock_urlopen.return_value = FakeResponse()
        status, body = gateway.send_to_ghl({"a": 1}, "token")
        self.assertEqual(status, 201)
        self.assertEqual(body["contact"]["id"], "123")


if __name__ == "__main__":
    unittest.main()
