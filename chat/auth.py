#all of the auth related function
from django.shortcuts import render, redirect
from .models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_backends
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
import requests
from django.conf import settings
from django.contrib.auth.hashers import make_password
from imhotep_chat.settings import SITE_DOMAIN
from .auth_forms import RegistrationForm, LoginForm, AddUsernameForm

#the register route
def register(request):

    if request.user.is_authenticated:
        return redirect("main_menu")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user_type = form.cleaned_data.get('user_type')
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')

            # Create a new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                email_verify=False,
                first_name=first_name,
                last_name=last_name
            )

            # Send verification email
            mail_subject = 'Activate your account.'
            current_site = SITE_DOMAIN.rstrip('/')
            message = render_to_string('activate_mail_send.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            send_mail(mail_subject, message, 'imhoteptech1@gmail.com', [email], html_message=message)

            messages.success(request, "Account created successfully! Please check your email to verify your account.")
            return redirect("login")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
            return render(request, "register.html", {'form': form})

    else: # GET request
        form = RegistrationForm()
    return render(request, "register.html", {'form': form})

#the activate route
def activate(request, uidb64, token):
    try:
        # Decode the user ID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Check if the token is valid
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.email_verify = True
        user.save()

        # Set the backend attribute on the user
        backend = get_backends()[0]
        user.backend = f'{backend.__module__}.{backend.__class__.__name__}'

        # Log the user in
        login(request, user)
        messages.success(request, "Thank you for your email confirmation. You can now log in to your account.")
        return redirect('login')
    else:
        messages.success(request, "Activation link is invalid!")
        return redirect('login')

#the login route
def user_login(request):

    if request.user.is_authenticated:
        return redirect("main_menu")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user_username_mail = form.cleaned_data.get('user_username_mail')
            password = form.cleaned_data.get('password')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
            return render(request, "register.html", {'form': form})

        # Check if the input is a username or email
        if '@' not in user_username_mail:
            # Authenticate using username
            user = authenticate(request, username=user_username_mail, password=password)
            if user is not None:
                if user.email_verify == True:
                    login(request, user)
                    messages.success(request, "Login successful!")

                    return redirect("main_menu")

                else:
                    # Send verification email
                    mail_subject = 'Activate your account.'
                    current_site = SITE_DOMAIN.rstrip('/')  # Remove trailing slash if present
                    message = render_to_string('activate_mail_send.html', {
                        'user': user,
                        'domain': current_site,
                        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                        'token': default_token_generator.make_token(user),
                    })
                    send_mail(mail_subject, message, 'imhoteptech1@gmail.com', [user.email], html_message=message)

                    messages.error(request, "E-mail not verified!")
                    messages.info(request, "Please check your email to verify your account.")
                    return redirect("login")
            else:
                messages.error(request, "Invalid username or password!")
        else:
            # Authenticate using email
            user = User.objects.filter(email=user_username_mail).first()
            if user:
                username = user.username
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    if user.email_verify == True:
                        login(request, user)
                        messages.success(request, "Login successful!")
                        return redirect("main_menu")

                    else:
                        # Send verification email
                        mail_subject = 'Activate your account.'
                        current_site = SITE_DOMAIN.rstrip('/')  # Remove trailing slash if present
                        message = render_to_string('activate_mail_send.html', {
                            'user': user,
                            'domain': current_site,
                            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                            'token': default_token_generator.make_token(user),
                        })
                        send_mail(mail_subject, message, 'imhoteptech1@gmail.com', [user.email], html_message=message)

                        messages.error(request, "E-mail not verified!")
                        messages.info(request, "Please check your email to verify your account.")
                        return redirect("login")
                else:
                    messages.error(request, "Invalid E-mail or password!")
            else:
                messages.error(request, "Invalid E-mail or password!")

    return render(request, "login.html")

#the logout route
@login_required
def user_logout(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")

class CustomPasswordResetView(PasswordResetView):
    template_name = 'password_reset.html'
    form_class = PasswordResetForm
    email_template_name = 'password_reset_email.html'
    html_email_template_name = 'password_reset_email.html'
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)

    def get_extra_email_context(self):
        context = {}
        context['domain'] = SITE_DOMAIN.replace('http://', '').replace('https://', '')
        context['site_name'] = 'Imhotep Smart Clinic'  # Changed from Imhotep Tasks
        context['protocol'] = 'https' if 'https://' in SITE_DOMAIN else 'http'
        return context

    def form_valid(self, form):
        """
        Override form_valid to handle email sending ourselves rather than 
        letting Django's built-in functionality handle it.
        """
        # Get user email
        email = form.cleaned_data["email"]
        # Get associated users
        active_users = form.get_users(email)
        
        for user in active_users:
            # Generate token and context
            context = {
                'email': email,
                'domain': SITE_DOMAIN.replace('http://', '').replace('https://', ''),
                'site_name': 'Imhotep Smart Clinic',  # Changed from Imhotep Tasks
                'protocol': 'https' if 'https://' in SITE_DOMAIN else 'http',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': self.token_generator.make_token(user),
            }
            
            # Render email
            subject = "Reset your Imhotep Smart Clinic password"  # Changed from Imhotep Tasks
            email_message = render_to_string(self.email_template_name, context)
            html_email = render_to_string(self.html_email_template_name, context)
            
            # Send email
            send_mail(
                subject,
                email_message,
                self.from_email or 'imhoteptech1@gmail.com',
                [user.email],
                html_message=html_email,
            )
            
        # Return success response
        return super().form_valid(form)
    
class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_reset_confirm.html'
    form_class = SetPasswordForm

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return super().form_invalid(form)

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'password_reset_complete.html'


GOOGLE_CLIENT_ID = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['client_id']
GOOGLE_CLIENT_SECRET = settings.SOCIALACCOUNT_PROVIDERS['google']['APP']['secret']
GOOGLE_REDIRECT_URI = settings.SOCIALACCOUNT_PROVIDERS['google']['REDIRECT_URI']

def google_login(request):
    """Initiates the Google OAuth2 login flow"""
    oauth2_url = (
        'https://accounts.google.com/o/oauth2/v2/auth?'
        f'client_id={GOOGLE_CLIENT_ID}&'
        f'redirect_uri={SITE_DOMAIN}/google/callback/&'
        'response_type=code&'
        'scope=openid email profile'
    )
    return redirect(oauth2_url)

def google_callback(request):
    """Handles the callback from Google OAuth2"""
    code = request.GET.get('code')
    
    if not code:
        messages.error(request, "Google login was canceled. Please try again.")
        return redirect('login')

    # Exchange code for access token
    token_url = 'https://oauth2.googleapis.com/token'
    token_payload = {
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'code': code,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }

    try:
        token_response = requests.post(token_url, data=token_payload)
        token_data = token_response.json()

        # Get user info using access token
        userinfo_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
        headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
        userinfo_response = requests.get(userinfo_url, headers=headers)
        user_info = userinfo_response.json()

        email = user_info['email']
        username = email.split('@')[0]
        
        # Get first and last name if available
        first_name = user_info.get('given_name', '')
        last_name = user_info.get('family_name', '')
        
        # Check if user exists
        user = User.objects.filter(email=email).first()
        
        if user:
            # Set the backend attribute on the user
            backend = get_backends()[0]
            user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
            # User exists, log them in
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("main_menu")
        
        # Store info in session for the next steps
        google_user_data = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            # Need to collect a new username
            google_user_data['need_username'] = True
            request.session['google_user_info'] = google_user_data
            return render(request, 'add_username_google.html')
        
        google_user_data['username'] = username
        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=make_password(None),  # Random password since using OAuth
            first_name=first_name,
            last_name=last_name,
            email_verify=True,  # Google accounts are pre-verified
        )
        messages.success(request, "Account created successfully!")
        del request.session['google_user_info']
        return redirect('main_menu')

    except Exception as e:
        messages.error(request, f"An error occurred during Google login. Please try again. {e}")
        return redirect('login')
    
def add_username_google_login(request):
    
    if request.method != "POST":
        return redirect('login')

    user_info = request.session.get('google_user_info', {})
    if not user_info:
        messages.error(request, "Session expired. Please try again.")
        return redirect('login')

    form = AddUsernameForm(request.POST)
    if form.is_valid():
        username = form.cleaned_data.get('username')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
        return render(request, "register.html", {'form': form})

    # Update username in session
    user_info['username'] = username
    request.session['google_user_info'] = user_info
    
    return redirect('main_menu')
