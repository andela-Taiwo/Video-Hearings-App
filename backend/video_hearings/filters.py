import django_filters
from .models import Hearing


class HearingFilter(django_filters.FilterSet):
    """Filter set for Hearing model"""

    name = django_filters.CharFilter(field_name="name", lookup_expr="icontains")
    date_from = django_filters.DateTimeFilter(
        field_name="scheduled_at", lookup_expr="gte"
    )
    date_to = django_filters.DateTimeFilter(
        field_name="scheduled_at", lookup_expr="lte"
    )
    case_number = django_filters.CharFilter(
        field_name="case__case_number", lookup_expr="icontains"
    )
    courtroom_name = django_filters.CharFilter(
        field_name="courtroom__name", lookup_expr="icontains"
    )

    class Meta:
        model = Hearing
        fields = {
            "status": ["exact"],
            "hearing_type": ["exact", "icontains"],
            "is_public": ["exact"],
            "case": ["exact"],
            "courtroom": ["exact"],
        }
