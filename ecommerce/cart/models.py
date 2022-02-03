from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Address(models.Model):
    ADDRESS_CHOICES=(
        ('B','Billing'),
        ('S','Shipping'),
    )
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    address_line_1=models.CharField(max_length=150)
    addres_line_2=models.CharField(max_length=150)
    city=models.CharField(max_length=100)
    zip_code=models.CharField(max_length=100)
    address_type=models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default=models.BooleanField(default=False)

    def __str__(self):
        return f"{self.address_line_1},{self.address_line_2},{self.city},{self.zip_code} "

    class Meta:
        verbose_name_plural='Addresses'

class Product(models.Model):
    title=models.CharField(max_length=150)
    slug=models.SlugField()
    description=models.TextField()
    created=models.DateTimeField(auto_now_add=True)
    update=models.DateTimeField(auto_now=True)
    active=models.BooleanField(default=False)

    def __str__(self):
        return self.title

class OrderItem(models.Model):
    order=models.ForeignKey("Order", related_name='items', on_delete=models.CASCADE)
    products=models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.title}"

class Order(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    start_date_created=models.DateTimeField(auto_now_add=True)
    ordered_date=models.DateTimeField(blank=True, null=True)
    ordered=models.BooleanField(default=False)

    billing_address=models.ForeignKey(
        Address, related_name='billing_address', blank=True, null=True, on_delete=models.SET_NULL)
    shipping_address=models.ForeignKey(
        Address, related_name='shipping_address', blank=True, null=True, on_delete=models.SET_NULL)
    
    def __str__(self):
        return self.reference_number

    @property
    def reference_number(self):
        return f"ORDER--{self.pk}"

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