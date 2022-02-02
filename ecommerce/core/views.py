from django.shortcuts import render
from django.views import generic
from .forms import ContactForm
from django.urls import reverse

class HomeView(generic.TemplateView):
    template_name = 'index.html'

class ContactView(generic.FormView):
    form_class= ContactForm
    template_name='contact.html'

    def get_success_url(self) -> str:
        return reverse("contact")
