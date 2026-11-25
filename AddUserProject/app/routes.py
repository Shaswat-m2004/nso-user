import io
import logging
import pandas as pd
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template_string,
    request,
    send_file,
    url_for,
)

from app.core import UserManagementApp
from app.templates import PAGE

bp = Blueprint("main", __name__)
manager = UserManagementApp()


def _refresh_active_manager_count():
    """Safely refresh and return the live active manager count when connected."""
    if not manager.connection_config:
        manager.active_manager_count = None
        return None
    try:
        return manager.get_active_manager_count()
    except Exception as err:
        logging.warning("Unable to refresh active manager count: %s", err)
        return manager.active_manager_count


def render_page():
    active_count = _refresh_active_manager_count()
    return render_template_string(
        PAGE,
        connected=manager.connection_config is not None,
        config=manager.connection_config,
        logs=manager.logs[-40:],
        active_manager_columns=manager.active_manager_columns,
        active_managers=manager.active_managers,
        managers_list=manager.managers_list,
        others_list=manager.others_list,
        active_manager_count=active_count,
        max_active_managers=manager.MAX_ACTIVE_MANAGERS,
    )


@bp.get("/")
def index():
    return render_page()


@bp.post("/connect")
def connect():
    config = {
        key: request.form.get(key, "").strip()
        for key in ("ip", "database", "username", "password")
    }
    config["port"] = "1433"
    try:
        manager.connect(config)
        flash("Database connection established successfully.", "success")
        if (
            manager.active_manager_count is not None
            and manager.active_manager_count > manager.MAX_ACTIVE_MANAGERS
        ):
            flash(
                f"Flag: Connected database currently has {manager.active_manager_count} active managers "
                f"(exceeds the maximum limit of {manager.MAX_ACTIVE_MANAGERS}).",
                "warning",
            )
    except Exception as error:
        manager.log(f"CONNECTION FAILED | {error}")
        flash(str(error), "danger")
    return redirect(url_for("main.index", _anchor="connect"))


@bp.route("/download-template", methods=["GET"])
def download_template():
    columns = ["WarehouseID", "UserRole", "UserName", "UserID"]
    df = pd.DataFrame(columns=columns)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Template")

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="user_upload_template.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@bp.post("/add-user")
def add_user():
    values = {
        key: request.form.get(key, "").strip()
        for key in ("warehouse", "role", "name", "userid")
    }
    ip = manager.connection_config["ip"] if manager.connection_config else ""
    valid, message = manager.validate_record(
        ip, values["warehouse"], values["role"], values["name"], values["userid"]
    )
    try:
        if not valid:
            raise ValueError(message)

        # Enforce active manager limit on creation: existing + 1 <= 4
        if values["role"].lower() == "manager":
            current_active = manager.get_active_manager_count()
            if current_active + 1 > manager.MAX_ACTIVE_MANAGERS:
                msg = (
                    f"Creation blocked: Existing active managers ({current_active}) + "
                    f"1 new manager exceeds the maximum limit of {manager.MAX_ACTIVE_MANAGERS}."
                )
                manager.log(f"MANAGER CREATION BLOCKED | {msg}")
                raise ValueError(msg)

        manager.execute_query(
            ip, values["warehouse"], values["role"], values["name"], values["userid"]
        )
        _refresh_active_manager_count()
        manager.log(f"SUCCESS | {values['warehouse']} | {values['userid']}")
        flash("User created successfully.", "success")
    except Exception as error:
        logging.exception(str(error))
        flash(str(error), "danger")
    return redirect(url_for("main.index", _anchor="add"))


@bp.post("/active-managers")
def active_managers():
    try:
        columns, rows = manager.get_active_managers()
        manager.active_manager_columns = columns
        manager.active_managers = rows
        manager.log(f"ACTIVE MANAGERS CHECK | COUNT : {len(rows)}")
        if len(rows) > manager.MAX_ACTIVE_MANAGERS:
            flash(
                f"Flag: {len(rows)} active managers found (exceeds the limit of {manager.MAX_ACTIVE_MANAGERS}).",
                "warning",
            )
        else:
            flash(f"Active managers found: {len(rows)}", "success")
    except Exception as error:
        manager.active_manager_columns = []
        manager.active_managers = []
        logging.exception(str(error))
        manager.log(f"ACTIVE MANAGERS CHECK FAILED : {error}")
        flash(str(error), "danger")
    return redirect(url_for("main.index", _anchor="add"))


