class TestForms(TestCase):
    def test_user_form(self):
        form_data = {'username': 'testuser', 'password': 'testpass'}
        form = UserForm(data=form_data)
        self.assertTrue(form.is_valid())