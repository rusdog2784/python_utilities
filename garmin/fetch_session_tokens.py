import garth
from getpass import getpass

email = input("Enter email address: ")
password = getpass("Enter password: ")

# If there’s MFA (multi-factor authentication), you’ll be prompted during the login process
garth.login(email, password)
garth.save("./.garth")
print(f"Session tokens saved to ./.garth")

