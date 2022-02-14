from django import forms
from django.contrib.auth import get_user_model
from .models import Address, OrderItem, ColorVariation, SizeVariation, Product

User = get_user_model()

class AddToCartForm(forms.ModelForm):
    color = forms.ModelChoiceField(queryset=ColorVariation.objects.none())
    size = forms.ModelChoiceField(queryset=SizeVariation.objects.none())
    
    class Meta:
        model=OrderItem
        fields=['quantity', 'color', 'size']

    def __init__(self, *args, **kwargs):
        self.product_id = kwargs.pop('product_id')
        product = Product.objects.get(id=self.product_id)
        super().__init__(*args, **kwargs)

        self.fields['color'].queryset= product.available_colors.all()
        self.fields['size'].queryset= product.available_sizes.all()

class AddressForm(forms.Form):
    
    direccion_de_entrega_1 = forms.CharField(required=False)
    direccion_de_entrega_2 = forms.CharField(required=False)
    codigo_postal = forms.CharField(required=False)
    ciudad = forms.CharField(required=False)

    direccion_de_pago_1 = forms.CharField(required=False)
    direccion_de_pago_2 = forms.CharField(required=False)
    codigo_postal = forms.CharField(required=False)
    ciudad = forms.CharField(required=False)

    direccion_de_entrega_seleccionada = forms.ModelChoiceField(
        Address.objects.none(), required=False
    )

    direccion_de_pago_seleccionada = forms.ModelChoiceField(
        Address.objects.none(), required=False
    )

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        super().__init__(*args, **kwargs)

        user = User.objects.get(id=user_id)

        direccion_de_entrega_qs = Address.objects.filter(
            user=user,
            tipo_de_direccion='S'
        )

        direccion_de_pago_qs = Address.objects.filter(
            user=user,
            tipo_de_direccion='B'
        )

        self.fields['direccion_de_entrega_seleccionada'].queryset = direccion_de_entrega_qs
        self.fields['direccion_de_pago_seleccionada'].queryset = direccion_de_pago_qs


    def clean(self):
        data = self.cleaned_data

        direccion_de_entrega = data.get('direccion_de_entrega_seleccionada', None)
        if direccion_de_entrega is None:
            if not data.get('direccion_de_entrega_1', None):
                self.add_error("direccion_de_entrega_1", "Please fill in this field")
            if not data.get('direccion_de_entrega_2', None):
                self.add_error("direccion_de_entrega_2", "Please fill in this field")
            if not data.get('codigo_postal', None):
                self.add_error("codigo_postal", "Please fill in this field")
            if not data.get('ciudad', None):
                self.add_error("ciudad", "Please fill in this field")

        direccion_de_pago = data.get('direccion_de_pago_seleccionada', None)
        if direccion_de_pago is None:
            if not data.get('direccion_de_pago_1', None):
                self.add_error("direccion_de_pago_1", "Please fill in this field")
            if not data.get('direccion_de_pago_2', None):
                self.add_error("direccion_de_pago_2", "Please fill in this field")
            if not data.get('codigo_postal', None):
                self.add_error("codigo_postal", "Please fill in this field")
            if not data.get('ciudad', None):
                self.add_error("ciudad", "Please fill in this field")
