from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'placeholder': "Nombre"
    }))

    email = forms.EmailField(widget=forms.TextInput(attrs={
        'placeholder': "Email"
    }))

    mensaje = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder': "Mensaje"
    }))