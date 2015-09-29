import django_filters
from iati.transaction.models import Transaction
from api.generics.filters import CommaSeparatedCharFilter

class TransactionFilter(django_filters.FilterSet):
    """
    Transaction filter class
    """

    activity = CommaSeparatedCharFilter(
        lookup_type='in',
        name='activity')

    activity_related_activity_id = CommaSeparatedCharFilter(
        lookup_type='in',
        name='activity__current_activity__related_activity__id',
        distinct=True)

    min_value = django_filters.NumberFilter(name='value', lookup_type='gte')
    max_value = django_filters.NumberFilter(name='value', lookup_type='lte')

    class Meta:
        model = Transaction
        fields = [
            'id',
            'aid_type',
            'transaction_type',
            'value',
            'min_value',
            'max_value',
        ]