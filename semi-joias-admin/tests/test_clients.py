import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from clients.models import Cliente
from clients.forms import ClienteForm

pytestmark = pytest.mark.django_db


def make_cliente(**kwargs):
    defaults = {
        'first_name': 'Maria',
        'last_name': 'Silva',
        'phone_number': '11999998888',
    }
    defaults.update(kwargs)
    return Cliente.objects.create(**defaults)


# ─── model ────────────────────────────────────────────────────────────────────

class TestClienteModel:

    def test_save_title_cases_first_name(self):
        c = make_cliente(first_name='joao')
        c.refresh_from_db()
        assert c.first_name == 'Joao'

    def test_save_title_cases_last_name(self):
        c = make_cliente(last_name='silva')
        c.refresh_from_db()
        assert c.last_name == 'Silva'

    def test_full_name_property(self):
        c = make_cliente(first_name='Ana', last_name='Souza')
        assert c.full_name == 'Ana Souza'

    def test_str_returns_full_name(self):
        c = make_cliente(first_name='Ana', last_name='Souza')
        assert str(c) == 'Ana Souza'

    def test_formatted_phone_11_digits(self):
        c = make_cliente(phone_number='11999998888')
        assert c.formatted_phone == '(11) 99999-8888'

    def test_name_validator_rejects_digits(self):
        c = Cliente(first_name='Jo4o', last_name='Silva', phone_number='11999998888')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_name_validator_rejects_special_chars(self):
        c = Cliente(first_name='Jo-ao', last_name='Silva', phone_number='11999998888')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_name_validator_rejects_spaces_in_first_name(self):
        c = Cliente(first_name='Jo ao', last_name='Silva', phone_number='11999998888')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_last_name_validator_rejects_digits(self):
        c = Cliente(first_name='Joao', last_name='S1lva', phone_number='11999998888')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_phone_validator_rejects_too_short(self):
        c = Cliente(first_name='Joao', last_name='Silva', phone_number='1199999888')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_phone_validator_rejects_too_long(self):
        c = Cliente(first_name='Joao', last_name='Silva', phone_number='119999988881')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_phone_validator_rejects_letters(self):
        c = Cliente(first_name='Joao', last_name='Silva', phone_number='1199999888a')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_blank_first_name_rejected(self):
        c = Cliente(first_name='', last_name='Silva', phone_number='11999998888')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_blank_last_name_rejected(self):
        c = Cliente(first_name='Joao', last_name='', phone_number='11999998888')
        with pytest.raises(ValidationError):
            c.full_clean()

    def test_valid_cliente_passes_full_clean(self):
        c = Cliente(first_name='Joao', last_name='Silva', phone_number='11999998888')
        c.full_clean()


# ─── queryset ─────────────────────────────────────────────────────────────────

class TestClienteQuerySet:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.c1 = make_cliente(first_name='Ana', last_name='Silva', phone_number='11999998888')
        self.c2 = make_cliente(first_name='Bruno', last_name='Costa', phone_number='21988887777')
        self.c3 = make_cliente(first_name='Carla', last_name='Ferreira', phone_number='31977776666')

    def test_no_params_returns_all(self):
        assert Cliente.objects.param_filter().count() == 3

    def test_filter_by_nome_first_name(self):
        qs = Cliente.objects.param_filter(nome='Ana')
        assert self.c1 in qs
        assert self.c2 not in qs

    def test_filter_by_nome_last_name(self):
        qs = Cliente.objects.param_filter(nome='Costa')
        assert self.c2 in qs
        assert self.c1 not in qs

    def test_filter_by_nome_full_name(self):
        qs = Cliente.objects.param_filter(nome='Ana Silva')
        assert self.c1 in qs
        assert self.c2 not in qs

    def test_filter_by_nome_case_insensitive(self):
        qs = Cliente.objects.param_filter(nome='ana')
        assert self.c1 in qs

    def test_filter_by_celular_exact(self):
        qs = Cliente.objects.param_filter(celular='21988887777')
        assert self.c2 in qs
        assert self.c1 not in qs

    def test_filter_by_celular_partial(self):
        qs = Cliente.objects.param_filter(celular='219')
        assert self.c2 in qs
        assert self.c1 not in qs

    def test_filter_combined_nome_and_celular_intersection(self):
        qs = Cliente.objects.param_filter(nome='Bruno', celular='21')
        assert self.c2 in qs
        assert self.c1 not in qs

    def test_filter_combined_nome_celular_no_intersection(self):
        qs = Cliente.objects.param_filter(nome='Ana', celular='219')
        assert qs.count() == 0

    def test_filter_no_match_returns_empty(self):
        qs = Cliente.objects.param_filter(nome='Inexistente')
        assert qs.count() == 0

    def test_empty_string_params_treated_as_no_filter(self):
        qs = Cliente.objects.param_filter(nome='', celular='')
        assert qs.count() == 3


# ─── form ─────────────────────────────────────────────────────────────────────

