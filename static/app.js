console.log("app.js loaded");

let socket;
let audioContext;
let mediaStream;
let source;
let processor;
let gainNode;

async function startRecording() {

    const log = document.getElementById("log");

    console.log("1. startRecording() called");

    socket = new WebSocket(
        `ws://${window.location.host}/ws/audio`
    );

    socket.onopen = async () => {

        console.log("2. WebSocket connected");

        log.innerText = "Status: Connected. Listening...";

        try {

            // Get microphone
            mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            console.log("3. Microphone permission granted");

            // Create AudioContext
            audioContext = new AudioContext();

            console.log(
                "4. Audio sample rate:",
                audioContext.sampleRate
            );

            // Microphone → AudioContext
            source = audioContext.createMediaStreamSource(
                mediaStream
            );

            // Process audio in chunks
            processor = audioContext.createScriptProcessor(
                4096,
                1,
                1
            );

            // Prevent microphone audio from playing through speakers
            gainNode = audioContext.createGain();
            gainNode.gain.value = 0;

            processor.onaudioprocess = (event) => {

                if (
                    !socket ||
                    socket.readyState !== WebSocket.OPEN
                ) {
                    return;
                }

                // Get microphone samples
                const inputData =
                    event.inputBuffer.getChannelData(0);

                // Float32 → Int16 PCM
                const pcmData = new Int16Array(
                    inputData.length
                );

                for (let i = 0; i < inputData.length; i++) {

                    let sample = inputData[i];

                    // Clamp between -1 and +1
                    sample = Math.max(
                        -1,
                        Math.min(1, sample)
                    );

                    // Convert Float32 → Int16
                    pcmData[i] =
                        sample < 0
                            ? sample * 32768
                            : sample * 32767;
                }

                // Send raw PCM bytes
                socket.send(pcmData.buffer);

                console.log(
                    "5. PCM chunk sent:",
                    pcmData.byteLength,
                    "bytes"
                );
            };

            // Connect audio pipeline
            source.connect(processor);
            processor.connect(gainNode);
            gainNode.connect(audioContext.destination);

            console.log("6. PCM recording started");

            log.innerText =
                "Status: Recording PCM audio...";

        } catch (error) {

            console.error(
                "Microphone error:",
                error
            );

            log.innerText =
                "Microphone error: " + error.message;
        }
    };
    socket.onmessage = async(event) => {
        console.log("🔊 AI audio received");

        const audioBlob = new Blob(
            [event.data],
            {
                type: "audio/mpeg"
            }
        );

        const audioUrl = URL.createObjectURL(
            audioBlob
        );

        const audio = new Audio(audioUrl);

        audio.onended = () => {
            console.log("🔊 AI finished speaking");
            URL.revokeObjectURL(audioUrl);
        };

        try {

            await audio.play();

            console.log("🔊 AI is speaking");

        } catch (error) {

            console.error(
                "Audio playback error:",
                error
            );
        }
    };




    socket.onerror = (error) => {

        console.error(
            "WebSocket error:",
            error
        );
    };


    socket.onclose = () => {

        console.log("WebSocket closed");

        log.innerText =
            "Status: Disconnected";
    };
}


function stopRecording() {

    console.log("STOP clicked");

    // Stop microphone
    if (mediaStream) {

        mediaStream.getTracks().forEach(
            track => track.stop()
        );

        mediaStream = null;
    }

    // Disconnect audio nodes
    if (source) {
        source.disconnect();
        source = null;
    }

    if (processor) {
        processor.disconnect();
        processor = null;
    }

    if (gainNode) {
        gainNode.disconnect();
        gainNode = null;
    }

    // Close AudioContext
    if (audioContext) {

        audioContext.close();
        audioContext = null;
    }

    console.log(
        "Microphone stopped. Waiting for AI response..."
    );

    // Close WebSocket
    // if (
    //     socket &&
    //     socket.readyState === WebSocket.OPEN
    // ) {
    //     socket.close();
    // }

    // console.log("Recording stopped");
}