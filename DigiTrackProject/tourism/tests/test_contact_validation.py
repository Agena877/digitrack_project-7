from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Homestay
from django.urls import reverse
import json

User = get_user_model()

class ContactValidationTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user and homestay
        self.user = User.objects.create_user(username='owner1', password='pass1234', name='Owner One')
        self.homestay = Homestay.objects.create(owner=self.user, name='Test Homestay', address='123 Main St')

    def test_api_register_tourist_rejects_letters_in_contact(self):
        url = reverse('api_register_tourist')
        payload = {
            'name': 'Guest',
            'homestayName': self.homestay.name,
            'contactNumber': '0917ABC1234',
            'region': 'NCR',
            'province': 'Metro',
            'city': 'City',
            'barangay': 'Barangay',
            'dateArrival': '2025-10-20',
            'dateDeparture': '2025-10-20',
            'numTourist': 2
        }
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertFalse(data.get('success', True))
        self.assertIn('Invalid contact number', data.get('error', ''))

    def test_api_register_tourist_accepts_valid_contact(self):
        url = reverse('api_register_tourist')
        payload = {
            'name': 'Guest',
            'homestayName': self.homestay.name,
            'contactNumber': '09171234567',
            'region': 'NCR',
            'province': 'Metro',
            'city': 'City',
            'barangay': 'Barangay',
            'dateArrival': '2025-10-21',
            'dateDeparture': '2025-10-21',
            'numTourist': 2
        }
        resp = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get('success', False))

    def test_form_post_tourist_registration_rejects_letters_in_contact(self):
        url = reverse('register_tourist')
        # Need to login first
        self.client.force_login(self.user)
        payload = {
            'name': 'Guest',
            'homestayName': self.homestay.name,
            'contactNumber': '0917ABC1234',
            'region': 'NCR',
            'province': 'Metro',
            'city': 'City',
            'barangay': 'Barangay',
            'dateArrival': '2025-10-22',
            'dateDeparture': '2025-10-22',
            'numTourist': 2
        }
        resp = self.client.post(url, data=payload, follow=True)
        # Should redirect back with an error message in messages framework (status 200 OK after follow)
        self.assertEqual(resp.status_code, 200)
        # Check that our error message is present in the response content
        content = resp.content.decode('utf-8')
        self.assertIn('Invalid contact number', content)

    def test_form_post_accepts_valid_contact(self):
        url = reverse('register_tourist')
        self.client.force_login(self.user)
        payload = {
            'name': 'Guest',
            'homestayName': self.homestay.name,
            'contactNumber': '09171234567',
            'region': 'NCR',
            'province': 'Metro',
            'city': 'City',
            'barangay': 'Barangay',
            'dateArrival': '2025-10-23',
            'dateDeparture': '2025-10-23',
            'numTourist': 2
        }
        resp = self.client.post(url, data=payload, follow=True)
        self.assertEqual(resp.status_code, 200)
        content = resp.content.decode('utf-8')
        self.assertIn('Tourist registered successfully', content)
