from rest_framework import serializers
from .models import PrintOrder, Print
from django.db import transaction

class PrintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Print
        fields = [
            'id', 'name', 'file_url', 'copies', 'sides', 'print_color', 
            'print_pages', 'page_range', 'pages_per_slide', 'total_pages',
            'remaining_printing_options', 'cost'
        ]

class PrintOrderSerializer(serializers.ModelSerializer):
    prints = PrintSerializer(many=True, read_only=True)
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = PrintOrder
        fields = ['id', 'user', 'anon_id', 'printer', 'name', 'status', 'created_at', 'prints', 'total_cost']
        read_only_fields = ['user', 'created_at', 'status', 'anon_id']