@bp.post("/bulk-upload")
def bulk_upload():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        flash("Select a CSV or Excel file first.", "danger")
        return redirect(url_for("main.index", _anchor="bulk"))
    try:
        df = (
            pd.read_csv(uploaded)
            if uploaded.filename.lower().endswith(".csv")
            else pd.read_excel(uploaded)
        )
        required = ["WarehouseID", "UserRole", "UserName", "UserID"]
        missing = next((column for column in required if column not in df.columns), None)
        if missing:
            raise ValueError(f"Missing Column : {missing}")
        if not manager.connection_config:
            raise ValueError("Connect to a database before running an operation")

        # Enforce active manager limit on bulk creation:
        # existing active managers + managers to be created <= 4
        managers_to_create = sum(
            1
            for _, row in df.iterrows()
            if str(row["UserRole"]).strip().lower() == "manager"
        )
        if managers_to_create > 0:
            current_active = manager.get_active_manager_count()
            if current_active + managers_to_create > manager.MAX_ACTIVE_MANAGERS:
                msg = (
                    f"Bulk upload blocked: Existing active managers ({current_active}) + "
                    f"managers to be created ({managers_to_create}) = "
                    f"{current_active + managers_to_create}, which exceeds the maximum limit "
                    f"of {manager.MAX_ACTIVE_MANAGERS}."
                )
                manager.log(f"BULK MANAGER CREATION BLOCKED | {msg}")
                raise ValueError(msg)

        connected_ip = manager.connection_config["ip"]
        success = failed = 0

        for index, row in df.iterrows():
            try:
                values = {
                    "ip": connected_ip,
                    "warehouse": str(row["WarehouseID"]).strip(),
                    "role": str(row["UserRole"]).strip().lower(),
                    "username": str(row["UserName"]).strip(),
                    "userid": str(row["UserID"]).strip(),
                }
                valid, message = manager.validate_record(**values)
                if not valid:
                    raise ValueError(message)
                manager.execute_query(**values)
                success += 1
                manager.log(f"SUCCESS Row {index + 1}")
            except Exception as row_error:
                failed += 1
                manager.log(f"FAILED Row {index + 1} | {row_error}")

        _refresh_active_manager_count()
        manager.log(f"PROCESS COMPLETED | SUCCESS : {success} | FAILED : {failed}")
        flash(
            f"Bulk upload completed. Success={success}, Failed={failed}",
            "success" if failed == 0 else "warning",
        )
    except Exception as error:
        logging.exception(str(error))
        flash(f"Bulk Error: {error}", "danger")
    return redirect(url_for("main.index", _anchor="bulk"))


# ========================================== #
# STATUS MANAGEMENT ROUTES                   #
# ========================================== #

@bp.post("/fetch-users/<group>")
def fetch_users(group):
    try:
        if not manager.connection_config:
            raise ValueError("Connect to a database first.")

        rows = manager.fetch_user_status(group)
        if group == "manager":
            manager.managers_list = rows
            active_count = manager.active_manager_count
            if active_count is not None and active_count > manager.MAX_ACTIVE_MANAGERS:
                flash(
                    f"Fetched {len(rows)} managers. Flag: {active_count} active managers "
                    f"(exceeds the limit of {manager.MAX_ACTIVE_MANAGERS}).",
                    "warning",
                )
            else:
                flash(
                    f"Fetched {len(rows)} managers ({active_count} active).",
                    "success",
                )
        else:
            manager.others_list = rows
            flash(f"Fetched {len(rows)} other users.", "success")

    except Exception as error:
        logging.exception(str(error))
        flash(f"Error fetching users: {error}", "danger")

    return redirect(url_for("main.index", _anchor="status"))


@bp.post("/toggle-status")
def toggle_status():
    userid = (request.form.get("userid") or "").strip()
    current_status = str(request.form.get("current_status"))
    group_type = (request.form.get("group") or "").strip().lower()
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    new_status = "1" if current_status == "2" else "2"

    try:
        # Block manager activation if it would push active manager count > 4
        if new_status == "2" and group_type == "manager":
            current_active = manager.get_active_manager_count()
            if current_active + 1 > manager.MAX_ACTIVE_MANAGERS:
                err_msg = (
                    f"Activation blocked: Active manager count is already {current_active} "
                    f"(maximum allowed is {manager.MAX_ACTIVE_MANAGERS}). "
                    f"Deactivate another manager before activating {userid}."
                )
                manager.log(f"MANAGER ACTIVATION BLOCKED | User: {userid} | Active: {current_active}")
                if is_ajax:
                    return jsonify(
                        success=False,
                        error=err_msg,
                        active_manager_count=current_active,
                        max_active_managers=manager.MAX_ACTIVE_MANAGERS,
                    ), 400
                flash(err_msg, "danger")
                return redirect(url_for("main.index", _anchor="status"))

        # Activate runs ResetPassword.sql directly; deactivate runs DeactivateUser.sql.
        if new_status == "2":
            manager.reset_user_password(userid, group_type)
        else:
            manager.update_user_status(userid, new_status, group_type)

        updated_active_count = _refresh_active_manager_count()
        manager.log(
            f"STATUS UPDATE | User: {userid} ({group_type}) -> "
            f"{'Active' if new_status == '2' else 'Inactive'}"
        )

        # Keep cached list in sync for non-reload views
        target_list = manager.managers_list if group_type == "manager" else manager.others_list
        for row in target_list:
            if str(row.get("userid")) == userid:
                row["UserActive"] = int(new_status)
                break

        if is_ajax:
            return jsonify(
                success=True,
                userid=userid,
                status=new_status,
                active_manager_count=updated_active_count,
                max_active_managers=manager.MAX_ACTIVE_MANAGERS,
            )

        flash(f"User {userid} status successfully updated.", "success")
        manager.managers_list = []
        manager.others_list = []
    except Exception as error:
        logging.exception(str(error))
        if is_ajax:
            return jsonify(success=False, error=str(error)), 500
        flash(f"Error updating status: {error}", "danger")

    return redirect(url_for("main.index", _anchor="status"))


