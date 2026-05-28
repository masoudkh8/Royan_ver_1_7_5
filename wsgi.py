# wsgi.py
# TODO: Translate -  این File را در کنار app.py بسازید
# TODO: Translate -  Create اپلیکیشن برای محیط production


from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()