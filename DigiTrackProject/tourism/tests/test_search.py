from django.test import TestCase, Client
from django.urls import reverse
from ..models import CustomUser, Homestay, Booking
from datetime import date


class SearchApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user and homestay
        self.user = CustomUser.objects.create_user(username='owner1', password='pass', name='Owner One')
        self.homestay = Homestay.objects.create(owner=self.user, name='Test Homestay', address='Addr')
        # Create bookings via registration
        Booking.objects.create(homestay=self.homestay, date=date(2025,1,1), guest_name='Alice', num_people=2, status='reserved', source='registration')
        Booking.objects.create(homestay=self.homestay, date=date(2025,1,2), guest_name='Bob', num_people=1, status='reserved', source='registration')

    def test_tourist_search_empty_query_returns_all(self):
        url = reverse('api_tourist_search')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # should return at least the two bookings
        self.assertTrue(isinstance(data, list))
        self.assertGreaterEqual(len(data), 2)

    def test_tourist_search_by_name(self):
        url = reverse('api_tourist_search') + '?q=alice'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['guest_name'], 'Alice')

    def test_homestay_search_by_owner(self):
        url = reverse('api_homestay_search') + '?q=owner one'
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success'))
        users = data.get('users')
        self.assertTrue(any(u['homestayName'] == 'Test Homestay' for u in users))
