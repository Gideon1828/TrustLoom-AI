const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("electronAPI", {
  isElectron: true,
  authCallbackPort: 5890,
  openExternal: (url) => ipcRenderer.send("open-external", url),
  log: (msg) => ipcRenderer.send("renderer-log", msg),
});
