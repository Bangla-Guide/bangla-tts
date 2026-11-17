from app import app

# Cloudflare Python Workers এই নামটি চায়
default = app

if __name__ == "__main__":
    app.run()
