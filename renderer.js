console.log('Renderer process loaded');

const timerDisplay = document.getElementById('timer-display');
const startBtn = document.getElementById('start-btn');
const pauseBtn = document.getElementById('pause-btn');
const resetBtn = document.getElementById('reset-btn');
const statusDisplay = document.getElementById('status');
const cycleCountDisplay = document.getElementById('cycle-count');

// Durasi dalam detik
const POMODORO_DURATION = 25 * 60; // 25 menit
const SHORT_BREAK_DURATION = 5 * 60; // 5 menit
const LONG_BREAK_DURATION = 15 * 60; // 15 menit
const CYCLES_BEFORE_LONG_BREAK = 4;

let currentTimer = null; // Menyimpan interval ID
let timeLeft = POMODORO_DURATION;
let currentCycle = 0;
let isPaused = true;
let currentState = 'Pomodoro'; // Bisa 'Pomodoro', 'Short Break', 'Long Break'

function updateDisplay() {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    statusDisplay.textContent = currentState;
    cycleCountDisplay.textContent = currentCycle;
    document.title = `${timerDisplay.textContent} - ${currentState}`; // Update judul window
}

function playNotificationSound() {
    // Implementasi notifikasi suara (akan ditambahkan nanti)
    // Untuk sekarang, kita bisa menggunakan alert atau console.log
    console.log('Timer ended! Time for a break or work.');
    const audio = new Audio('./assets/notification.wav'); // Path relatif ke aset dari index.html
    audio.play().catch(error => console.error("Error playing sound:", error));
}

function switchState() {
    if (currentState === 'Pomodoro') {
        currentCycle++;
        if (currentCycle % CYCLES_BEFORE_LONG_BREAK === 0) {
            currentState = 'Long Break';
            timeLeft = LONG_BREAK_DURATION;
        } else {
            currentState = 'Short Break';
            timeLeft = SHORT_BREAK_DURATION;
        }
    } else { // Jika sedang break (Short atau Long)
        currentState = 'Pomodoro';
        timeLeft = POMODORO_DURATION;
    }
    playNotificationSound();
    updateDisplay();
    // Otomatis mulai timer berikutnya atau biarkan user yang memulai?
    // Untuk sekarang, kita biarkan user yang memulai.
    isPaused = true; 
    clearInterval(currentTimer);
}

function startTimer() {
    if (isPaused) {
        isPaused = false;
        startBtn.textContent = 'Start'; // Atau sembunyikan tombol start, tampilkan pause
        currentTimer = setInterval(() => {
            if (timeLeft > 0) {
                timeLeft--;
                updateDisplay();
            } else {
                clearInterval(currentTimer);
                switchState();
            }
        }, 1000);
    }
}

function pauseTimer() {
    isPaused = true;
    clearInterval(currentTimer);
    startBtn.textContent = 'Resume'; // Atau ganti teks tombol start
}

function resetTimer() {
    clearInterval(currentTimer);
    isPaused = true;
    // Reset ke state saat ini atau selalu ke Pomodoro?
    // Untuk sekarang, reset ke durasi awal state saat ini.
    if (currentState === 'Pomodoro') {
        timeLeft = POMODORO_DURATION;
    } else if (currentState === 'Short Break') {
        timeLeft = SHORT_BREAK_DURATION;
    } else if (currentState === 'Long Break') {
        timeLeft = LONG_BREAK_DURATION;
    }
    // Jika ingin selalu reset ke Pomodoro awal:
    // currentState = 'Pomodoro';
    // timeLeft = POMODORO_DURATION;
    // currentCycle = 0; // Reset siklus juga jika kembali ke Pomodoro awal
    startBtn.textContent = 'Start';
    updateDisplay();
}

startBtn.addEventListener('click', () => {
    if (isPaused) {
        startTimer();
    } 
    // Jika ingin tombol start juga berfungsi sebagai pause saat timer berjalan:
    // else {
    //     pauseTimer();
    // }
});

pauseBtn.addEventListener('click', pauseTimer);
resetBtn.addEventListener('click', resetTimer);

// Inisialisasi tampilan awal
updateDisplay();
