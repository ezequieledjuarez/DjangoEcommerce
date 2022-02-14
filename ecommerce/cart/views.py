import datetime
import json
from django.shortcuts import redirect, render
from django.views import generic
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from .utils import get_or_set_order_session
from .models import Product,OrderItem,Order, OrderItem, Address, Payment,Order
from .forms import AddToCartForm,AddressForm

class ProductListView(generic.ListView):
    template_name='cart/product_list.html'
    queryset= Product.objects.all()

class ProductDetailView(generic.FormView):
    template_name = 'cart/product_detail.html'
    form_class = AddToCartForm
    
    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self):
        return reverse("cart:summary")


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
        return redirect("cart:summary")

class DecreaseQuantityView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item=get_object_or_404(OrderItem, id=kwargs['pk'])

        if order_item.quantity <=1:
            order_item.delete()
            return redirect("cart:summary")
        else:
            order_item.quantity -= 1
            order_item.save()
            return redirect("cart:summary")

class RemoveFromCartView(generic.View):
    def get(self, request, *args, **kwargs):
        order_item=get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.delete()
        return redirect("cart:summary")

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
        payment = Payment.objects.create(
            order=order,
            succesful=True,
            raw_response=json.dumps(body),
            amount=float(body["purchase_units"][0]["amount"]["value"]),
            payment_method='PayPal'
        ),
        order.ordered=True
        order.ordered_date=datetime.date.today()
        order.save()
        return JsonResponse({"data": "Success"})

class ThankYouView(generic.TemplateView):
    template_name='cart/thanks.html'

class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    template_name = 'order.html'
    queryset = Order.objects.all()
    context_object_name='order'