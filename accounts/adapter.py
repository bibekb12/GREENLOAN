from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """
        This method is called when a new social user is created.
        """
        user = super().populate_user(request, sociallogin, data)

        # Google provides 'given_name' and 'family_name'
        if sociallogin.account.provider == 'google':
            user.first_name = data.get('given_name', '')
            user.last_name = data.get('family_name', '')
            user.full_name = f"{user.first_name} {user.last_name}"
        return user
