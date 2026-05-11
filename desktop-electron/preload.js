const { contextBridge } = require("electron");

contextBridge.exposeInMainWorld("desktopInfo", {
  isElectron: true,
  platform: process.platform
});
