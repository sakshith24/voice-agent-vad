let socket;
let mediaRecorder;

async function startRecording(){
    const log = document.getElementById('log');
    socket = new WebSocket(`ws://${window.location.host}ws/audio`);
}