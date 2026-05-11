const { app, BrowserWindow, dialog } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");
const waitOn = require("wait-on");

let mainWindow = null;
let backendProcess = null;
let isQuitting = false;

const APP_PORT = process.env.APP_PORT || "5000";
const BASE_URL = `http://127.0.0.1:${APP_PORT}`;
const START_PAGE = `${BASE_URL}/booking.html`;
const HEALTH_URL = `${BASE_URL}/healthz`;

function getBackendRoot() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "app-src");
  }
  return path.resolve(__dirname, "..");
}

function getPythonCommand() {
  const embeddedWin = path.join(process.resourcesPath, "python-runtime", "Scripts", "python.exe");
  const embeddedUnix = path.join(process.resourcesPath, "python-runtime", "bin", "python3");
  const devRuntimeWin = path.join(__dirname, "runtime", "python", "Scripts", "python.exe");
  const devRuntimeUnix = path.join(__dirname, "runtime", "python", "bin", "python3");

  if (app.isPackaged) {
    if (process.platform === "win32" && fs.existsSync(embeddedWin)) return embeddedWin;
    if (process.platform !== "win32" && fs.existsSync(embeddedUnix)) return embeddedUnix;
  } else {
    if (process.platform === "win32" && fs.existsSync(devRuntimeWin)) return devRuntimeWin;
    if (process.platform !== "win32" && fs.existsSync(devRuntimeUnix)) return devRuntimeUnix;
  }

  if (process.platform === "win32") {
    return process.env.PYTHON_CMD || "python";
  }
  return process.env.PYTHON_CMD || "python3";
}

function startBackend() {
  const backendRoot = getBackendRoot();
  const pythonCmd = getPythonCommand();
  const scriptPath = path.join(backendRoot, "run_waitress.py");

  const env = {
    ...process.env,
    PORT: APP_PORT,
    FLASK_ENV: "production",
    USE_HTTPS: "0"
  };

  backendProcess = spawn(pythonCmd, [scriptPath], {
    cwd: backendRoot,
    env,
    windowsHide: true,
    stdio: "ignore"
  });

  backendProcess.on("error", (err) => {
    dialog.showErrorBox(
      "Không thể khởi động backend Python",
      `Lỗi: ${err.message}\n\nHãy chạy lại build runtime hoặc kiểm tra Python runtime kèm app.`
    );
  });
}

async function waitForBackend() {
  await waitOn({
    resources: [HEALTH_URL],
    timeout: 45000,
    interval: 500,
    tcpTimeout: 10000,
    validateStatus: (status) => status >= 200 && status < 500
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  await mainWindow.loadURL(START_PAGE);
  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function stopBackend() {
  if (!backendProcess || backendProcess.killed) return;
  try {
    backendProcess.kill();
  } catch (_) {
    // no-op
  }
}

app.on("before-quit", () => {
  isQuitting = true;
  stopBackend();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", async () => {
  if (mainWindow === null && !isQuitting) {
    await createWindow();
  }
});

app.whenReady().then(async () => {
  try {
    startBackend();
    await waitForBackend();
    await createWindow();
  } catch (err) {
    dialog.showErrorBox(
      "Khởi động ứng dụng thất bại",
      `Không kết nối được backend tại ${HEALTH_URL}.\n\nChi tiết: ${err.message}`
    );
    app.quit();
  }
});
