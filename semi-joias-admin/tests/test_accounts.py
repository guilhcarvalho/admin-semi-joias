import pytest
from django.urls import reverse

LOGIN_URL = reverse('accounts:login')
LOGOUT_URL = reverse('accounts:logout')
MALETAS_URL = reverse('sales:maletas_lista')

pytestmark = pytest.mark.django_db


class TestLoginView:

    @pytest.fixture(autouse=True)
    def setup(self, client, django_user_model):
        self.http = client
        self.user = django_user_model.objects.create_user('carol', password='senha123')

    def test_get_renders_form(self):
        response = self.http.get(LOGIN_URL)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_get_already_authenticated_redirects_to_maletas(self):
        self.http.force_login(self.user)
        response = self.http.get(LOGIN_URL)
        assert response.status_code == 302
        assert response.url == MALETAS_URL

    def test_post_valid_credentials_redirects_to_maletas(self):
        response = self.http.post(LOGIN_URL, {'username': 'carol', 'password': 'senha123'})
        assert response.status_code == 302
        assert response.url == MALETAS_URL

    def test_post_valid_credentials_logs_user_in(self):
        self.http.post(LOGIN_URL, {'username': 'carol', 'password': 'senha123'})
        response = self.http.get(MALETAS_URL)
        assert response.status_code == 200

    def test_post_valid_with_next_redirects_to_next(self):
        next_url = reverse('clients:lista')
        response = self.http.post(LOGIN_URL, {
            'username': 'carol',
            'password': 'senha123',
            'next': next_url,
        })
        assert response.status_code == 302
        assert response.url == next_url

    def test_post_unsafe_next_redirects_to_maletas(self):
        response = self.http.post(LOGIN_URL, {
            'username': 'carol',
            'password': 'senha123',
            'next': 'https://evil.com/phishing',
        })
        assert response.status_code == 302
        assert response.url == MALETAS_URL

    def test_post_invalid_password_rerenders_form(self):
        response = self.http.post(LOGIN_URL, {'username': 'carol', 'password': 'errada'})
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_post_invalid_username_rerenders_form(self):
        response = self.http.post(LOGIN_URL, {'username': 'inexistente', 'password': 'senha123'})
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_post_missing_username_rerenders_form(self):
        response = self.http.post(LOGIN_URL, {'password': 'senha123'})
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_post_missing_password_rerenders_form(self):
        response = self.http.post(LOGIN_URL, {'username': 'carol'})
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_post_empty_body_rerenders_form(self):
        response = self.http.post(LOGIN_URL, {})
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_get_with_next_passes_next_to_context(self):
        next_url = reverse('clients:lista')
        response = self.http.get(f'{LOGIN_URL}?next={next_url}')
        assert response.status_code == 200
        assert response.context['next'] == next_url


class TestLogoutView:

    @pytest.fixture(autouse=True)
    def setup(self, client, django_user_model):
        self.http = client
        self.user = django_user_model.objects.create_user('carol', password='senha123')

    def test_post_logs_out_and_redirects_to_login(self):
        self.http.force_login(self.user)
        response = self.http.post(LOGOUT_URL)
        assert response.status_code == 302
        assert response.url == LOGIN_URL

    def test_post_session_cleared_after_logout(self):
        self.http.force_login(self.user)
        self.http.post(LOGOUT_URL)
        response = self.http.get(MALETAS_URL)
        assert response.status_code == 302
        assert response.url == f'{LOGIN_URL}?next={MALETAS_URL}'

    def test_get_does_not_log_out(self):
        self.http.force_login(self.user)
        self.http.get(LOGOUT_URL)
        response = self.http.get(MALETAS_URL)
        assert response.status_code == 200

    def test_post_unauthenticated_redirects_to_login(self):
        response = self.http.post(LOGOUT_URL)
        assert response.status_code == 302
        assert response.url == LOGIN_URL
