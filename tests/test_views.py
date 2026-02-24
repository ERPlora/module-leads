"""Tests for leads views."""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestDashboard:
    """Dashboard view tests."""

    def test_dashboard_loads(self, auth_client):
        """Test dashboard page loads."""
        url = reverse('leads:dashboard')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_dashboard_htmx(self, auth_client):
        """Test dashboard HTMX partial."""
        url = reverse('leads:dashboard')
        response = auth_client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_dashboard_requires_auth(self, client):
        """Test dashboard requires authentication."""
        url = reverse('leads:dashboard')
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestPipelineViews:
    """Pipeline view tests."""

    def test_list_loads(self, auth_client):
        """Test list view loads."""
        url = reverse('leads:pipelines_list')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_list_htmx(self, auth_client):
        """Test list HTMX partial."""
        url = reverse('leads:pipelines_list')
        response = auth_client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_list_search(self, auth_client):
        """Test list search."""
        url = reverse('leads:pipelines_list')
        response = auth_client.get(url, {'q': 'test'})
        assert response.status_code == 200

    def test_list_sort(self, auth_client):
        """Test list sorting."""
        url = reverse('leads:pipelines_list')
        response = auth_client.get(url, {'sort': 'created_at', 'dir': 'desc'})
        assert response.status_code == 200

    def test_export_csv(self, auth_client):
        """Test CSV export."""
        url = reverse('leads:pipelines_list')
        response = auth_client.get(url, {'export': 'csv'})
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']

    def test_export_excel(self, auth_client):
        """Test Excel export."""
        url = reverse('leads:pipelines_list')
        response = auth_client.get(url, {'export': 'excel'})
        assert response.status_code == 200

    def test_add_form_loads(self, auth_client):
        """Test add form loads."""
        url = reverse('leads:pipeline_add')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_add_post(self, auth_client):
        """Test creating via POST."""
        url = reverse('leads:pipeline_add')
        data = {
            'name': 'New Name',
            'description': 'Test description',
            'is_default': 'on',
            'is_active': 'on',
        }
        response = auth_client.post(url, data)
        assert response.status_code == 200

    def test_edit_form_loads(self, auth_client, pipeline):
        """Test edit form loads."""
        url = reverse('leads:pipeline_edit', args=[pipeline.pk])
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_edit_post(self, auth_client, pipeline):
        """Test editing via POST."""
        url = reverse('leads:pipeline_edit', args=[pipeline.pk])
        data = {
            'name': 'Updated Name',
            'description': 'Test description',
            'is_default': '',
            'is_active': '',
        }
        response = auth_client.post(url, data)
        assert response.status_code == 200

    def test_delete(self, auth_client, pipeline):
        """Test soft delete via POST."""
        url = reverse('leads:pipeline_delete', args=[pipeline.pk])
        response = auth_client.post(url)
        assert response.status_code == 200
        pipeline.refresh_from_db()
        assert pipeline.is_deleted is True

    def test_toggle_status(self, auth_client, pipeline):
        """Test toggle active status."""
        url = reverse('leads:pipeline_toggle_status', args=[pipeline.pk])
        original = pipeline.is_active
        response = auth_client.post(url)
        assert response.status_code == 200
        pipeline.refresh_from_db()
        assert pipeline.is_active != original

    def test_bulk_delete(self, auth_client, pipeline):
        """Test bulk delete."""
        url = reverse('leads:pipelines_bulk_action')
        response = auth_client.post(url, {'ids': str(pipeline.pk), 'action': 'delete'})
        assert response.status_code == 200
        pipeline.refresh_from_db()
        assert pipeline.is_deleted is True

    def test_list_requires_auth(self, client):
        """Test list requires authentication."""
        url = reverse('leads:pipelines_list')
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestLossReasonViews:
    """LossReason view tests."""

    def test_list_loads(self, auth_client):
        """Test list view loads."""
        url = reverse('leads:loss_reasons_list')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_list_htmx(self, auth_client):
        """Test list HTMX partial."""
        url = reverse('leads:loss_reasons_list')
        response = auth_client.get(url, HTTP_HX_REQUEST='true')
        assert response.status_code == 200

    def test_list_search(self, auth_client):
        """Test list search."""
        url = reverse('leads:loss_reasons_list')
        response = auth_client.get(url, {'q': 'test'})
        assert response.status_code == 200

    def test_list_sort(self, auth_client):
        """Test list sorting."""
        url = reverse('leads:loss_reasons_list')
        response = auth_client.get(url, {'sort': 'created_at', 'dir': 'desc'})
        assert response.status_code == 200

    def test_export_csv(self, auth_client):
        """Test CSV export."""
        url = reverse('leads:loss_reasons_list')
        response = auth_client.get(url, {'export': 'csv'})
        assert response.status_code == 200
        assert 'text/csv' in response['Content-Type']

    def test_export_excel(self, auth_client):
        """Test Excel export."""
        url = reverse('leads:loss_reasons_list')
        response = auth_client.get(url, {'export': 'excel'})
        assert response.status_code == 200

    def test_add_form_loads(self, auth_client):
        """Test add form loads."""
        url = reverse('leads:loss_reason_add')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_add_post(self, auth_client):
        """Test creating via POST."""
        url = reverse('leads:loss_reason_add')
        data = {
            'name': 'New Name',
            'is_active': 'on',
            'sort_order': '5',
        }
        response = auth_client.post(url, data)
        assert response.status_code == 200

    def test_edit_form_loads(self, auth_client, loss_reason):
        """Test edit form loads."""
        url = reverse('leads:loss_reason_edit', args=[loss_reason.pk])
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_edit_post(self, auth_client, loss_reason):
        """Test editing via POST."""
        url = reverse('leads:loss_reason_edit', args=[loss_reason.pk])
        data = {
            'name': 'Updated Name',
            'is_active': '',
            'sort_order': '5',
        }
        response = auth_client.post(url, data)
        assert response.status_code == 200

    def test_delete(self, auth_client, loss_reason):
        """Test soft delete via POST."""
        url = reverse('leads:loss_reason_delete', args=[loss_reason.pk])
        response = auth_client.post(url)
        assert response.status_code == 200
        loss_reason.refresh_from_db()
        assert loss_reason.is_deleted is True

    def test_toggle_status(self, auth_client, loss_reason):
        """Test toggle active status."""
        url = reverse('leads:loss_reason_toggle_status', args=[loss_reason.pk])
        original = loss_reason.is_active
        response = auth_client.post(url)
        assert response.status_code == 200
        loss_reason.refresh_from_db()
        assert loss_reason.is_active != original

    def test_bulk_delete(self, auth_client, loss_reason):
        """Test bulk delete."""
        url = reverse('leads:loss_reasons_bulk_action')
        response = auth_client.post(url, {'ids': str(loss_reason.pk), 'action': 'delete'})
        assert response.status_code == 200
        loss_reason.refresh_from_db()
        assert loss_reason.is_deleted is True

    def test_list_requires_auth(self, client):
        """Test list requires authentication."""
        url = reverse('leads:loss_reasons_list')
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestSettings:
    """Settings view tests."""

    def test_settings_loads(self, auth_client):
        """Test settings page loads."""
        url = reverse('leads:settings')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_settings_requires_auth(self, client):
        """Test settings requires authentication."""
        url = reverse('leads:settings')
        response = client.get(url)
        assert response.status_code == 302

