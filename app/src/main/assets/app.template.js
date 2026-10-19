
(() => {
  "use strict";

  const API_URL = "https://script.google.com/macros/s/AKfycbwZ3D3NWv31w9xIaEQsqgpVlvfQuE-p2TgkF1fKuFajS9M2NelnaRCblg-cldbHLHFb/exec";
  const API_TOKEN = "__API_TOKEN__";

  const fields = [
    ["taskName", "Task Name", "text", true],
    ["type", "Type", "text"],
    ["progress", "Progress", "select", false, ["Not Started", "In Progress", "On Hold", "Completed"]],
    ["priority", "Priority", "select", false, ["Low", "Medium", "High", "Urgent"]],
    ["deadline", "Deadline", "date"],
    ["vendorCraftsman", "Vendor / Craftsman", "text"],
    ["contactNumber", "Contact Number", "tel"],
    ["estimatedCost", "Estimated Cost (INR)", "number"],
    ["actualCost", "Actual Cost (INR)", "number"],
    ["nextFollowUp", "Next Follow-up", "date"],
    ["deliveryDate", "Delivery Date", "date"],
    ["paymentStatus", "Payment Status", "select", false, ["None", "Pending", "Partially Paid", "Paid"]],
    ["link", "Link", "url"],
    ["taskFocus", "Task Focus", "text"],
    ["valueAdd", "Value Add", "text"],
    ["notes", "Notes", "textarea"],
    ["taskAdded", "Task Added", "date"],
    ["taskStarted", "Task Started", "date"],
    ["taskCompleted", "Task Completed", "date"],
    ["lastUpdated", "Last Updated", "date"]
  ];

  let tasks = [];
  let view = "active";
  let editingId = null;
  let busy = false;
  let toastTimer;
  let sequence = 0;

  const $ = id => document.getElementById(id);
  const safe = value => String(value ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[c]);

  function toast(message) {
    $("toast").textContent = message;
    $("toast").classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => $("toast").classList.remove("show"), 2600);
  }

  function setStatus(message) {
    $("connectionStatus").textContent = message;
  }

  function newId() {
    return "task-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8);
  }

  function isCompleted(task) {
    return String(task.status || "").toLowerCase() === "completed" ||
      String(task.progress || "").toLowerCase() === "completed";
  }

  function normalize(task) {
    const t = { ...task };
    t.id = String(t.id || t.ID || newId());
    t.taskName = t.taskName || t.title || t["Task Name"] || "";
    t.type = t.type || t["Type"] || "";
    t.progress = t.progress || t.status || "Not Started";
    t.priority = t.priority || "Medium";
    t.deadline = t.deadline || t.dueDate || "";
    t.vendorCraftsman = t.vendorCraftsman || "";
    t.contactNumber = t.contactNumber || "";
    t.estimatedCost = t.estimatedCost ?? "";
    t.actualCost = t.actualCost ?? "";
    t.nextFollowUp = t.nextFollowUp || "";
    t.deliveryDate = t.deliveryDate || "";
    t.paymentStatus = t.paymentStatus || "";
    t.link = t.link || "";
    t.taskFocus = t.taskFocus || "";
    t.valueAdd = t.valueAdd || "";
    t.notes = t.notes || t.description || "";
    t.taskAdded = t.taskAdded || t.createdAt || "";
    t.taskStarted = t.taskStarted || "";
    t.taskCompleted = t.taskCompleted || t.completedAt || "";
    t.lastUpdated = t.lastUpdated || t.updatedAt || "";
    t.status = isCompleted(t) ? "completed" : (t.progress || "Not Started");
    return t;
  }

  function nativeRequest(payload) {
    return new Promise((resolve, reject) => {
      if (!window.AndroidBridge || typeof AndroidBridge.nativeHttp !== "function") {
        reject(new Error("Android network bridge is unavailable."));
        return;
      }

      const callbackId = "req_" + (++sequence) + "_" + Date.now();
      let timer = setTimeout(() => {
        delete window.__requests[callbackId];
        reject(new Error("Request timed out. Please try again."));
      }, 35000);

      window.__requests[callbackId] = (success, base64) => {
        clearTimeout(timer);
        delete window.__requests[callbackId];
        try {
          const binary = atob(base64 || "");
          const bytes = Uint8Array.from(binary, c => c.charCodeAt(0));
          const text = new TextDecoder("utf-8").decode(bytes);
          if (!success) {
            reject(new Error("Server request failed: " + text.slice(0, 180)));
            return;
          }
          const result = JSON.parse(text);
          if (result.success === false || result.ok === false) {
            reject(new Error(result.error || result.message || "Server rejected the request."));
            return;
          }
          resolve(result);
        } catch (err) {
          reject(new Error("Could not read server response: " + err.message));
        }
      };

      try {
        AndroidBridge.nativeHttp(API_URL, "POST", JSON.stringify(payload), callbackId);
      } catch (err) {
        clearTimeout(timer);
        delete window.__requests[callbackId];
        reject(err);
      }
    });
  }

  window.__requests = window.__requests || {};
  window.onNativeHttpResponse = (id, success, base64) => {
    const callback = window.__requests[id];
    if (callback) callback(success, base64);
  };

  function buildForm() {
    const host = $("fields");
    host.innerHTML = "";

    fields.forEach(([key, label, type, required, options]) => {
      const wrap = document.createElement("div");
      wrap.className = "field" + (type === "textarea" ? " wide" : "");
      const lab = document.createElement("label");
      lab.htmlFor = "f_" + key;
      lab.textContent = label;
      wrap.appendChild(lab);

      let input;
      if (type === "select") {
        input = document.createElement("select");
        options.forEach(option => {
          const opt = document.createElement("option");
          opt.value = option;
          opt.textContent = option;
          input.appendChild(opt);
        });
      } else if (type === "textarea") {
        input = document.createElement("textarea");
      } else {
        input = document.createElement("input");
        input.type = type;
        if (type === "number") input.min = "0";
      }
      input.id = "f_" + key;
      input.name = key;
      if (required) input.required = true;
      wrap.appendChild(input);
      host.appendChild(wrap);
    });
  }

  function openEditor(task) {
    editingId = task ? task.id : null;
    $("formTitle").textContent = task ? "Edit task" : "New task";
    $("saveBtn").textContent = task ? "Save changes" : "Save task";
    $("editor").classList.remove("hidden");
    const current = task || {};
    fields.forEach(([key]) => {
      const input = $("f_" + key);
      input.value = current[key] ?? "";
    });
    if (!task) {
      $("f_taskAdded").value = new Date().toISOString().slice(0, 10);
      $("f_lastUpdated").value = new Date().toISOString().slice(0, 10);
      $("f_progress").value = "Not Started";
      $("f_priority").value = "Medium";
      $("f_paymentStatus").value = "None";
    }
    $("editor").scrollIntoView({ behavior: "smooth", block: "start" });
    $("f_taskName").focus();
  }

  function closeEditor() {
    $("editor").classList.add("hidden");
    $("taskForm").reset();
    editingId = null;
  }

  function readForm() {
    const task = {};
    fields.forEach(([key]) => {
      task[key] = $("f_" + key).value.trim();
    });
    const old = tasks.find(t => t.id === editingId);
    task.id = editingId || newId();
    task.status = task.progress === "Completed" ? "completed" : task.progress;
    task.taskAdded = task.taskAdded || (old && old.taskAdded) || new Date().toISOString().slice(0, 10);
    task.lastUpdated = new Date().toISOString().slice(0, 10);

    if (task.status === "completed") {
      task.progress = "Completed";
      task.taskCompleted = task.taskCompleted || new Date().toISOString().slice(0, 10);
    } else {
      task.taskCompleted = "";
    }
    return task;
  }

  async function sendBatch(upserts, deletes) {
    if (busy) throw new Error("Please wait for the current sync to finish.");
    busy = true;
    $("syncBtn").disabled = true;
    $("saveBtn").disabled = true;

    try {
      const result = await nativeRequest({
        action: "batchSync",
        token: API_TOKEN,
        upserts: upserts || [],
        deletes: deletes || []
      });
      if (Array.isArray(result.tasks)) {
        tasks = result.tasks.map(normalize);
      } else {
        await loadTasks();
      }
      render();
      setStatus("Connected Â· Synced with Google Sheets");
      return result;
    } finally {
      busy = false;
      $("syncBtn").disabled = false;
      $("saveBtn").disabled = false;
    }
  }

  async function loadTasks() {
    setStatus("Syncing with Google Sheetsâ€¦");
    const result = await nativeRequest({ action: "getTasks", token: API_TOKEN });
    tasks = (result.tasks || []).map(normalize);
    render();
    setStatus("Connected Â· Synced with Google Sheets");
  }

  async function sync() {
    if (API_TOKEN === "PASTE_YOUR_NEW_SECRET_TOKEN_HERE" || !API_TOKEN) {
      setStatus("Add your API token in app.js to connect.");
      toast("Add your API token in app.js first.");
      return;
    }
    try {
      await loadTasks();
      toast("Google Sheets synced");
    } catch (err) {
      setStatus("Sync failed Â· " + err.message);
      toast(err.message);
    }
  }

  function render() {
    const completed = tasks.filter(isCompleted);
    const active = tasks.filter(t => !isCompleted(t));
    $("activeCount").textContent = active.length;
    $("doneCount").textContent = completed.length;
    $("summaryTitle").textContent = active.length ? "One step at a time." : "Stay on track.";
    $("listTitle").textContent = view === "active" ? "Your tasks" : "Completed tasks";

    const list = view === "active" ? active : completed;
    $("taskCount").textContent = list.length + (list.length === 1 ? " task" : " tasks");
    $("taskList").innerHTML = "";
    $("emptyState").classList.toggle("hidden", list.length !== 0);

    list.forEach(task => {
      const card = document.createElement("article");
      card.className = "task-card";
      const priority = String(task.priority || "Medium");
      const meta = [
        task.type,
        task.deadline ? "Deadline: " + task.deadline : "",
        task.vendorCraftsman ? "Vendor: " + task.vendorCraftsman : "",
        task.estimatedCost !== "" ? "Estimated: â‚¹" + task.estimatedCost : "",
        task.paymentStatus ? "Payment: " + task.paymentStatus : ""
      ].filter(Boolean).join(" Â· ");

      card.innerHTML = `
        <div class="task-top">
          <div>
            <p class="task-name">${safe(task.taskName || "Untitled task")}</p>
            <div class="task-meta">${safe(meta || "No additional details")}</div>
          </div>
          <span class="pill ${isCompleted(task) ? "completed" : priority.toLowerCase() === "high" || priority.toLowerCase() === "urgent" ? "high" : ""}">${safe(isCompleted(task) ? "Completed" : priority)}</span>
        </div>
        ${task.notes ? `<p class="task-meta">${safe(task.notes)}</p>` : ""}
        <div class="task-actions">
          ${!isCompleted(task) ? '<button class="complete" data-action="complete">âœ“ Complete</button>' : '<button data-action="reopen">â†¶ Reopen</button>'}
          <button data-action="edit">Edit</button>
          <button class="delete" data-action="delete">Delete</button>
        </div>`;

      card.querySelectorAll("button").forEach(button => {
        button.addEventListener("click", () => handleTaskAction(button.dataset.action, task));
      });
      $("taskList").appendChild(card);
    });
  }

  async function handleTaskAction(action, task) {
    if (action === "edit") {
      openEditor(task);
      return;
    }
    if (action === "delete") {
      if (!confirm("Delete this task from the app and Google Sheets?")) return;
      try {
        toast("Deleting taskâ€¦");
        await sendBatch([], [task.id]);
        toast("Task deleted");
      } catch (err) {
        toast(err.message);
      }
      return;
    }
    const updated = { ...task, lastUpdated: new Date().toISOString().slice(0, 10) };
    if (action === "complete") {
      updated.status = "completed";
      updated.progress = "Completed";
      updated.taskCompleted = new Date().toISOString().slice(0, 10);
    } else if (action === "reopen") {
      updated.status = "In Progress";
      updated.progress = "In Progress";
      updated.taskCompleted = "";
    }
    try {
      await sendBatch([updated], []);
      toast(action === "complete" ? "Task completed" : "Task reopened");
    } catch (err) {
      toast(err.message);
    }
  }

  $("taskForm").addEventListener("submit", async event => {
    event.preventDefault();
    if (!$("taskForm").reportValidity()) return;
    const task = readForm();
    try {
      await sendBatch([task], []);
      closeEditor();
      toast("Task saved to Google Sheets");
    } catch (err) {
      toast(err.message);
    }
  });

  $("addBtn").addEventListener("click", () => openEditor(null));
  $("cancelBtn").addEventListener("click", closeEditor);
  $("cancelBtn2").addEventListener("click", closeEditor);
  $("syncBtn").addEventListener("click", sync);

  document.querySelectorAll(".tab").forEach(button => {
    button.addEventListener("click", () => {
      view = button.dataset.view;
      document.querySelectorAll(".tab").forEach(b => b.classList.toggle("active", b === button));
      render();
    });
  });

  buildForm();
  render();
  sync();
})();

