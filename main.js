const { app, BrowserWindow } = require('electron');
const path = require('path');

console.log('Main process starting...'); // Log tambahan

let mainWindow; // Pindahkan deklarasi ke sini

function createWindow () {
  console.log('createWindow function called'); // Log tambahan
  mainWindow = new BrowserWindow({ // Hapus 'const'
    width: 800,
    height: 600,
    webPreferences: {
      // preload: path.join(__dirname, 'preload.js') // Dikomentari untuk sementara
      nodeIntegration: true, // Diperlukan agar renderer.js bisa menggunakan require
      contextIsolation: false // Diperlukan untuk nodeIntegration true pada Electron versi baru
    }
  });
  console.log('BrowserWindow created'); // Log tambahan

  mainWindow.loadFile('index.html')
    .then(() => {
      console.log('index.html loaded successfully'); // Log tambahan
    })
    .catch(err => {
      console.error('Failed to load index.html:', err); // Log tambahan untuk error
    });
  
  mainWindow.on('closed', () => {
    console.log('MainWindow closed'); // Log tambahan
    mainWindow = null; // Penting untuk membersihkan referensi
  });

  // Open the DevTools.
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  console.log('App is ready'); // Log tambahan
  createWindow();

  app.on('activate', function () {
    console.log('App activate event'); // Log tambahan
    if (BrowserWindow.getAllWindows().length === 0) {
      console.log('No windows open, creating new one on activate'); // Log tambahan
      createWindow();
    }
  });
});

app.on('window-all-closed', function () {
  console.log('All windows closed'); // Log tambahan
  if (process.platform !== 'darwin') {
    console.log('Quitting app (not macOS)'); // Log tambahan
    app.quit();
  }
});

app.on('quit', () => {
  console.log('App quit event'); // Log tambahan
});

console.log('Main process script finished executing initial block'); // Log tambahan