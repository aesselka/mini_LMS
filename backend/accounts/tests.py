from django.test import TestCase
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class AuthThrottlingTest(APITestCase):
    def setUp(self):
        cache.clear()  # очищаем счётчик перед каждым тестом

    def test_login_bruteforce_protection(self):
        url = reverse('login')
        data = {'username': 'wronguser', 'password': 'wrongpassword'}

        # Первые 5 попыток возвращают 401
        for _ in range(5):
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 6-я попытка блокируется со статусом 429 Too Many Requests
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)