let socket;
let mediaRecorder;

async function startRecording(){
    const log = document.getElementById('log');
    socket = new WebSocket(`ws://${window.location.host}/ws/audio`);

    socket.onopen = async () => {
        log.innerText = "Status : Connected. Listening....";
        const stream = await navigator.mediaDevices.getUserMedia({audio:true});
        mediaRecorder = new MediaRecorder(stream , {mimeType:'audio/webm'});

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0 && socket.readyState === WebSocket.OPEN){
                socket.send(event.data);
            }
        };
        mediaRecorder.start(100);
    };
    socket.onmessage = (event) => {
        console.log("Server response:", event(data));
    };

    socket.onclose = () => {
        log.innerText = "status: Disconnected"
    };
}

function stopRecording() {
    if (mediaRecorder) mediaRecorder.stop();
    if (socket) socket.close();
}
