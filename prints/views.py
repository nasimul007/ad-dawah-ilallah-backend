import json
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import PrintOrder, Print
from .serializers import PrintOrderSerializer, PrintSerializer
from .utils import upload_file_to_r2, get_pdf_page_count
from utils.page_range_validator import validate_page_range
from utils.print_cost_calculator import get_print_cost_from_data

from rest_framework.permissions import AllowAny, IsAuthenticated

class PrintOrderViewSet(viewsets.ModelViewSet):
    queryset = PrintOrder.objects.all()
    serializer_class = PrintOrderSerializer

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # For operators, we might want different behavior, but for regular users:
            return self.queryset.filter(user=user).order_by('-created_at')
        
        anon_id = self.request.headers.get('X-ANON-ID')
        if anon_id:
            return self.queryset.filter(anon_id=anon_id).order_by('-created_at')
        
        return self.queryset.none()


    def create(self, request, *args, **kwargs):
        # 1. Extract data from request
        name = request.data.get('name')
        printer_id = request.data.get('printer')
        prints_json = request.data.get('prints')
        files = request.FILES.getlist('files')

        if not prints_json:
            return Response({"detail": "No print data provided."}, status=status.HTTP_400_BAD_REQUEST)

        # prints can arrive as a JSON string (from FormData) or already as a list
        if isinstance(prints_json, str):
            try:
                prints_data = json.loads(prints_json)
            except json.JSONDecodeError as e:
                return Response(
                    {"detail": f"Invalid JSON in prints field: {str(e)}", "received": prints_json[:200]},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif isinstance(prints_json, list):
            prints_data = prints_json
        else:
            return Response(
                {"detail": f"prints must be a JSON string or list, got: {type(prints_json).__name__}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(prints_data, list):
            return Response(
                {"detail": f"prints JSON must decode to a list, got: {type(prints_data).__name__}", "received": str(prints_json)[:200]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Basic Validation
        if len(prints_data) != len(files):
            return Response(
                {"detail": f"Mismatch between print items ({len(prints_data)}) and files ({len(files)})."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Create PrintOrder and Prints with R2 Upload
        from django.db import transaction
        try:
            with transaction.atomic():
                user = request.user if request.user.is_authenticated else None
                anon_id = request.headers.get('X-ANON-ID')
                
                print_order = PrintOrder.objects.create(
                    user=user,
                    anon_id=anon_id if not user else None,
                    name=name,
                    printer_id=printer_id
                )
                for i, p_data in enumerate(prints_data):
                    file_obj = files[i]
                    
                    # Count pages
                    total_pages = get_pdf_page_count(file_obj)
                    
                    # Validate page range if custom
                    print_pages = p_data.get('print_pages', 'ALL')
                    page_range = p_data.get('page_range')
                    
                    if print_pages == 'CUSTOM':
                        if not page_range or not validate_page_range(page_range, total_pages):
                            raise Exception(f"Invalid page range '{page_range}' for file {file_obj.name} (Total pages: {total_pages})")

                    # Upload to R2
                    try:
                        file_url = upload_file_to_r2(
                            file_obj, 
                            file_obj.name, 
                            content_type=file_obj.content_type
                        )
                    except Exception as upload_err:
                        raise Exception(f"Failed to upload file {file_obj.name} to R2: {str(upload_err)}")

                    # Calculate cost using default coverage of 9%
                    cost = get_print_cost_from_data(
                        p_data, 
                        total_pages, 
                        coverage_pct=9.0
                    )

                    Print.objects.create(
                        print_order=print_order,
                        name=p_data.get('name', f"File {i+1}"),
                        file_url=file_url,
                        copies=p_data.get('copies', 1),
                        sides=p_data.get('sides', 'SINGLE_SIDED'),
                        print_color=p_data.get('print_color', 'B_W'),
                        print_pages=print_pages,
                        page_range=page_range,
                        pages_per_slide=p_data.get('pages_per_slide', 1),
                        total_pages=total_pages,
                        remaining_printing_options=p_data.get('remaining_printing_options'),
                        cost=cost
                    )
        except Exception as e:
            return Response({"detail": f"Error creating order: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Initiate payment session
        from payments.utils import create_payment_session
        try:
            # total_cost + 1 tk for payment
            payment_amount = float(print_order.total_cost) + 1.0
            payment = create_payment_session(
                request=request,
                print_order=print_order,
                amount=payment_amount,
                kind="ONE_TIME"
            )
            return Response({
                "order_id": print_order.id,
                "payment_id": payment.id,
                "tran_id": payment.tran_id,
                "gateway_page_url": payment.gateway_page_url,
            }, status=status.HTTP_201_CREATED)
        except Exception as exc:
            return Response({
                "order_id": print_order.id,
                "detail": "Order created, but failed to initiate payment.",
                "error": str(exc)
            }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """
        Endpoint for printer operators to see paid orders for their printers.
        """
        if not request.user.has_permission_code("PRINT_ORDER_VIEW_PRINTER"):
            return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        
        # Get printers connected to this user
        from varsity.models import Printer
        connected_printers = Printer.objects.filter(connected_user=request.user)
        
        if not connected_printers.exists():
            return Response({"detail": "No printers connected to this user."}, status=status.HTTP_404_NOT_FOUND)
        
        # Filter SUCCESSful orders for these printers
        # We join with PaymentTransaction using the reverse relation 'payments'
        orders = PrintOrder.objects.filter(
            printer__in=connected_printers,
            payments__status="SUCCESS",
            status="RECEIVED"
        ).distinct().order_by('-created_at')
        
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_update_status(self, request):
        """
        Endpoint for print client to update multiple print order status in a single request.
        """
        order_ids = request.data.get('order_ids', [])
        new_status = request.data.get('status')

        if not order_ids or not isinstance(order_ids, list):
            return Response({"detail": "order_ids must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_status not in PrintOrder.Status.values:
            return Response({"detail": f"Invalid status. Choose from {PrintOrder.Status.values}"}, status=status.HTTP_400_BAD_REQUEST)

        updated_count = PrintOrder.objects.filter(id__in=order_ids).update(status=new_status)
        
        return Response({
            "detail": f"Successfully updated {updated_count} orders to {new_status}.",
            "updated_count": updated_count
        })

    def perform_create(self, serializer):
        # This is not strictly needed since we override create, but good practice
        anon_id = self.request.headers.get('X-ANON-ID')
        serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None,
            anon_id=anon_id if not self.request.user.is_authenticated else None
        )

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # If it's a printer operator or admin, they might need more access, 
            # but for regular user flow, we filter by their user.
            # Printer operators have their own 'my_orders' action.
            return self.queryset.filter(user=user).order_by('-created_at')
        
        anon_id = self.request.headers.get('X-ANON-ID')
        if anon_id:
            return self.queryset.filter(anon_id=anon_id).order_by('-created_at')
        
        return self.queryset.none()

class PrintViewSet(viewsets.ModelViewSet):
    queryset = Print.objects.all()
    serializer_class = PrintSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return self.queryset.filter(print_order__user=user)
        
        anon_id = self.request.headers.get('X-ANON-ID')
        if anon_id:
            return self.queryset.filter(print_order__anon_id=anon_id)
        
        return self.queryset.none()

