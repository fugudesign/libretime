from datetime import datetime, timedelta, timezone

from django.conf import settings
from model_bakery import baker
from rest_framework.test import APITestCase


class TestStationsView(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/stations"
        cls.token = settings.CONFIG.general.api_key

    def test_stations_list(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.token}")
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        first = data[0]
        self.assertIn("id", first)
        self.assertIn("name", first)

    def test_stations_unauthenticated(self):
        response = self.client.get(self.path)
        self.assertEqual(response.status_code, 403)


class TestScheduleStationIdFilter(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.path = "/api/v2/schedule"
        cls.token = settings.CONFIG.general.api_key

    def test_filter_by_station_id(self):
        show1 = baker.make("schedule.Show", station_id=1)
        show2 = baker.make("schedule.Show", station_id=2)
        now = datetime.now(tz=timezone.utc)
        instance1 = baker.make(
            "schedule.ShowInstance",
            show=show1,
            starts_at=now - timedelta(minutes=5),
            ends_at=now + timedelta(minutes=5),
        )
        instance2 = baker.make(
            "schedule.ShowInstance",
            show=show2,
            starts_at=now - timedelta(minutes=5),
            ends_at=now + timedelta(minutes=5),
        )
        baker.make("schedule.Schedule", instance=instance1, starts_at=now)
        baker.make("schedule.Schedule", instance=instance2, starts_at=now)

        self.client.credentials(HTTP_AUTHORIZATION=f"Api-Key {self.token}")

        resp1 = self.client.get(self.path, {"station_id": 1})
        self.assertEqual(resp1.status_code, 200)
        ids1 = {item["instance"] for item in resp1.json()}

        resp2 = self.client.get(self.path, {"station_id": 2})
        self.assertEqual(resp2.status_code, 200)
        ids2 = {item["instance"] for item in resp2.json()}

        self.assertFalse(ids1.intersection(ids2), "Stations should not share schedule items")
