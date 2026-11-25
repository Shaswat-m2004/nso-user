import ipaddress
import logging
import re
import pymssql
from app.config import Config


class UserManagementApp:
    MAX_ACTIVE_MANAGERS = 4
    ROLES = {
        "manager": "Manager.sql",
        "cashier": "Cashier.sql",
        "csd": "CSD.sql",
    }
    ACTIVE_MANAGERS_SQL = "ActiveManagers.sql"
    RESET_PASSWORD_SQL = "ResetPassword.sql"
    DEACTIVATE_USER_SQL = "DeactivateUser.sql"

    def __init__(self):
        self.connection_config = None
        self.logs = []
        self.active_manager_columns = []
        self.active_managers = []
        self.managers_list = []
        self.others_list = []
        self.active_manager_count = None

    def log(self, text):
        self.logs.append(str(text))
        logging.info(text)

    def validate_ip(self, ip):
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    def connect(self, config):
        if not self.validate_ip(config["ip"]):
            raise ValueError("Invalid server IP address")
        if not config["database"] or not config["username"]:
            raise ValueError("Database and username are required")
        port = 1433

        connection = pymssql.connect(
            server=f"{config['ip']}:{port}",
            user=config["username"],
            password=config["password"],
            database=config["database"],
            login_timeout=10,
            timeout=60,
        )
        connection.close()
        self.connection_config = {**config, "port": str(port)}
        self.managers_list = []
        self.others_list = []
        self.log(f"CONNECTED | {config['ip']}:{port} | {config['database']}")
        try:
            count = self.get_active_manager_count()
            if count > self.MAX_ACTIVE_MANAGERS:
                self.log(
                    f"FLAG | Connected DB has {count} active managers "
                    f"(limit is {self.MAX_ACTIVE_MANAGERS})"
                )
        except Exception as err:
            self.active_manager_count = None
            self.log(f"ACTIVE MANAGER COUNT CHECK FAILED | {err}")

    def get_connection(self):
        if not self.connection_config:
            raise ValueError("Connect to a database before running an operation")
        config = self.connection_config
        return pymssql.connect(
            server=f"{config['ip']}:{config['port']}",
            user=config["username"],
            password=config["password"],
            database=config["database"],
            login_timeout=10,
            timeout=60,
        )

    def validate_record(self, ip, warehouse, role, username, userid):
        if not self.validate_ip(ip):
            return False, "Invalid IP"
        if not warehouse:
            return False, "Warehouse Missing"

        if role.lower() not in self.ROLES:
            return False, "Invalid Role"

        if not re.fullmatch(r"[A-Za-z][A-Za-z ]*", str(username or "")):
            return False, "Invalid Username"

        # Clean the userid input
        if userid is None or str(userid).strip() == "" or str(userid).lower() == "nan":
            return False, "User ID missing"

        # Handle float conversion (e.g., 3455.0 -> "3455")
        userid_str = str(userid).split(".")[0].strip()

        if not userid_str.isdigit():
            return False, "User ID must be numeric"

        if len(userid_str) < 4:
            return False, "User ID minimum length = 4"

        return True, "Valid"

    def execute_query(self, ip, warehouse, role, username, userid):
        sql_path = Config.BASE_DIR / self.ROLES[role.lower()]

        clean_userid = str(userid).split(".")[0].strip()
        if not sql_path.exists():
            raise FileNotFoundError(f"{sql_path.name} not found")
        query = sql_path.read_text(encoding="utf-8")
        query = query.replace("{WAREHOUSE}", warehouse)
        query = query.replace("{USERID}", clean_userid)
        query = query.replace("{NAME}", username)

        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            cursor.close()
        finally:
            connection.close()

    def get_active_managers(self):
        sql_path = Config.BASE_DIR / self.ACTIVE_MANAGERS_SQL
        if not sql_path.exists():
            raise FileNotFoundError(f"{sql_path.name} not found")

        query = sql_path.read_text(encoding="utf-8")
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description] if cursor.description else []
            cursor.close()
            self.active_manager_count = len(rows)
            return columns, rows
        finally:
            connection.close()

    def get_active_manager_count(self):
        """Return the live count of active managers (UserActive = 2) in the connected DB."""
        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            query = (
                "SELECT COUNT(*) FROM [user] (nolock) "
                "WHERE LOWER(GroupID) = 'manager' "
                "AND UserActive = 2 "
                "AND company = '100' AND division = '200'"
            )
            cursor.execute(query)
            row = cursor.fetchone()
            cursor.close()
            count = int(row[0]) if row and row[0] is not None else 0
            self.active_manager_count = count
            return count
        finally:
            connection.close()

    def get_users_by_ids(self, userids):
        """
        Fetch userid, username, GroupID, and UserActive for a list of User IDs.
        Returns a dict keyed by string userid.
        """
        clean_ids = [str(uid).strip() for uid in userids if str(uid).strip()]
        if not clean_ids:
            return {}

        placeholders = ", ".join(["%s"] * len(clean_ids))
        query = (
            f"SELECT userid, username, GroupID, UserActive "
            f"FROM [user] (nolock) "
            f"WHERE CAST(userid AS VARCHAR(50)) IN ({placeholders}) "
            f"AND company = '100' AND division = '200'"
        )
        connection = self.get_connection()
        try:
            cursor = connection.cursor(as_dict=True)
            cursor.execute(query, tuple(clean_ids))
            rows = cursor.fetchall()
            cursor.close()
            return {str(row["userid"]).strip(): row for row in rows}
        finally:
            connection.close()

    def fetch_user_status(self, group_type):
        connection = self.get_connection()
        try:
            cursor = connection.cursor(as_dict=True)
            if group_type == "manager":
                query = (
                    "SELECT userid, username, UserActive FROM [user] (nolock) "
                    "WHERE GroupID = 'manager' AND company = '100' AND division = '200'"
                )
            else:
                query = (
                    "SELECT userid, username, UserActive FROM [user] (nolock) "
                    "WHERE GroupID IN ('cashier', 'csd') AND company = '100' AND division = '200'"
                )

            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            if group_type == "manager":
                self.active_manager_count = sum(
                    1 for r in rows if str(r.get("UserActive")) == "2"
                )
            return rows
        finally:
            connection.close()

    def update_user_status(self, userid, status_val, group_type):
        """status_val should be '1' (inactive) or '2' (active)"""
        if status_val not in {"1", "2"}:
            raise ValueError("status_val must be '1' (inactive) or '2' (active)")

        sql_filename = self.DEACTIVATE_USER_SQL if status_val == "1" else self.RESET_PASSWORD_SQL
        sql_path = Config.BASE_DIR / sql_filename

        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file '{sql_filename}' not found in root directory")

        query = sql_path.read_text(encoding="utf-8")
        query = query.replace("{USERID}", str(userid))

        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            cursor.close()
        finally:
            connection.close()

    def reset_user_password(self, userid, group_type):
        """Reset/activate a user using the shared ResetPassword.sql file."""
        sql_path = Config.BASE_DIR / self.RESET_PASSWORD_SQL

        if not sql_path.exists():
            raise FileNotFoundError(f"Missing password reset SQL file: {self.RESET_PASSWORD_SQL}")

        query = sql_path.read_text(encoding="utf-8")
        query = query.replace("{USERID}", str(userid))

        connection = self.get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            cursor.close()
            self.log(f"PASSWORD RESET SUCCESS | User: {userid} | Group: {group_type}")
        finally:
            connection.close()

    def parse_bulk_ids(self, text):
        raw_ids = re.split(r"[\s,]+", text.strip())
        seen = set()
        result = []
        for uid in raw_ids:
            if uid and uid not in seen:
                seen.add(uid)
                result.append(uid)
        return result