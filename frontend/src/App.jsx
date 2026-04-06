import { useEffect, useMemo, useState } from "react";
import api from "./api";

function App() {
  const [token, setToken] = useState(localStorage.getItem("auth_token") || "");
  const [profile, setProfile] = useState(() => {
    const raw = localStorage.getItem("auth_profile");
    return raw ? JSON.parse(raw) : null;
  });

  const [loginRole, setLoginRole] = useState("manager");
  const [loginUsername, setLoginUsername] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const [tasks, setTasks] = useState([]);
  const [employees, setEmployees] = useState([]);

  const [taskTitle, setTaskTitle] = useState("");
  const [taskDescription, setTaskDescription] = useState("");
  const [taskDeadline, setTaskDeadline] = useState("");
  const [taskEmployeeId, setTaskEmployeeId] = useState("");

  const [employeeName, setEmployeeName] = useState("");
  const [employeePassword, setEmployeePassword] = useState("");

  const [reasonByTaskId, setReasonByTaskId] = useState({});

  const [loading, setLoading] = useState(false);
  const [submittingTask, setSubmittingTask] = useState(false);
  const [submittingEmployee, setSubmittingEmployee] = useState(false);
  const [error, setError] = useState("");
  const [notification, setNotification] = useState({ overdue_count: 0, overdue_tasks: [] });

  const completedCount = useMemo(() => tasks.filter((task) => task.status === "completed").length, [tasks]);
  const overdueCount = useMemo(() => tasks.filter((task) => task.is_overdue).length, [tasks]);

  const isManager = profile?.role === "manager";
  const isEmployee = profile?.role === "employee";

  const logout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_profile");
    setToken("");
    setProfile(null);
    setTasks([]);
    setEmployees([]);
    setError("");
  };

  const extractError = (err, fallback) => err?.response?.data?.detail || fallback;

  const login = async (event) => {
    event.preventDefault();
    setError("");
    try {
      const response = await api.post("/auth/login", {
        role: loginRole,
        username: loginUsername.trim(),
        password: loginPassword,
      });

      const authToken = response.data.access_token;
      const nextProfile = {
        role: response.data.role,
        username: response.data.username,
        user_id: response.data.user_id,
      };

      localStorage.setItem("auth_token", authToken);
      localStorage.setItem("auth_profile", JSON.stringify(nextProfile));
      setToken(authToken);
      setProfile(nextProfile);
      setLoginPassword("");
      setLoginUsername("");
    } catch (err) {
      setError(extractError(err, "Login failed."));
    }
  };

  const fetchPortalData = async () => {
    if (!token || !profile) return;
    setLoading(true);
    setError("");
    try {
      const [tasksResponse, notificationsResponse] = await Promise.all([
        api.get("/tasks"),
        api.get("/notifications"),
      ]);

      setTasks(tasksResponse.data);
      setNotification(notificationsResponse.data);

      if (profile.role === "manager") {
        const employeesResponse = await api.get("/employees");
        setEmployees(employeesResponse.data);
      }
    } catch (err) {
      setError(extractError(err, "Failed to load portal data."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortalData();
  }, [token, profile]);

  const handleCreateEmployee = async (event) => {
    event.preventDefault();
    if (!employeeName.trim() || !employeePassword.trim()) return;

    setSubmittingEmployee(true);
    setError("");
    try {
      await api.post("/employees", {
        name: employeeName.trim(),
        password: employeePassword,
      });
      setEmployeeName("");
      setEmployeePassword("");
      await fetchPortalData();
    } catch (err) {
      setError(extractError(err, "Failed to add employee."));
    } finally {
      setSubmittingEmployee(false);
    }
  };

  const handleCreateTask = async (event) => {
    event.preventDefault();
    if (!taskTitle.trim() || !taskDescription.trim() || !taskDeadline || !taskEmployeeId) {
      return;
    }

    setSubmittingTask(true);
    setError("");
    try {
      await api.post("/tasks", {
        title: taskTitle.trim(),
        description: taskDescription.trim(),
        deadline: new Date(taskDeadline).toISOString(),
        assigned_employee_id: Number(taskEmployeeId),
      });
      setTaskTitle("");
      setTaskDescription("");
      setTaskDeadline("");
      setTaskEmployeeId("");
      await fetchPortalData();
    } catch (err) {
      setError(extractError(err, "Failed to assign task."));
    } finally {
      setSubmittingTask(false);
    }
  };

  const updateTaskStatus = async (taskId, statusValue) => {
    setError("");
    try {
      const reason = reasonByTaskId[taskId]?.trim() || null;
      await api.put(`/tasks/${taskId}/status`, {
        status: statusValue,
        not_completed_reason: statusValue === "not_completed" ? reason : null,
      });
      await fetchPortalData();
    } catch (err) {
      setError(extractError(err, "Failed to update task status."));
    }
  };

  const handleDeleteTask = async (taskId) => {
    setError("");
    try {
      await api.delete(`/tasks/${taskId}`);
      await fetchPortalData();
    } catch (err) {
      setError(extractError(err, "Failed to delete task."));
    }
  };

  if (!token || !profile) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-orange-50 px-4 py-10 text-ink">
        <div className="mx-auto max-w-md rounded-2xl bg-white/90 p-6 shadow-soft">
          <h1 className="mb-2 text-3xl font-bold">Company Task Portal</h1>
          <p className="mb-6 text-sm text-slate-500">Sign in as manager or employee.</p>
          <form onSubmit={login} className="space-y-3">
            <select
              value={loginRole}
              onChange={(event) => setLoginRole(event.target.value)}
              className="w-full rounded-xl border border-slate-200 px-4 py-3"
            >
              <option value="manager">Login as Manager</option>
              <option value="employee">Login as Employee</option>
            </select>
            <input
              type="text"
              value={loginUsername}
              onChange={(event) => setLoginUsername(event.target.value)}
              placeholder={loginRole === "manager" ? "Manager username" : "Employee name"}
              className="w-full rounded-xl border border-slate-200 px-4 py-3"
            />
            <input
              type="password"
              value={loginPassword}
              onChange={(event) => setLoginPassword(event.target.value)}
              placeholder="Password"
              className="w-full rounded-xl border border-slate-200 px-4 py-3"
            />
            <button type="submit" className="w-full rounded-xl bg-ink px-4 py-3 text-white">
              Sign In
            </button>
          </form>
          {error && <p className="mt-4 text-sm text-rose-700">{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-orange-50 px-4 py-8 text-ink">
      <div className="mx-auto w-full max-w-5xl rounded-2xl bg-white/90 p-5 shadow-soft backdrop-blur sm:p-8">
        <header className="mb-6 border-b border-slate-100 pb-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Company Task Portal</h1>
              <p className="mt-1 text-sm text-slate-500">
                Signed in as {profile.username} ({profile.role})
              </p>
            </div>
            <button onClick={logout} className="rounded-lg bg-slate-200 px-4 py-2 text-sm font-medium">
              Logout
            </button>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Managers can add employees and assign tasks. Employees update completion status.
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-sm">
            <span className="rounded-full bg-slate-100 px-3 py-1">
              Total: {tasks.length}
            </span>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-700">
              Completed: {completedCount}
            </span>
            <span className="rounded-full bg-rose-100 px-3 py-1 text-rose-700">
              Overdue: {overdueCount}
            </span>
          </div>
          {notification.overdue_count > 0 && (
            <p className="mt-2 text-sm text-rose-700">
              You have {notification.overdue_count} overdue task(s) on your dashboard.
            </p>
          )}
        </header>

        {isManager && (
          <section className="mb-6 grid gap-4 md:grid-cols-2">
            <form onSubmit={handleCreateEmployee} className="rounded-xl border border-slate-200 p-4">
              <h2 className="mb-3 text-lg font-semibold">Add Employee</h2>
              <div className="space-y-2">
                <input
                  type="text"
                  value={employeeName}
                  onChange={(event) => setEmployeeName(event.target.value)}
                  placeholder="Employee name"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2"
                />
                <input
                  type="password"
                  value={employeePassword}
                  onChange={(event) => setEmployeePassword(event.target.value)}
                  placeholder="Employee password"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2"
                />
                <button
                  type="submit"
                  disabled={submittingEmployee}
                  className="rounded-lg bg-ink px-4 py-2 text-sm text-white"
                >
                  {submittingEmployee ? "Adding..." : "Add Employee"}
                </button>
              </div>
            </form>

            <form onSubmit={handleCreateTask} className="rounded-xl border border-slate-200 p-4">
              <h2 className="mb-3 text-lg font-semibold">Assign Task</h2>
              <div className="space-y-2">
                <input
                  type="text"
                  value={taskTitle}
                  onChange={(event) => setTaskTitle(event.target.value)}
                  placeholder="Task name"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2"
                />
                <textarea
                  value={taskDescription}
                  onChange={(event) => setTaskDescription(event.target.value)}
                  placeholder="Task description"
                  className="w-full rounded-lg border border-slate-200 px-3 py-2"
                  rows={3}
                />
                <input
                  type="datetime-local"
                  value={taskDeadline}
                  onChange={(event) => setTaskDeadline(event.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2"
                />
                <select
                  value={taskEmployeeId}
                  onChange={(event) => setTaskEmployeeId(event.target.value)}
                  className="w-full rounded-lg border border-slate-200 px-3 py-2"
                >
                  <option value="">Assign to employee</option>
                  {employees.map((employee) => (
                    <option key={employee.id} value={employee.id}>
                      {employee.name}
                    </option>
                  ))}
                </select>
                <button
                  type="submit"
                  disabled={submittingTask}
                  className="rounded-lg bg-ink px-4 py-2 text-sm text-white"
                >
                  {submittingTask ? "Assigning..." : "Assign Task"}
                </button>
              </div>
            </form>
          </section>
        )}

        {error && (
          <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <section>
          {loading ? (
            <p className="text-sm text-slate-500">Loading tasks...</p>
          ) : tasks.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-500">
              No tasks yet. Create your first one.
            </p>
          ) : (
            <ul className="space-y-3">
              {tasks.map((task) => (
                <li
                  key={task.id}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-3"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="text-base font-semibold text-slate-800">{task.title}</p>
                      <p className="text-sm text-slate-600">{task.description}</p>
                      <p className="mt-1 text-xs text-slate-500">
                        Deadline: {new Date(task.deadline).toLocaleString()}
                      </p>
                      <p className="text-xs text-slate-500">
                        Assigned to: {task.assigned_employee_name || "Employee #" + task.assigned_employee_id}
                      </p>
                      <p className="text-xs text-slate-500">Status: {task.status}</p>
                      {task.not_completed_reason && (
                        <p className="text-xs text-rose-700">Reason: {task.not_completed_reason}</p>
                      )}
                      {task.is_overdue && (
                        <p className="mt-1 text-xs font-semibold text-rose-700">Overdue</p>
                      )}
                    </div>

                    <div className="flex flex-col gap-2">
                      {isEmployee && task.status !== "completed" && (
                        <>
                          <button
                            onClick={() => updateTaskStatus(task.id, "completed")}
                            className="rounded-lg bg-emerald-100 px-3 py-1.5 text-sm font-medium text-emerald-800"
                          >
                            Mark Completed
                          </button>
                          <input
                            type="text"
                            value={reasonByTaskId[task.id] || ""}
                            onChange={(event) =>
                              setReasonByTaskId((prev) => ({ ...prev, [task.id]: event.target.value }))
                            }
                            placeholder="Reason if not completed"
                            className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
                          />
                          <button
                            onClick={() => updateTaskStatus(task.id, "not_completed")}
                            className="rounded-lg bg-rose-100 px-3 py-1.5 text-sm font-medium text-rose-800"
                          >
                            Mark Not Completed
                          </button>
                        </>
                      )}

                      {isManager && (
                        <button
                          onClick={() => handleDeleteTask(task.id)}
                          className="rounded-lg bg-orange-100 px-3 py-1.5 text-sm font-medium text-orange-700"
                        >
                          Delete Task
                        </button>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}

export default App;
