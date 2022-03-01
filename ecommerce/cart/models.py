from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.utils.text import slugify
from django.urls import reverse
 
User = get_user_model()

class Address(models.Model):
    ADDRESS_CHOICES=(
        ('B','Billing'),
        ('S','Shipping'),
    )
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    direccion_1=models.CharField(max_length=150)
    direccion_2=models.CharField(max_length=150)
    ciudad=models.CharField(max_length=100)
    codigo_postal=models.CharField(max_length=100)
    tipo_de_direccion=models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.direccion_1},{self.direccion_2},{self.ciudad},{self.codigo_postal} "

    class Meta:
        verbose_name_plural='Addresses'

class ColorVariation(models.Model):
    name=models.CharField(max_length=50)

    def __str__(self):
        return self.name

class SizeVariation(models.Model):
    name=models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Product(models.Model):
    title=models.CharField(max_length=150)
    slug=models.SlugField(unique=True)
    image=models.ImageField(upload_to='product_images')
    description=models.TextField()
    price=models.IntegerField(default=0)
    created=models.DateTimeField(auto_now_add=True)
    update=models.DateTimeField(auto_now=True)
    active=models.BooleanField(default=False)
    available_colors=models.ManyToManyField(ColorVariation)
    available_sizes=models.ManyToManyField(SizeVariation)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("cart:product-detail", kwargs={'slug': self.slug})

    def get_price(self):
        return "{:.2f}".format(self.price/100)

class OrderItem(models.Model):
    order=models.ForeignKey("Order", related_name='items', on_delete=models.CASCADE)
    product=models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)
    color = models.ForeignKey(ColorVariation, on_delete=models.CASCADE)
    size = models.ForeignKey(SizeVariation, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

    def get_raw_total_item_price(self):
        return self.quantity * self.product.price

    def get_total_item_price(self):
        price = self.get_raw_total_item_price()
        return "{:.2f}".format(price/100)

class Order(models.Model):
    user=models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    start_date_created=models.DateTimeField(auto_now_add=True)
    ordered_date=models.DateTimeField(blank=True, null=True)
    ordered=models.BooleanField(default=False)

    direccion_de_entrega=models.ForeignKey(
        Address, related_name='direccion_de_entrega', blank=True, null=True, on_delete=models.SET_NULL)
    diraccion_de_pago=models.ForeignKey(
        Address, related_name='direccion_de_pago', blank=True, null=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f"ORDER--{self.pk}"

    def get_raw_subtotal(self):
        total=0
        for order_item in self.items.all():
            total+=order_item.get_raw_total_item_price()
        return total
    
    def get_subtotal(self):
        subtotal=self.get_raw_subtotal()
        return "{:.2f}".format(subtotal/100)

    def get_raw_total(self):
        subtotal=self.get_raw_subtotal()
        total=subtotal+ subtotal*0.21
        return total

    def get_total(self):
        total=self.get_raw_total()
        return "{:.2f}".format(total/100)

    def get_raw_total_usd(self):
        total = self.get_raw_total() * 0.0093
        return "{:.2f}".format(total/100)


class Payment(models.Model):
    order=models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method=models.CharField(max_length=20, choices=(
        ('Paypal', 'Paypal'),
    ))
    timestamp=models.DateTimeField(auto_now_add=True)
    succesful=models.BooleanField(default=False)
    amount=models.FloatField()
    raw_Response=models.TextField()

    def __str__(self):
        return self.order
    
    @property
    def reference_number(self):
        return f"Payment-{self.order}-{self.pk}"

def pre_save_product_receiver(sender, instance, *args, **kwargs):
    if not instance.slug:
        instance.slug=slugify(instance.title)

pre_save.connect(pre_save_product_receiver, sender=Product)