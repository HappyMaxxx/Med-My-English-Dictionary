from django.core.exceptions import ValidationError
from django.utils.translation import ngettext

class NecessaryValuesValidator:
    SPECIAL = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', ',', '.', '?', '":', '{', '}', '|', '<', '>', '_']
    NECESSARY = ['upper', 'lower', 'digit', 'special']

    def validate(self, password, user=None):
        necessary = self.NECESSARY.copy()

        if any(char.isupper() for char in password):
            necessary.remove('upper')

        if any(char.islower() for char in password):
            necessary.remove('lower')

        if any(char.isdigit() for char in password):
            necessary.remove('digit')
        
        if any(char in self.SPECIAL for char in password):
            necessary.remove('special')

        if len(necessary) != 0:
            raise ValidationError(
                ngettext(
                    "This password must contain at least one %(necessary)s character.",
                    "This password must contain at least one %(necessary)s characters.",
                    len(necessary),
                ),
                code="password_no_necessary",
                params={"necessary": ', '.join(necessary)},
            )

    def get_help_text(self):
        return ngettext(
            "Your password must contain at least one %(necessaty)s character.",
            "Your password must contain at least one %(necessaty)s characters.",
            len(self.NECESSATY),
        ) % {'necessaty': ', '.join(self.NECESSATY)}