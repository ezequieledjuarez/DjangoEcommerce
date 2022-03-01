import datetime
import json
import sys
import unicodedata 

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from src.app.settings import PAYPAL_CLIENT_ID, PAYPAL_SECRET_KEY

from .forms import AddressForm, AddToCartForm
from .models import Address, Order, OrderItem, Payment, Product
from .utils import get_or_set_order_session

from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersGetRequest, OrdersCaptureRequest
import environ

env = environ.Env()

environ.Env().read_env()

cart_summary = "cart:summary"


class ProductListView(generic.ListView):
    template_name='cart/product_list.html'
    queryset= Product.objects.all()

class ProductDetailView(generic.FormView):
    template_name = 'cart/product_detail.html'
    form_class = AddToCartForm
    
    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self):
        return reverse(cart_summary)


    def get_form_kwargs(self):
        kwargs=super(ProductDetailView, self).get_form_kwargs()
        kwargs["product_id"]=self.get_object().id
        return kwargs

    
    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        product = self.get_object()

        item_filter = order.items.filter(
            product=product,
            color=form.cleaned_data['color'],
            size=form.cleaned_data['size'])
       
        if item_filter.exists():
            item = item_filter.first()
            item.quantity += int(form.cleaned_data['quantity'])
            item.save()

        else:
            new_item = form.save(commit=False)
            new_item.product = product
            new_item.order = order
            new_item.save()
        
        return super(ProductDetailView, self).form_valid(form)


    
    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['product'] = self.get_object()
        return context


class CartView(generic.TemplateView):
    template_name = 'cart/cart.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CartView, self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context

class IncreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item=get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.quantity += 1
        order_item.save()
        return redirect("cart_summary")

class DecreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item=get_object_or_404(OrderItem, id=kwargs['pk'])

        if order_item.quantity <=1:
            order_item.delete()
            return redirect("cart_summary")
        else:
            order_item.quantity -= 1
            order_item.save()
            return redirect("cart_summary")

class RemoveFromCartView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item=get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.delete()
        return redirect("cart_summary")

class CheckoutView(generic.FormView):
    template_name='cart/checkout.html'
    form_class=AddressForm

    def get_success_url(self):
        return reverse("cart:payment") 

    def form_valid(self, form):
        order=get_or_set_order_session(self.request)
        direccion_de_entrega_seleccionada=form.cleaned_data.get('direccion_de_entrega_seleccionada')
        direccion_de_pago_seleccionada=form.cleaned_data.get('direccion_de_pago_seleccionada')

        if direccion_de_entrega_seleccionada:
            order.direccion_de_entrega=direccion_de_entrega_seleccionada
        else:
            address=Address.objects.create(
                tipo_de_direccion='S',
                user=self.request.user,
                direccion_1=form.cleaned_data['direccion_de_entrega_1'],
                direccion_2=form.cleaned_data['direccion_de_entrega_2'],
                codigo_postal=form.cleaned_data['codigo_postal'],
                ciudad=form.cleaned_data['ciudad'],
            )

            order.direccion_de_pago=address

        if direccion_de_pago_seleccionada:
            order.direccion_de_pago=direccion_de_pago_seleccionada
        else:
            address=Address.objects.create(
                tipo_de_direccion='B',
                user=self.request.user,
                direccion_1=form.cleaned_data['direccion_de_pago_1'],
                direccion_2=form.cleaned_data['direccion_de_pago_2'],
                codigo_postal=form.cleaned_data['codigo_postal'],
                ciudad=form.cleaned_data['ciudad'],
            )

            order.direccion_de_pago=address
        order.save()
        messages.info(self.request, "Tus direcciones fueron agregadas correctamente")
        return super(CheckoutView, self).form_valid(form)
        
    def get_context_data(self, *args, **kwargs):
        context = super(CheckoutView, self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context

    def get_form_kwargs(self):
        kwargs=super(CheckoutView, self).get_form_kwargs()
        kwargs["user_id"]=self.request.user.id
        return kwargs

class PaymentView(generic.TemplateView):
    template_name = 'cart/payment.html'

    def get_context_data(self, **kwargs):
        context = super(PaymentView, self).get_context_data(**kwargs)
        context["PAYPAL_CLIENT_ID"] = settings.PAYPAL_CLIENT_ID
        context['order'] = get_or_set_order_session(self.request)
        context['CALLBACK_URL']= self.request.build_absolute_uri(reverse("cart:thank-you"))
        return context

class ConfirmOrderView(generic.View):    
    def post(self, request, *args, **kwargs):
        order=get_or_set_order_session(request) 
        body= json.loads(request.body)
        order_id= body ['orderID']
        detail  = GetOrder().get_order(order_id)
        trx = CaptureOrder().capture_order(order_id, debug=False)
        payment = Payment.objects.create(
            order=order,
            succesful=True,
            raw_Response= str(order_id),
            amount=float(detail.result["purchase_units"][0]["amount"]["value"]),
            payment_method='PayPal'
        ),
        order.ordered=True
        order.ordered_date=datetime.date.today()
        order.save()

        data = {
            "id" : f"{trx.result.id}",
            "status": f"{trx.result.status}"
        }

        return JsonResponse(data)

class ThankYouView(generic.TemplateView):
    template_name='cart/thanks.html'

class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = 'order.html'
    queryset = Order.objects.all()
    context_object_name='order'

class PayPalClient:
    def __init__(self):
        self.client_id= PAYPAL_CLIENT_ID
        self.client_secret= PAYPAL_SECRET_KEY

        self.enviroment = SandboxEnvironment(client_id=self.client_id, client_secret=self.client_secret)
        self.client=PayPalHttpClient(self.enviroment)

    def object_to_json(self, json_data):
        result = {}
        if sys.version_info[0]<3:
            itr=json_data.__dict__.iteritems()
        else:
            itr=json_data.__dict__.items()
        for key,value in itr:
            if key.startswith("__"):
                continue
        result[key]=self.array_to_json_array(value) if isinstance(value,list)else\
               self.object_to_json(value) if not self.is_primittive(value) else value
        return result

    def array_to_json_array(self, json_array):
        result = []
        if isinstance(json_array, list):
            for item in json_array:
                result.append(self.object_to_json(item)if not self.is_primittive(item)\
                    else self.array_to_json_array(item) if isinstance(item, list) else item)
    
    def is_primittive(self,data):
        return isinstance(data, str) or isinstance(data,unicodedata) or isinstance(data,int)
        
class GetOrder(PayPalClient):
    def get_order(self, order_id):
        request=OrdersGetRequest(order_id)
        response=self.client.execute(request)
        return response

class CaptureOrder(PayPalClient):
    def capture_order(self, order_id, debug=True):
        request = OrdersCaptureRequest(order_id)
        response= self.client.execute(request)
        return response