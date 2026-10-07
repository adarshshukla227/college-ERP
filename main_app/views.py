import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from .EmailBackend import EmailBackend
from .models import Attendance, Session, Subject 

# Create your views here.


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    role = request.GET.get('role', '').lower()
    return render(request, 'main_app/login.html', {'role': role})


def admin_login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html', {'role': 'admin'})


def student_login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html', {'role': 'student'})


def staff_login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("staff_home"))
        else:
            return redirect(reverse("student_home"))
    return render(request, 'main_app/login.html', {'role': 'staff'})


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        portal = request.POST.get('portal', '').lower()
        user_type_expected = str(request.POST.get('user_type', '')).strip()

        # Determine redirect target on error
        if portal == 'admin' or user_type_expected == '1':
            error_redirect = reverse('admin_login')
        elif portal == 'student' or user_type_expected == '3':
            error_redirect = reverse('student_login')
        elif portal == 'staff' or user_type_expected == '2':
            error_redirect = reverse('staff_login')
        else:
            error_redirect = reverse('login_page')

        # Google recaptcha (only enforced in production when DEBUG is False)
        captcha_token = request.POST.get('g-recaptcha-response')
        if captcha_token and not settings.DEBUG:
            captcha_url = "https://www.google.com/recaptcha/api/siteverify"
            captcha_key = "6LfTGD4qAAAAALtlli02bIM2MGi_V0cUYrmzGEGd"
            data = {
                'secret': captcha_key,
                'response': captcha_token
            }
            try:
                captcha_server = requests.post(url=captcha_url, data=data, timeout=5)
                response = json.loads(captcha_server.text)
                if response.get('success') is False:
                    messages.error(request, 'Invalid Captcha. Try Again')
                    return redirect(error_redirect)
            except Exception:
                pass
        
        # Authenticate
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = EmailBackend.authenticate(request, username=email, password=password)
        if user is not None:
            # Check that user role matches the chosen portal
            if user_type_expected == '1':
                if str(user.user_type) != '1' and not (user.is_superuser or user.is_staff):
                    messages.error(request, "Access Denied: This account is registered as a Student. Please login using the Student Portal.")
                    return redirect(error_redirect)
            elif user_type_expected == '3':
                if str(user.user_type) != '3':
                    messages.error(request, "Access Denied: This account is registered as an Admin. Please login using the Admin Portal.")
                    return redirect(error_redirect)
            elif user_type_expected == '2':
                if str(user.user_type) != '2' and not user.is_superuser:
                    messages.error(request, "Access Denied: This account is not a Faculty / Staff member.")
                    return redirect(error_redirect)

            login(request, user)
            
            # Handle "Remember Me" functionality
            remember_me = request.POST.get('remember')
            if remember_me:
                # Set session to expire in 30 days
                request.session.set_expiry(30 * 24 * 60 * 60)
            else:
                # Set session to expire when browser closes
                request.session.set_expiry(0)
            
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("staff_home"))
            else:
                return redirect(reverse("student_home"))
        else:
            messages.error(request, "Invalid email or password. Please try again.")
            return redirect(error_redirect)



def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                    "id": attd.id,
                    "attendance_date": str(attd.date),
                    "session": attd.session.id
                    }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')

