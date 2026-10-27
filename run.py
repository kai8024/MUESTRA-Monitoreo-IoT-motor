from app import create_app

app = create_app()

if __name__ == "__main__":
    # host 0.0.0.0 para que el ESP32 (misma red Wi-Fi) pueda alcanzar el servidor
    app.run(host="0.0.0.0", port=5000, debug=True)
