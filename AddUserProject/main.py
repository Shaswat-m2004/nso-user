import threading
import io
import pandas as pd
import webview
from app import create_app


class DesktopAPI:
    def download_template(self):
        # 1. Generate Excel File in memory
        columns = ["WarehouseID", "UserRole", "UserName", "UserID"]
        df = pd.DataFrame(columns=columns)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Template")
        excel_bytes = buffer.getvalue()

        # 2. Open Native OS Save File Dialog
        active_window = webview.windows[0]
        file_path = active_window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename="user_upload_template.xlsx",
            file_types=("Excel Files (*.xlsx)", "All files (*.*)"),
        )

        # 3. Write file to disk if user selected a path
        if file_path:
            path = file_path[0] if isinstance(file_path, (list, tuple)) else file_path
            with open(path, "wb") as f:
                f.write(excel_bytes)
            return {"status": "success", "message": "File saved successfully!"}

        return {"status": "cancelled"}


def run_flask(app):
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )


if __name__ == "__main__":
    app = create_app()

    flask_thread = threading.Thread(
        target=run_flask,
        args=(app,),
        daemon=True,
    )
    flask_thread.start()

    # 1. Instantiate the Desktop API
    api = DesktopAPI()

    # 2. Bind the API via js_api
    webview.create_window(
        "NSO User Manager",
        "http://127.0.0.1:5000",
        width=1200,
        height=800,
        resizable=True,
        js_api=api,
    )

    webview.start()