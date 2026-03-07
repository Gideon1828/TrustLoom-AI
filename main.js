const { app, BrowserWindow, shell, ipcMain } = require("electron");
const path = require("path");
const http = require("http");
const url = require("url");

let mainWindow;
let authCallbackServer = null;
const AUTH_CALLBACK_PORT = 5890;

/**
 * Start a small local HTTP server to capture OAuth redirects.
 * Supabase redirects here with tokens in the URL hash/fragment.
 * We serve a tiny HTML page that reads the hash and posts it to the Electron app.
 */
function startAuthCallbackServer() {
  if (authCallbackServer) return;

  authCallbackServer = http.createServer((req, res) => {
    const parsed = url.parse(req.url, true);

    if (parsed.pathname === "/auth/callback") {
      // Serve an HTML page that extracts the hash fragment tokens
      // and sends them to the Electron app via window.postMessage
      res.writeHead(200, { "Content-Type": "text/html" });
      res.end(`<!DOCTYPE html>
<html><head><title>TrustLoom AI - Signing In</title>
<style>
  body{margin:0;display:flex;justify-content:center;align-items:center;height:100vh;
  font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0a0f1e;color:#e0e6ed;}
  .card{text-align:center;padding:40px 60px;border-radius:16px;background:rgba(255,255,255,0.05);
  box-shadow:0 8px 32px rgba(0,0,0,0.3);}
  h2{margin-bottom:8px;} p{opacity:0.7;margin-top:4px;}
  .spinner{width:40px;height:40px;border:4px solid rgba(255,255,255,0.1);
  border-top-color:#6366f1;border-radius:50%;animation:spin 0.8s linear infinite;margin:0 auto 20px;}
  @keyframes spin{to{transform:rotate(360deg)}}
  .checkmark{display:none;margin:0 auto 20px;width:48px;height:48px;border-radius:50%;
  background:#22c55e;position:relative;}
  .checkmark::after{content:'';position:absolute;left:16px;top:10px;width:12px;height:22px;
  border:solid #fff;border-width:0 3px 3px 0;transform:rotate(45deg);}
  .done .spinner{display:none;} .done .checkmark{display:block;}
  .done h2{color:#22c55e;} .close-msg{font-size:13px;opacity:0.5;margin-top:12px;}
  .error .spinner{display:none;} .error h2{color:#ef4444;}
</style></head><body>
<div class="card" id="card">
  <div class="spinner"></div>
  <div class="checkmark"></div>
  <h2 id="title">Signing you in...</h2>
  <p id="msg">Sending credentials to TrustLoom AI</p>
  <p class="close-msg" id="close-msg" style="display:none">This tab will close automatically...</p>
</div>
<script>
  const card = document.getElementById('card');
  const title = document.getElementById('title');
  const msg = document.getElementById('msg');
  const closeMsg = document.getElementById('close-msg');
  const hash = window.location.hash.substring(1);
  if (hash) {
    fetch('/auth/token-relay', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: hash
    }).then(() => {
      card.classList.add('done');
      title.textContent = 'Authentication Successful!';
      msg.textContent = 'You are now signed in. Returning to TrustLoom AI...';
      closeMsg.style.display = 'block';
      setTimeout(() => { window.close(); }, 2000);
      setTimeout(() => {
        closeMsg.textContent = 'You can close this tab now.';
      }, 2500);
    }).catch(() => {
      card.classList.add('error');
      title.textContent = 'Connection Error';
      msg.textContent = 'Could not reach TrustLoom AI. Please try again.';
    });
  } else {
    card.classList.add('error');
    title.textContent = 'Authentication Issue';
    msg.textContent = 'No tokens received. Please try again in the app.';
  }
</script>
</body></html>`);
    } else if (parsed.pathname === "/auth/token-relay" && req.method === "POST") {
      // Receive tokens posted by the HTML page above
      let body = "";
      req.on("data", (chunk) => { body += chunk; });
      req.on("end", () => {
        res.writeHead(200, {
          "Content-Type": "text/plain",
          "Access-Control-Allow-Origin": "*"
        });
        res.end("ok");

        // Parse the tokens and send to the Electron renderer
        const params = new URLSearchParams(body);
        const tokens = {
          access_token: params.get("access_token"),
          refresh_token: params.get("refresh_token"),
          expires_in: params.get("expires_in"),
          token_type: params.get("token_type"),
          provider_token: params.get("provider_token"),
        };

        console.log("[TrustLoom] OAuth tokens received, forwarding to app");
        console.log("[TrustLoom] Token details - access_token:", tokens.access_token ? "present" : "null",
          "refresh_token:", tokens.refresh_token ? "present" : "null");
        if (mainWindow && !mainWindow.isDestroyed()) {
          // Dispatch a custom event on the renderer window with the tokens
          const tokensJson = JSON.stringify(tokens);
          mainWindow.webContents.executeJavaScript(`
            (async function() {
              try {
                console.log('[Electron] Dispatching oauth callback event with tokens');
                console.log('[Electron] electronAPI available:', !!window.electronAPI);
                const event = new CustomEvent('electron-oauth-callback', { detail: ${tokensJson} });
                const dispatched = window.dispatchEvent(event);
                console.log('[Electron] Event dispatched result:', dispatched);
                console.log('[Electron] Listener count check - event type: electron-oauth-callback');
              } catch(e) {
                console.error('[Electron] Error dispatching event:', e.message);
              }
            })();
          `).then(result => {
            console.log("[TrustLoom] executeJavaScript completed");
          }).catch(err => {
            console.error("[TrustLoom] executeJavaScript FAILED:", err.message);
          });
          mainWindow.focus();
        }
      });
    } else {
      res.writeHead(404);
      res.end("Not found");
    }
  });

  authCallbackServer.listen(AUTH_CALLBACK_PORT, "127.0.0.1", () => {
    console.log(`[TrustLoom] Auth callback server on http://127.0.0.1:${AUTH_CALLBACK_PORT}`);
  });

  authCallbackServer.on("error", (err) => {
    console.error("[TrustLoom] Auth callback server error:", err.message);
    authCallbackServer = null;
  });
}

