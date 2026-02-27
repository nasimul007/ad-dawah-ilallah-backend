from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Varsity, PrintingPoint, Printer
from .serializers import VarsitySerializer, PrintingPointSerializer, PrinterSerializer

class VarsityViewSet(viewsets.ModelViewSet):
    queryset = Varsity.objects.all()
    serializer_class = VarsitySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class PrintingPointViewSet(viewsets.ModelViewSet):
    queryset = PrintingPoint.objects.all()
    serializer_class = PrintingPointSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class PrinterViewSet(viewsets.ModelViewSet):
    queryset = Printer.objects.all()
    serializer_class = PrinterSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

