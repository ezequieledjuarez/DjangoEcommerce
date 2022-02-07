from django.shortcuts import render
from django.views import generic
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .utils import get_or_set_order_session
from .models import Product,OrderItem,Order
from .forms import AddToCartForm

class ProductListView(generic.ListView):
    template_name='cart/product_list.html'
    queryset= Product.objects.all()

class ProductDetailView(generic.FormView):
    template_name = 'cart/product_detail.html'
    form_class = AddToCartForm
    
    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self):
        return reverse("home")


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
            item.quantity = int(form.cleaned_data['quantity'])
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