class TestClienteForm:

    def test_valid_form(self):
        form = ClienteForm(data={
            'first_name': 'Joao',
            'last_name': 'Silva',
            'phone_number': '11999998888',
        })
        assert form.is_valid()

    def test_form_rejects_name_with_digit(self):
        form = ClienteForm(data={
            'first_name': 'Jo3o',
            'last_name': 'Silva',
            'phone_number': '11999998888',
        })
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_form_rejects_short_phone(self):
        form = ClienteForm(data={
            'first_name': 'Joao',
            'last_name': 'Silva',
            'phone_number': '119999988',
        })
        assert not form.is_valid()
        assert 'phone_number' in form.errors

    def test_form_rejects_long_phone(self):
        form = ClienteForm(data={
            'first_name': 'Joao',
            'last_name': 'Silva',
            'phone_number': '119999988881',
        })
        assert not form.is_valid()
        assert 'phone_number' in form.errors

    def test_form_rejects_blank_first_name(self):
        form = ClienteForm(data={
            'first_name': '',
            'last_name': 'Silva',
            'phone_number': '11999998888',
        })
        assert not form.is_valid()
        assert 'first_name' in form.errors

    def test_form_rejects_blank_last_name(self):
        form = ClienteForm(data={
            'first_name': 'Joao',
            'last_name': '',
            'phone_number': '11999998888',
        })
        assert not form.is_valid()
        assert 'last_name' in form.errors


# ─── views ────────────────────────────────────────────────────────────────────

class TestExibirClientes:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.c1 = make_cliente(first_name='Ana', last_name='Silva', phone_number='11999998888')
        self.c2 = make_cliente(first_name='Bruno', last_name='Costa', phone_number='21988887777')

    def test_get_lists_all_clients(self):
        response = self.http.get(reverse('clients:lista'))
        assert response.status_code == 200
        assert 'Ana' in response.content.decode()
        assert 'Bruno' in response.content.decode()

    def test_get_with_nome_filter(self):
        response = self.http.get(reverse('clients:lista'), {'nome': 'Ana'})
        assert 'Ana' in response.content.decode()
        assert 'Bruno' not in response.content.decode()

    def test_get_with_celular_filter(self):
        response = self.http.get(reverse('clients:lista'), {'celular': '219'})
        assert 'Bruno' in response.content.decode()
        assert 'Ana' not in response.content.decode()


class TestCadastrarCliente:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.url = reverse('clients:criar')

    def test_get_renders_form(self):
        response = self.http.get(self.url)
        assert response.status_code == 200

    def test_post_valid_creates_and_redirects(self):
        response = self.http.post(self.url, {
            'first_name': 'Joao',
            'last_name': 'Silva',
            'phone_number': '11999998888',
        })
        assert response.status_code == 302
        assert response.url == reverse('clients:lista')
        assert Cliente.objects.filter(phone_number='11999998888').exists()

    def test_post_invalid_name_does_not_create(self):
        self.http.post(self.url, {
            'first_name': 'J0ao',
            'last_name': 'Silva',
            'phone_number': '11999998888',
        })
        assert Cliente.objects.count() == 0

    def test_post_invalid_phone_does_not_create(self):
        self.http.post(self.url, {
            'first_name': 'Joao',
            'last_name': 'Silva',
            'phone_number': '119',
        })
        assert Cliente.objects.count() == 0

    def test_post_invalid_re_renders_with_errors(self):
        response = self.http.post(self.url, {
            'first_name': 'J0ao',
            'last_name': 'Silva',
            'phone_number': '11999998888',
        })
        assert response.status_code == 200
        assert response.context['form'].errors


class TestAtualizarCliente:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.cliente = make_cliente()
        self.url = reverse('clients:atualizar', args=[self.cliente.id])

    def test_get_renders_form_pre_filled(self):
        response = self.http.get(self.url)
        assert response.status_code == 200
        assert self.cliente.first_name in response.content.decode()

    def test_post_valid_updates_and_redirects(self):
        response = self.http.post(self.url, {
            'first_name': 'Joana',
            'last_name': 'Santos',
            'phone_number': '11888887777',
        })
        assert response.status_code == 302
        assert response.url == reverse('clients:lista')
        self.cliente.refresh_from_db()
        assert self.cliente.first_name == 'Joana'

    def test_post_invalid_does_not_update(self):
        self.http.post(self.url, {
            'first_name': 'J0ana',
            'last_name': 'Santos',
            'phone_number': '11888887777',
        })
        self.cliente.refresh_from_db()
        assert self.cliente.first_name == 'Maria'

    def test_post_invalid_re_renders_with_errors(self):
        response = self.http.post(self.url, {
            'first_name': 'J0ana',
            'last_name': 'Santos',
            'phone_number': '11888887777',
        })
        assert response.status_code == 200
        assert response.context['form'].errors

    def test_404_for_nonexistent_client(self):
        response = self.http.get(reverse('clients:atualizar', args=[9999]))
        assert response.status_code == 404


class TestDeletarCliente:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client):
        self.http = auth_client
        self.cliente = make_cliente()
        self.url = reverse('clients:deletar', args=[self.cliente.id])

    def test_post_deletes_and_redirects(self):
        response = self.http.post(self.url)
        assert response.status_code == 302
        assert response.url == reverse('clients:lista')
        assert not Cliente.objects.filter(id=self.cliente.id).exists()

    def test_get_does_not_delete(self):
        self.http.get(self.url)
        assert Cliente.objects.filter(id=self.cliente.id).exists()

    def test_get_redirects_without_deleting(self):
        response = self.http.get(self.url)
        assert response.status_code == 302
        assert response.url == reverse('clients:lista')
        assert Cliente.objects.count() == 1

    def test_404_for_nonexistent_client(self):
        response = self.http.post(reverse('clients:deletar', args=[9999]))
        assert response.status_code == 404
