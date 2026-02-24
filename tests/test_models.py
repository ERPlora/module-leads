"""Tests for leads models."""
import pytest
from django.utils import timezone

from leads.models import Pipeline, LossReason


@pytest.mark.django_db
class TestPipeline:
    """Pipeline model tests."""

    def test_create(self, pipeline):
        """Test Pipeline creation."""
        assert pipeline.pk is not None
        assert pipeline.is_deleted is False

    def test_str(self, pipeline):
        """Test string representation."""
        assert str(pipeline) is not None
        assert len(str(pipeline)) > 0

    def test_soft_delete(self, pipeline):
        """Test soft delete."""
        pk = pipeline.pk
        pipeline.is_deleted = True
        pipeline.deleted_at = timezone.now()
        pipeline.save()
        assert not Pipeline.objects.filter(pk=pk).exists()
        assert Pipeline.all_objects.filter(pk=pk).exists()

    def test_queryset_excludes_deleted(self, hub_id, pipeline):
        """Test default queryset excludes deleted."""
        pipeline.is_deleted = True
        pipeline.deleted_at = timezone.now()
        pipeline.save()
        assert Pipeline.objects.filter(hub_id=hub_id).count() == 0

    def test_toggle_active(self, pipeline):
        """Test toggling is_active."""
        original = pipeline.is_active
        pipeline.is_active = not original
        pipeline.save()
        pipeline.refresh_from_db()
        assert pipeline.is_active != original


@pytest.mark.django_db
class TestLossReason:
    """LossReason model tests."""

    def test_create(self, loss_reason):
        """Test LossReason creation."""
        assert loss_reason.pk is not None
        assert loss_reason.is_deleted is False

    def test_str(self, loss_reason):
        """Test string representation."""
        assert str(loss_reason) is not None
        assert len(str(loss_reason)) > 0

    def test_soft_delete(self, loss_reason):
        """Test soft delete."""
        pk = loss_reason.pk
        loss_reason.is_deleted = True
        loss_reason.deleted_at = timezone.now()
        loss_reason.save()
        assert not LossReason.objects.filter(pk=pk).exists()
        assert LossReason.all_objects.filter(pk=pk).exists()

    def test_queryset_excludes_deleted(self, hub_id, loss_reason):
        """Test default queryset excludes deleted."""
        loss_reason.is_deleted = True
        loss_reason.deleted_at = timezone.now()
        loss_reason.save()
        assert LossReason.objects.filter(hub_id=hub_id).count() == 0

    def test_toggle_active(self, loss_reason):
        """Test toggling is_active."""
        original = loss_reason.is_active
        loss_reason.is_active = not original
        loss_reason.save()
        loss_reason.refresh_from_db()
        assert loss_reason.is_active != original