@bp.post("/bulk-status")
def bulk_status():
    text = request.form.get("userids", "")
    action = (request.form.get("action") or "").strip().lower()
    selected_group = (request.form.get("bulk_group") or "").strip().lower()

    if selected_group not in {"manager", "others"}:
        flash("Select a valid target role (Manager or Cashier / CSD) before running bulk update.", "danger")
        return redirect(url_for("main.index", _anchor="status"))

    if not manager.connection_config:
        flash("Connect to a database before running a bulk status update.", "danger")
        return redirect(url_for("main.index", _anchor="status"))

    new_status = "2" if action == "activate" else "1"
    userids = manager.parse_bulk_ids(text)

    if not userids:
        flash("No valid User IDs found in the text box.", "warning")
        return redirect(url_for("main.index", _anchor="status"))

    try:
        # 1. Verify each User ID against the selected role in the connected DB
        users_map = manager.get_users_by_ids(userids)
        eligible_ids = []
        skipped_reasons = []
        allowed_db_groups = {"manager"} if selected_group == "manager" else {"cashier", "csd"}
        role_label = "Manager" if selected_group == "manager" else "Cashier / CSD"

        for uid in userids:
            record = users_map.get(uid)
            if not record:
                reason = f"{uid} (not found in DB)"
                skipped_reasons.append(reason)
                manager.log(f"BULK ROLE CHECK FAILED | {reason}")
                continue

            db_group = str(record.get("GroupID") or "").strip().lower()
            if db_group not in allowed_db_groups:
                reason = f"{uid} (role is '{record.get('GroupID')}', expected {role_label})"
                skipped_reasons.append(reason)
                manager.log(f"BULK ROLE MISMATCH | {reason}")
                continue

            eligible_ids.append((uid, record))

        if not eligible_ids:
            flash(
                f"Bulk {action} aborted: None of the entered User IDs belong to {role_label}. "
                f"Skipped: {', '.join(skipped_reasons)}",
                "danger",
            )
            return redirect(url_for("main.index", _anchor="status"))

        # 2. Enforce active manager count <= 4 when bulk activating managers
        if selected_group == "manager" and action == "activate":
            current_active = manager.get_active_manager_count()
            newly_activating = sum(
                1 for _, rec in eligible_ids if str(rec.get("UserActive")) != "2"
            )
            if newly_activating > 0 and (current_active + newly_activating) > manager.MAX_ACTIVE_MANAGERS:
                msg = (
                    f"Bulk activation blocked: Existing active managers ({current_active}) + "
                    f"inactive managers to activate ({newly_activating}) = "
                    f"{current_active + newly_activating}, which exceeds the maximum limit "
                    f"of {manager.MAX_ACTIVE_MANAGERS}."
                )
                manager.log(f"BULK MANAGER ACTIVATION BLOCKED | {msg}")
                flash(msg, "danger")
                return redirect(url_for("main.index", _anchor="status"))

        # 3. Execute bulk update on role-verified IDs
        success = 0
        failed = len(skipped_reasons)
        for uid, _ in eligible_ids:
            try:
                manager.update_user_status(uid, new_status, selected_group)
                success += 1
            except Exception as e:
                failed += 1
                logging.error("Failed to update %s: %s", uid, e)
                manager.log(f"BULK UPDATE ERROR | User: {uid} | {e}")

        _refresh_active_manager_count()
        manager.log(
            f"BULK {action.upper()} ({role_label}) | Success: {success} | Failed/Skipped: {failed}"
        )

        summary_msg = f"Bulk {action} ({role_label}) completed. Success: {success}, Failed/Skipped: {failed}."
        if skipped_reasons:
            summary_msg += f" Skipped due to role mismatch/missing: {', '.join(skipped_reasons)}"
        flash(summary_msg, "success" if failed == 0 else "warning")

        manager.managers_list = []
        manager.others_list = []
    except Exception as error:
        logging.exception(str(error))
        flash(f"Bulk status error: {error}", "danger")

    return redirect(url_for("main.index", _anchor="status"))