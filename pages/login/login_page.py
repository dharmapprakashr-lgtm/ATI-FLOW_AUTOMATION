from config.environment import config


class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username_input = self.page.locator("input[name='username'], input[placeholder='Username'], input[type='text']").first
        self.password_input = self.page.locator("input[name='password'], input[placeholder='Password'], input[type='password']").first
        self.login_button = self.page.locator("button[type='submit'], button:has-text('Login')").first

    def open_login_page(self):
        self.page.goto(config.base_url)

    def enter_username(self, username):
        self.username_input.fill(username)

    def enter_password(self, password):
        self.password_input.fill(password)

    def click_login(self):
        self.login_button.click()

    def login(self, username, password):
        self.open_login_page()
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
