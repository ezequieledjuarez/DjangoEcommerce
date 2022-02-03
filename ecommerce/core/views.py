from django.core.mail import send_mail
from django.shortcuts import render

from django.views import generic
from django.contrib import messages
from django.urls import reverse
from .forms import ContactForm

from django.conf import settings

class HomeView(generic.TemplateView):
    template_name = 'index.html'

class ContactView(generic.FormView):
    form_class= ContactForm
    template_name='contact.html'

    def get_success_url(self) -> str:
        return reverse("contact")

    def form_valid(self,form):
        messages.info(
            self.request,"Recibimos tu mensaje")
        
        name = form.cleaned_data.get('name')
        email = form.cleaned_data.get('email')
        message = form.cleaned_data.get('message')

        full_message = f"""
            Mensaje recibido de {name}, {email}
            ____________________________________

            {message}
        """
        send_mail(
            subject="Mensaje recibido",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.NOTIFY_EMAIL]
        )
           
        
            
        return super(ContactView, self).form_valid(form)
