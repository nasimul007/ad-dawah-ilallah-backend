from rest_framework import serializers
from .models import Varsity, PrintingPoint, Printer

class PrinterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Printer
        fields = '__all__'

class PrintingPointSerializer(serializers.ModelSerializer):
    printer = PrinterSerializer(read_only=True)

    class Meta:
        model = PrintingPoint
        fields = '__all__'

class VarsitySerializer(serializers.ModelSerializer):
    printing_points = PrintingPointSerializer(many=True, read_only=True)

    class Meta:
        model = Varsity
        fields = '__all__'
