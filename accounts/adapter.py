from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        """
        This method is called when a new social user is created.
        """
        user = super().populate_user(request, sociallogin, data)

        # Google provides 'given_name' and 'family_name'
        if sociallogin.account.provider == 'google':
            first = data.get('given_name') or ''
            last = data.get('family_name') or ''
            user.first_name = first
            user.last_name = last

            full_name = f"{first} {last}".strip()
            if not full_name:
                full_name = user.email.split('@')[0]
            user.full_name = full_name
            user.nationality = data.get('locale')
        return user
