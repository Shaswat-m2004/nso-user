PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NSO User Manager</title>
  
  <!-- ========================================== -->
  <!-- EXTERNAL RESOURCES & STYLES                -->
  <!-- ========================================== -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
  <style>
    :root { --ink: #172033; --muted: #667085; --blue: #356ae6; --surface: #fff; --line: #e8ebf2; }
    body { color: var(--ink); background: #f5f7fb; font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif; }
    
    /* Layout & Components */
    .topbar { background: #111a2e; color: white; }
    .brand-mark { width: 40px; height: 40px; display: grid; place-items: center; border-radius: 12px; background: #527cf0; }
    .surface { background: var(--surface); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 8px 25px rgba(24, 36, 64, .05); }
    .section-icon { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 12px; background: #edf2ff; color: #315ed7; font-size: 1.2rem; }
    
    /* Navigation Tabs */
    .nav-pills .nav-link { color: var(--muted); border-radius: 10px; font-weight: 600; }
    .nav-pills .nav-link.active { background: #e9efff; color: #315ed7; }
    
    /* Form Inputs */
    .form-label { color: #475467; font-size: .83rem; font-weight: 700; }
    .form-control, .form-select { border-color: #dfe3eb; padding: .7rem .85rem; }
    .form-control:focus, .form-select:focus { border-color: var(--blue); box-shadow: 0 0 0 .2rem rgba(53,106,230,.12); }
    .btn-primary { background: var(--blue); border-color: var(--blue); }
    
    /* Status & Logs */
    .status-dot { width: 9px; height: 9px; border-radius: 50%; background: #f04438; display: inline-block; }
    .status-dot.connected { background: #12b76a; }
    .log { background: #101828; color: #d0d5dd; min-height: 180px; max-height: 310px; overflow: auto; white-space: pre-wrap; font: .78rem/1.6 ui-monospace, SFMono-Regular, Consolas, monospace; }
    
    /* Tables inside scrollable cards */
    .table-container { max-height: 350px; overflow-y: auto; border: 1px solid var(--line); border-radius: 8px; }
    .table th { position: sticky; top: 0; background-color: #f8f9fa; z-index: 1; }
  </style>
</head>
<body>

  <!-- ========================================== -->
  <!-- HEADER / APP BAR                           -->
  <!-- ========================================== -->
  <header class="topbar py-3">
    <div class="container d-flex align-items-center justify-content-between">
      <div class="d-flex gap-3 align-items-center">
        <div class="brand-mark"><i class="bi bi-person-gear fs-5"></i></div>
        <div>
          <div class="fw-bold">NSO User Manager</div>
          <small class="text-white-50">Operations console</small>
        </div>
      </div>
      <div class="small">
        <span class="status-dot {% if connected %}connected{% endif %}"></span> 
        <span class="ms-1">{% if connected %}Connected{% else %}Not connected{% endif %}</span>
      </div>
    </div>
  </header>

  <main class="container py-4 py-lg-5">
    
    <!-- ========================================== -->
    <!-- FLASH MESSAGES / ALERTS                    -->
    <!-- ========================================== -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
            <i class="bi bi-{% if category == 'success' %}check-circle{% else %}exclamation-triangle{% endif %} me-2"></i>
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
          </div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <!-- ========================================== -->
    <!-- NAVIGATION TABS                            -->
    <!-- ========================================== -->
    <div class="surface p-2 mb-4">
      <ul class="nav nav-pills nav-fill" id="workspaceTabs" role="tablist">
        <li class="nav-item">
          <button class="nav-link active" data-bs-toggle="pill" data-bs-target="#connect" type="button"><i class="bi bi-plug me-2"></i>Connect Database</button>
        </li>
        <li class="nav-item">
          <button class="nav-link" data-bs-toggle="pill" data-bs-target="#add" type="button"><i class="bi bi-person-plus me-2"></i>Add New User</button>
        </li>
        <li class="nav-item">
          <button class="nav-link" data-bs-toggle="pill" data-bs-target="#bulk" type="button"><i class="bi bi-file-earmark-spreadsheet me-2"></i>Bulk Upload</button>
        </li>
        <li class="nav-item">
          <button class="nav-link" data-bs-toggle="pill" data-bs-target="#status" type="button"><i class="bi bi-person-lines-fill me-2"></i>Manage User Status</button>
        </li>
      </ul>
    </div>

    <!-- ========================================== -->
    <!-- TAB CONTENT SECTIONS                       -->
    <!-- ========================================== -->
    <div class="tab-content">
      
      <!-- 1. CONNECT DATABASE TAB -->
      <div class="tab-pane fade show active" id="connect">
        <div class="surface p-4 p-lg-5">
          <div class="d-flex gap-3 mb-4">
            <div class="section-icon"><i class="bi bi-database-check"></i></div>
            <div>
              <h2 class="h4 mb-1">Database connection</h2>
              <p class="text-secondary mb-0">Set your SQL Server details and test the connection before managing users.</p>
            </div>
          </div>
          <form method="post" action="{{ url_for('main.connect') }}">
            <div class="row g-3">
              <div class="col-md-8">
                <label class="form-label">Server IP address</label>
                <input class="form-control" name="ip" placeholder="192.168.1.10" value="{{ config.ip if config else '' }}" required>
              </div> 
              <div class="col-md-6">
                <label class="form-label">Database</label>
                <input class="form-control" name="database" placeholder="WarehouseDB" value="{{ config.database if config else '' }}" required>
              </div>
              <div class="col-md-6">
                <label class="form-label">Username</label>
                <input class="form-control" name="username" value="{{ config.username if config else '' }}" required>
              </div>
              <div class="col-md-6">
                <label class="form-label">Password</label>
                <input class="form-control" type="password" name="password" placeholder="SQL Server password" required>
              </div>
            </div>
            <div class="d-flex gap-2 mt-4">
              <button type="submit" class="btn btn-primary px-4"><i class="bi bi-plug me-2"></i>Test & Connect</button>
            </div>
          </form>
        </div>
      </div>

      <!-- 2. ADD USER TAB (Includes Active Managers) -->
      <div class="tab-pane fade" id="add">
        <div class="surface p-4 p-lg-5">
          
          <div class="d-flex gap-3 mb-4">
            <div class="section-icon"><i class="bi bi-person-plus"></i></div>
            <div>
              <h2 class="h4 mb-1">Add a new user</h2>
              <p class="text-secondary mb-0">Enter the new user's details. Maximum {{ max_active_managers }} active managers are allowed per database.</p>
            </div>
          </div>
          
          <form method="post" action="{{ url_for('main.add_user') }}">
            <div class="row g-3">
              <div class="col-md-6">
                <label class="form-label">Warehouse</label>
                <input class="form-control" name="warehouse" placeholder="4-digit warehouse ID" required>
              </div>
              <div class="col-md-6">
                <label class="form-label">Role</label>
                <select class="form-select" name="role">
                  <option>manager</option>
                  <option>cashier</option>
                  <option>csd</option>
                </select>
              </div>
              <div class="col-md-6">
                <label class="form-label">User name</label>
                <input class="form-control" name="name" placeholder="Letters only" required>
              </div>
              <div class="col-md-6">
                <label class="form-label">User ID</label>
                <input class="form-control" name="userid" placeholder="Minimum 4 digits" required>
              </div>
              <div class="col-12">
                <button class="btn btn-primary px-4"><i class="bi bi-person-check me-2"></i>Create User</button>
              </div>
            </div>
          </form>

          <!-- 2B. ACTIVE MANAGERS LIST -->
          <div class="border-top mt-4 pt-4">
            <div class="d-flex justify-content-between align-items-center mb-3">
              <div>
                <h3 class="h6 mb-1">Active Managers</h3>
                <p class="text-secondary small mb-0">Check the active managers in the connected database.</p>
              </div>
              <form method="post" action="{{ url_for('main.active_managers') }}">
                <button class="btn btn-outline-primary px-4"><i class="bi bi-people me-2"></i>Check Active Managers</button>
              </form>
            </div>
            
            {% if active_manager_columns %}
              <div class="table-responsive">
                <table class="table table-sm table-bordered align-middle mb-0">
                  <thead>
                    <tr>{% for column in active_manager_columns %}<th>{{ column }}</th>{% endfor %}</tr>
                  </thead>
                  <tbody>
                    {% for row in active_managers %}
                      <tr>{% for value in row %}<td>{{ value }}</td>{% endfor %}</tr>
                    {% endfor %}
                  </tbody>
                </table>
              </div>
              <div class="small text-secondary mt-2">{{ active_managers|length }} active manager(s) found.</div>
            {% endif %}
          </div>
        </div>
      </div>

      <!-- 3. BULK UPLOAD TAB -->
      <div class="tab-pane fade" id="bulk">
        <div class="surface p-4 p-lg-5">
          <div class="d-flex gap-3 mb-4">
            <div class="section-icon"><i class="bi bi-upload"></i></div>
            <div>
              <h2 class="h4 mb-1">Bulk upload</h2>
              <p class="text-secondary mb-0">Upload a CSV or Excel file with WarehouseID, UserRole, UserName, and UserID columns. Total active managers (existing + new) cannot exceed {{ max_active_managers }}.</p>
            </div>
          </div>
          
          <div class="mb-3">
            <button type="button" class="btn btn-outline-secondary px-4" onclick="downloadTemplate()">
              <i class="bi bi-download me-2"></i>Download Template
            </button>

            <script>
            function downloadTemplate() {
              if (window.pywebview && window.pywebview.api) {
                window.pywebview.api.download_template().then(response => {
                  if (response.status === "success") {
                    console.log("Template saved successfully!");
                  }
                });
              } else {
                window.location.href = "/download-template";
              }
            }
            </script>
          </div>

          <form method="post" action="{{ url_for('main.bulk_upload') }}" enctype="multipart/form-data">
            <input class="form-control" type="file" name="file" accept=".csv,.xlsx" required>
            <button type="submit" class="btn btn-primary mt-3 px-4">
              <i class="bi bi-cloud-upload me-2"></i>Process File
            </button>
          </form>
        </div>
      </div>

      <!-- 4. MANAGE USER STATUS TAB -->
      <div class="tab-pane fade" id="status">
        <div class="surface p-4 p-lg-5">
          <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4">
            <div class="d-flex gap-3">
              <div class="section-icon"><i class="bi bi-person-lines-fill"></i></div>
              <div>
                <h2 class="h4 mb-1">User Status Management</h2>
                <p class="text-secondary mb-0">Activate or deactivate database IDs individually or in bulk.</p>
              </div>
            </div>

            <!-- Live Active Manager Count Badge -->
            <div id="active-manager-tracker" class="d-flex align-items-center gap-2">
              {% if active_manager_count is not none %}
                <span id="active-manager-badge" class="badge fs-6 px-3 py-2 {% if active_manager_count > max_active_managers %}bg-danger{% elif active_manager_count == max_active_managers %}bg-warning text-dark{% else %}bg-success{% endif %}">
                  <i class="bi bi-person-badge me-1"></i>
                  Active Managers: <span id="active-manager-count-val">{{ active_manager_count }}</span> / {{ max_active_managers }}
                </span>
              {% else %}
                <span id="active-manager-badge" class="badge fs-6 px-3 py-2 bg-secondary">
                  <i class="bi bi-person-badge me-1"></i>
                  Active Managers: -- / {{ max_active_managers }}
                </span>
              {% endif %}
            </div>
          </div>

          <!-- Flag Banner when Active Manager Count > 4 -->
          <div id="active-manager-flag" class="alert alert-danger d-flex align-items-center {% if active_manager_count is none or active_manager_count <= max_active_managers %}d-none{% endif %}" role="alert">
            <i class="bi bi-flag-fill me-2"></i>
            <span id="active-manager-flag-text">
              {% if active_manager_count is not none and active_manager_count > max_active_managers %}
                Flag: Connected database currently has {{ active_manager_count }} active managers, which exceeds the maximum allowed limit of {{ max_active_managers }}. Manager activation and creation are blocked until count is reduced below {{ max_active_managers }}.
              {% endif %}
            </span>
          </div>

          <div id="status-action-message" class="alert d-none" role="status"></div>
          
          <div class="row g-4">
            
            <!-- SECTION: Manager Status -->
            <div class="col-lg-6">
              <div class="card shadow-sm border-0 bg-light">
                <div class="card-body">
                  <div class="d-flex justify-content-between align-items-center mb-3">
                    <h3 class="h6 mb-0 fw-bold">Managers</h3>
                    <form method="post" action="{{ url_for('main.fetch_users', group='manager') }}">
                      <button class="btn btn-sm btn-outline-primary shadow-sm"><i class="bi bi-arrow-clockwise me-1"></i>Fetch</button>
                    </form>
                  </div>
                  
                  {% if managers_list %}
                    <div class="input-group input-group-sm mb-3">
                      <span class="input-group-text"><i class="bi bi-search"></i></span>
                      <input id="manager-user-search" type="search" class="form-control" placeholder="Search by username or User ID" aria-label="Search managers by username or User ID" autocomplete="off">
                    </div>
                    <div class="table-container bg-white">
                      <table class="table table-sm table-hover align-middle mb-0 text-center">
                        <thead><tr><th>User ID</th><th>Username</th><th>Status</th><th>Action</th></tr></thead>
                        <tbody id="manager-status-rows">
                          {% for row in managers_list %}
                          <tr data-userid="{{ row.userid }}" data-username="{{ row.username }}">
                            <td class="fw-bold">{{ row.userid }}</td>
                            <td>{{ row.username }}</td>
                            <td>
                              {% if row.UserActive|string == '2' %}
                                <span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25">Active</span>
                              {% else %}
                                <span class="badge bg-secondary bg-opacity-10 text-secondary border border-secondary border-opacity-25">Inactive</span>
                              {% endif %}
                            </td>
                            <td>
                              <form method="post" action="{{ url_for('main.toggle_status') }}" class="status-toggle-form">
                                <input type="hidden" name="userid" value="{{ row.userid }}">
                                <input type="hidden" name="current_status" value="{{ row.UserActive }}">
                                <input type="hidden" name="group" value="manager">
                                {% if row.UserActive|string == '2' %}
                                  <button class="btn btn-sm btn-outline-danger w-100">Deactivate</button>
                                {% else %}
                                  <button class="btn btn-sm btn-outline-success w-100">Activate</button>
                                {% endif %}
                              </form>
                            </td>
                          </tr>
                          {% endfor %}
                        </tbody>
                      </table>
                    </div>
                  {% else %}
                    <div class="text-muted small text-center p-3 border rounded bg-white">Click "Fetch" to load manager status data.</div>
                  {% endif %}
                </div>
              </div>
            </div>

            <!-- SECTION: Other Users Status -->
            <div class="col-lg-6">
              <div class="card shadow-sm border-0 bg-light">
                <div class="card-body">
                  <div class="d-flex justify-content-between align-items-center mb-3">
                    <h3 class="h6 mb-0 fw-bold">Cashiers / CSDs</h3>
                    <form method="post" action="{{ url_for('main.fetch_users', group='others') }}">
                      <button class="btn btn-sm btn-outline-secondary shadow-sm"><i class="bi bi-arrow-clockwise me-1"></i>Fetch</button>
                    </form>
                  </div>
                  
                  {% if others_list %}
                    <div class="input-group input-group-sm mb-3">
                      <span class="input-group-text"><i class="bi bi-search"></i></span>
                      <input id="other-user-search" type="search" class="form-control" placeholder="Search by username or User ID" aria-label="Search cashiers and CSDs by username or User ID" autocomplete="off">
                    </div>
                    <div class="table-container bg-white">
                      <table class="table table-sm table-hover align-middle mb-0 text-center">
                        <thead><tr><th>User ID</th><th>Username</th><th>Status</th><th>Action</th></tr></thead>
                        <tbody id="other-status-rows">
                          {% for row in others_list %}
                          <tr data-userid="{{ row.userid }}" data-username="{{ row.username }}">
                            <td class="fw-bold">{{ row.userid }}</td>
                            <td>{{ row.username }}</td>
                            <td>
                              {% if row.UserActive|string == '2' %}
                                <span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25">Active</span>
                              {% else %}
                                <span class="badge bg-secondary bg-opacity-10 text-secondary border border-secondary border-opacity-25">Inactive</span>
                              {% endif %}
                            </td>
                            <td>
                              <form method="post" action="{{ url_for('main.toggle_status') }}" class="status-toggle-form">
                                <input type="hidden" name="userid" value="{{ row.userid }}">
                                <input type="hidden" name="current_status" value="{{ row.UserActive }}">
                                <input type="hidden" name="group" value="others">
                                {% if row.UserActive|string == '2' %}
                                  <button class="btn btn-sm btn-outline-danger w-100">Deactivate</button>
                                {% else %}
                                  <button class="btn btn-sm btn-outline-success w-100">Activate</button>
                                {% endif %}
                              </form>
                            </td>
                          </tr>
                          {% endfor %}
                        </tbody>
                      </table>
                    </div>
                  {% else %}
                    <div class="text-muted small text-center p-3 border rounded bg-white">Click "Fetch" to load cashier/csd data.</div>
                  {% endif %}
                </div>
              </div>
            </div>
            
            <!-- SECTION: Bulk Update -->
            <div class="col-12 mt-4 pt-3 border-top">
              <h3 class="h6 fw-bold mb-2"><i class="bi bi-collection me-2 text-primary"></i>Mass Activate / Deactivate</h3>
              <p class="text-secondary small mb-3">Select the role group first. Each User ID will be verified against the selected role before running the bulk action.</p>
              
              <form method="post" action="{{ url_for('main.bulk_status') }}">
                <div class="row g-3 mb-3">
                  <div class="col-md-4">
                    <label for="bulk-group-select" class="form-label">User Role Group</label>
                    <select id="bulk-group-select" class="form-select" name="bulk_group" required>
                      <option value="manager">Manager</option>
                      <option value="others">Cashier / CSD</option>
                    </select>
                  </div>
                </div>
                <textarea class="form-control mb-3" name="userids" rows="3" placeholder="e.g. 5001, 5002, 5003" required></textarea>
                <div class="d-flex gap-2">
                  <button type="submit" name="action" value="activate" class="btn btn-success px-4"><i class="bi bi-check-circle me-2"></i>Mass Activate</button>
                  <button type="submit" name="action" value="deactivate" class="btn btn-danger px-4"><i class="bi bi-x-circle me-2"></i>Mass Deactivate</button>
                </div>
              </form>
            </div>
            
          </div>
        </div>
      </div>
      
    </div> <!-- END TAB CONTENT -->

    <!-- ========================================== -->
    <!-- ACTIVITY LOG                               -->
    <!-- ========================================== -->
    <section class="mt-4">
      <div class="d-flex justify-content-between align-items-center mb-2">
        <h2 class="h6 text-uppercase text-secondary fw-bold mb-0">Activity log</h2>
        <span class="small text-secondary">{{ logs|length }} events</span>
      </div>
      <div class="surface log p-3">
        {% if logs %}
          {{ logs|join('\\n') }}
        {% else %}
          No activity yet. Connect to a database to get started.
        {% endif %}
      </div>
    </section>
    
  </main>
  
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    function activateTabFromHash() {
      const hash = window.location.hash;
      if (!hash) return;
      const trigger = document.querySelector(`button[data-bs-target="${hash}"]`);
      if (trigger && window.bootstrap && bootstrap.Tab) {
        const tab = new bootstrap.Tab(trigger);
        tab.show();
      }
    }

    window.addEventListener('load', activateTabFromHash);
    window.addEventListener('hashchange', activateTabFromHash);

    const managerSearch = document.getElementById('manager-user-search');
    if (managerSearch) {
      managerSearch.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        document.querySelectorAll('#manager-status-rows tr').forEach(function (row) {
          const userId = (row.dataset.userid || '').toLowerCase();
          const username = (row.dataset.username || '').toLowerCase();
          row.hidden = Boolean(query) && !userId.includes(query) && !username.includes(query);
        });
      });
    }

    const otherUserSearch = document.getElementById('other-user-search');
    if (otherUserSearch) {
      otherUserSearch.addEventListener('input', function () {
        const query = this.value.trim().toLowerCase();
        document.querySelectorAll('#other-status-rows tr').forEach(function (row) {
          const userId = (row.dataset.userid || '').toLowerCase();
          const username = (row.dataset.username || '').toLowerCase();
          row.hidden = Boolean(query) && !userId.includes(query) && !username.includes(query);
        });
      });
    }

    function showStatusActionMessage(message, success) {
      const messageBox = document.getElementById('status-action-message');
      messageBox.textContent = message;
      messageBox.className = `alert alert-${success ? 'success' : 'danger'}`;
    }

    function updateActiveManagerTracker(count, maxLimit) {
      if (count === null || count === undefined) return;
      const badge = document.getElementById('active-manager-badge');
      const flag = document.getElementById('active-manager-flag');
      const flagText = document.getElementById('active-manager-flag-text');
      const limit = maxLimit || 4;

      if (badge) {
        badge.className = 'badge fs-6 px-3 py-2 ' + (
          count > limit ? 'bg-danger' : (count === limit ? 'bg-warning text-dark' : 'bg-success')
        );
        badge.innerHTML = `<i class="bi bi-person-badge me-1"></i> Active Managers: <span id="active-manager-count-val">${count}</span> / ${limit}`;
      }

      if (flag && flagText) {
        if (count > limit) {
          flagText.textContent =
            `Flag: Connected database currently has ${count} active managers, which exceeds the maximum allowed limit of ${limit}. ` +
            `Manager activation and creation are blocked until count is reduced below ${limit}.`;
          flag.classList.remove('d-none');
        } else {
          flag.classList.add('d-none');
        }
      }
    }

    document.querySelectorAll('.status-toggle-form').forEach(function (form) {
      form.addEventListener('submit', async function (event) {
        event.preventDefault();
        const button = form.querySelector('button[type="submit"], button');
        const originalLabel = button.textContent;
        button.disabled = true;
        button.textContent = 'Updating...';

        try {
          const response = await fetch(form.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: new FormData(form)
          });
          const result = await response.json();
          if (result.active_manager_count !== undefined) {
            updateActiveManagerTracker(result.active_manager_count, result.max_active_managers);
          }
          if (!response.ok || !result.success) {
            throw new Error(result.error || 'Unable to update the user status.');
          }

          const isActive = result.status === '2';
          const statusCell = form.closest('tr').children[2];
          statusCell.innerHTML = isActive
            ? '<span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25">Active</span>'
            : '<span class="badge bg-secondary bg-opacity-10 text-secondary border border-secondary border-opacity-25">Inactive</span>';
          form.querySelector('input[name="current_status"]').value = result.status;
          button.className = `btn btn-sm w-100 ${isActive ? 'btn-outline-danger' : 'btn-outline-success'}`;
          button.textContent = isActive ? 'Deactivate' : 'Activate';
          showStatusActionMessage(`User ${result.userid} is now ${isActive ? 'active' : 'inactive'}.`, true);
        } catch (error) {
          button.textContent = originalLabel;
          showStatusActionMessage(error.message, false);
        } finally {
          button.disabled = false;
        }
      });
    });
  </script>
</body>
</html>
"""