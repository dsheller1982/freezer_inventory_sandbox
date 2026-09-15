import os
import unittest
from decimal import Decimal
from unittest.mock import patch

import database


class DatabaseHelpersTest(unittest.TestCase):
    def test_quantity_accepts_positive_number(self):
        self.assertEqual(database._positive_quantity("2.5"), Decimal("2.5"))

    def test_quantity_rejects_zero(self):
        with self.assertRaisesRegex(database.DatabaseError, "between 1 and 999"):
            database._positive_quantity(0)

    def test_text_is_trimmed_and_internal_whitespace_collapsed(self):
        self.assertEqual(database._require_text("  Pork   Shoulder  ", "Item", 100), "Pork Shoulder")

    def test_text_is_required(self):
        with self.assertRaisesRegex(database.DatabaseError, "required"):
            database._require_text("   ", "Location", 50)

    def test_railway_variables_are_supported(self):
        railway = {
            "MYSQLHOST": "mysql.railway.internal",
            "MYSQLPORT": "3307",
            "MYSQLUSER": "demo-user",
            "MYSQLPASSWORD": "demo-pass",
            "MYSQLDATABASE": "demo-db",
        }
        with patch.dict(os.environ, railway, clear=True):
            config = database.connection_config()
        self.assertEqual(config["host"], railway["MYSQLHOST"])
        self.assertEqual(config["port"], 3307)
        self.assertEqual(config["user"], railway["MYSQLUSER"])
        self.assertEqual(config["password"], railway["MYSQLPASSWORD"])
        self.assertEqual(config["database"], railway["MYSQLDATABASE"])


if __name__ == "__main__":
    unittest.main()

