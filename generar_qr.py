vscode_lsp_terminal_prompt_tracker= {}
import qrcode
import os
import traceback

try:
    # Dirección de Transiweb
    url = "http://192.168.17.89:5000"

    print("Generando código QR...")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4
    )

    qr.add_data(url)
    qr.make(fit=True)

    imagen = qr.make_image(
        fill_color="#0F1B33",
        back_color="white"
    )

    carpeta = os.path.dirname(os.path.abspath(__file__))
    ruta = os.path.join(carpeta, "qr_transiweb.png")

    imagen.save(ruta)

    print("Código QR generado correctamente.")
    print("Ubicación:", ruta)
    print("Dirección:", url)

except Exception:
    traceback.print_exc()
