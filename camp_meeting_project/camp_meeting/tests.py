from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Contribution

class ContributionModelTest(TestCase):
    def test_str_representation(self):
        contribution = Contribution(full_name="John Doe", amount=500)
        self.assertEqual(str(contribution), "John Doe - Ksh. 500")

    def test_first_name_property(self):
        contribution = Contribution(full_name="Jane Smith")
        self.assertEqual(contribution.first_name, "Jane")

class LandingPageTest(TestCase):
    def test_landing_page_status_code(self):
        response = self.client.get(reverse('camp_meeting:landing'))
        self.assertEqual(response.status_code, 200)

class UserLoginLogoutTest(TestCase):
    def setUp(self):
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(username=self.username, password=self.password)

    def test_login_view(self):
        response = self.client.post(reverse('camp_meeting:login'), {
            'username': self.username,
            'password': self.password
        })
        self.assertEqual(response.status_code, 302)  # Should redirect after login

    def test_logout_view(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('camp_meeting:logout'))
        self.assertEqual(response.status_code, 302)  # Should redirect after logout

class FinanceReportViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="finance", password="financepass")
        self.client.login(username="finance", password="financepass")

    def test_finance_report_access(self):
        response = self.client.get(reverse('camp_meeting:finance_report'))
        self.assertEqual(response.status_code, 200)