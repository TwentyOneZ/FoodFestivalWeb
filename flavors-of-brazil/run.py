import os
import sys

from app import create_app, seed_database

app = create_app()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "init-db":
        seed_database(app)
        print("Banco inicializado com usuario admin e dados de exemplo.")
        print("Admin: admin@flavorsofbrazil.com / ChangeMe123!")
        return

    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_RUN_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
    )


if __name__ == "__main__":
    main()