/**
 * Create the main Electron window and load the React UI
 */
function createWindow() {
  // In packaged app, preload.js is unpacked from asar to app.asar.unpacked/
  const preloadPath = app.isPackaged
    ? path.join(__dirname.replace('app.asar', 'app.asar.unpacked'), 'preload.js')
    : path.join(__dirname, 'preload.js');

  // Icon path: in dev it's under frontend/public, in packaged it's in extraResources
  const iconPath = app.isPackaged
    ? path.join(process.resourcesPath, 'frontend', 'logo.ico')
    : path.join(__dirname, 'frontend', 'public', 'logo.ico');

  console.log(`[TrustLoom] Preload path: ${preloadPath}`);
  console.log(`[TrustLoom] Icon path: ${iconPath}`);
  console.log(`[TrustLoom] app.isPackaged: ${app.isPackaged}`);

  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: "TrustLoom AI",
    icon: iconPath,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: preloadPath,
    },
    show: false,
  });

  mainWindow.setMenuBarVisibility(false);

  // Block ALL external navigations — the app runs from file://, so any http(s)
  // navigation must be opened in the system browser instead.
  function isExternalUrl(targetUrl) {
    return targetUrl.startsWith("http://") || targetUrl.startsWith("https://");
  }

  // Intercept window.open calls
  mainWindow.webContents.setWindowOpenHandler(({ url: targetUrl }) => {
    if (isExternalUrl(targetUrl)) {
      console.log("[TrustLoom] Blocked popup, opening in browser:", targetUrl.substring(0, 80));
      shell.openExternal(targetUrl);
      return { action: "deny" };
    }
    return { action: "allow" };
  });

  // Intercept window.location.href navigations
  mainWindow.webContents.on("will-navigate", (event, targetUrl) => {
    if (isExternalUrl(targetUrl)) {
      console.log("[TrustLoom] Blocked navigation, opening in browser:", targetUrl.substring(0, 80));
      event.preventDefault();
      shell.openExternal(targetUrl);
    }
  });

  // Intercept frame navigations (Electron 28+)
  mainWindow.webContents.on("will-frame-navigate", (details) => {
    if (details.isMainFrame && isExternalUrl(details.url)) {
      console.log("[TrustLoom] Blocked frame nav, opening in browser:", details.url.substring(0, 80));
      details.preventDefault();
      shell.openExternal(details.url);
    }
  });

  const isDev = !app.isPackaged;
  const indexPath = isDev
    ? path.join(__dirname, "frontend", "dist", "index.html")
    : path.join(process.resourcesPath, "frontend", "index.html");

  console.log(`[TrustLoom] Loading UI from: ${indexPath}`);
  mainWindow.loadFile(indexPath);

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  // IPC handler: open URL in system browser (called from preload)
  ipcMain.on("open-external", (event, url) => {
    console.log("[TrustLoom] IPC open-external:", url);
    shell.openExternal(url);
  });

  // IPC handler: log messages from renderer to main process terminal
  ipcMain.on("renderer-log", (event, msg) => {
    console.log("[Renderer]", msg);
  });

  startAuthCallbackServer();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on("window-all-closed", () => {
  if (authCallbackServer) {
    authCallbackServer.close();
    authCallbackServer = null;
  }
  app.quit();
});
