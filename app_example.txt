console.log("app.js loaded");

let socket = null;

let audioContext = null;
let mediaStream = null;
let source = null;
let processor = null;
let gainNode = null;

let currentAudio = null;
let currentAudioUrl = null;


// ==========================================
// START RECORDING
// ==========================================

async function startRecording() {

    const log = document.getElementById("log");

    console.log("1. startRecording() called");

    socket = new WebSocket(
        `ws://${window.location.host}/ws/audio`
    );

    socket.binaryType = "arraybuffer";


    // ======================================
    // WEBSOCKET CONNECTED
    // ======================================

    socket.onopen = async () => {

        console.log("2. WebSocket connected");

        log.innerText =
            "Status: Connected. Listening...";

        try {

            // -------------------------------
            // Microphone
            // -------------------------------

            mediaStream =
                await navigator.mediaDevices
                    .getUserMedia({
                        audio: true
                    });

            console.log(
                "3. Microphone permission granted"
            );


            // -------------------------------
            // Audio Context
            // -------------------------------

            audioContext =
                new AudioContext();

            console.log(
                "4. Audio sample rate:",
                audioContext.sampleRate
            );


            // -------------------------------
            // Microphone source
            // -------------------------------

            source =
                audioContext
                    .createMediaStreamSource(
                        mediaStream
                    );


            // -------------------------------
            // Audio processor
            // -------------------------------

            processor =
                audioContext.createScriptProcessor(
                    4096,
                    1,
                    1
                );


            // -------------------------------
            // Prevent microphone playback
            // -------------------------------

            gainNode =
                audioContext.createGain();

            gainNode.gain.value = 0;


            // =================================
            // AUDIO PROCESSING
            // =================================

            processor.onaudioprocess =
                (event) => {

                    if (
                        !socket ||
                        socket.readyState !==
                            WebSocket.OPEN
                    ) {

                        return;
                    }


                    const inputData =
                        event.inputBuffer
                            .getChannelData(0);


                    const pcmData =
                        new Int16Array(
                            inputData.length
                        );


                    for (
                        let i = 0;
                        i < inputData.length;
                        i++
                    ) {

                        let sample =
                            inputData[i];

                        sample =
                            Math.max(
                                -1,
                                Math.min(
                                    1,
                                    sample
                                )
                            );


                        pcmData[i] =
                            sample < 0
                                ? sample * 32768
                                : sample * 32767;
                    }


                    // Send PCM to server
                    socket.send(
                        pcmData.buffer
                    );
                };


            // Connect audio graph

            source.connect(
                processor
            );

            processor.connect(
                gainNode
            );

            gainNode.connect(
                audioContext.destination
            );


            console.log(
                "6. PCM recording started"
            );

            log.innerText =
                "Status: Listening...";

        } catch (error) {

            console.error(
                "Microphone error:",
                error
            );

            log.innerText =
                "Microphone error: "
                + error.message;
        }
    };


    // ==========================================
    // SERVER MESSAGE
    // ==========================================

    socket.onmessage = async (event) => {

        // --------------------------------------
        // JSON control message
        // --------------------------------------

        if (
            typeof event.data === "string"
        ) {

            let message;

            try {

                message =
                    JSON.parse(
                        event.data
                    );

            } catch (error) {

                console.error(
                    "Invalid JSON:",
                    error
                );

                return;
            }


            // ==============================
            // INTERRUPT
            // ==============================

            if (
                message.type ===
                "interrupt"
            ) {

                console.log(
                    "⚡ AI interrupted"
                );

                stopCurrentAudio();

                return;
            }


            // ==============================
            // AUDIO START
            // ==============================

            if (
                message.type ===
                "audio_start"
            ) {

                console.log(
                    "🔊 AI audio starting"
                );

                return;
            }

            return;
        }


        // --------------------------------------
        // Binary audio
        // --------------------------------------

        console.log(
            "🔊 AI audio received"
        );


        const audioBlob =
            new Blob(
                [event.data],
                {
                    type: "audio/mpeg"
                }
            );


        currentAudioUrl =
            URL.createObjectURL(
                audioBlob
            );


        currentAudio =
            new Audio(
                currentAudioUrl
            );


        currentAudio.onended = () => {

            console.log(
                "🔊 AI finished speaking"
            );


            cleanupCurrentAudio();


            // Tell server that
            // playback has finished.

            if (
                socket &&
                socket.readyState ===
                    WebSocket.OPEN
            ) {

                socket.send(
                    JSON.stringify({
                        type:
                            "playback_finished"
                    })
                );
            }
        };


        currentAudio.onerror = (
            error
        ) => {

            console.error(
                "Audio playback error:",
                error
            );

            cleanupCurrentAudio();
        };


        try {

            await currentAudio.play();

            console.log(
                "🔊 AI is speaking"
            );

        } catch (error) {

            console.error(
                "Audio playback error:",
                error
            );
        }
    };


    // ==========================================
    // WEBSOCKET ERROR
    // ==========================================

    socket.onerror = (error) => {

        console.error(
            "WebSocket error:",
            error
        );
    };


    // ==========================================
    // WEBSOCKET CLOSED
    // ==========================================

    socket.onclose = () => {

        console.log(
            "WebSocket closed"
        );

        log.innerText =
            "Status: Disconnected";
    };
}


// ==========================================
// STOP CURRENT AI AUDIO
// ==========================================

function stopCurrentAudio() {

    if (currentAudio) {

        console.log(
            "🛑 Stopping AI audio"
        );

        currentAudio.pause();

        currentAudio.currentTime = 0;
    }

    cleanupCurrentAudio();
}


// ==========================================
// CLEAN AUDIO
// ==========================================

function cleanupCurrentAudio() {

    if (currentAudioUrl) {

        URL.revokeObjectURL(
            currentAudioUrl
        );

        currentAudioUrl = null;
    }

    currentAudio = null;
}


// ==========================================
// STOP RECORDING
// ==========================================

function stopRecording() {

    console.log(
        "STOP clicked"
    );


    // Stop AI audio

    stopCurrentAudio();


    // Stop microphone

    if (mediaStream) {

        mediaStream
            .getTracks()
            .forEach(
                track => track.stop()
            );

        mediaStream = null;
    }


    // Disconnect source

    if (source) {

        source.disconnect();

        source = null;
    }


    // Disconnect processor

    if (processor) {

        processor.disconnect();

        processor = null;
    }


    // Disconnect gain

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
        "Microphone stopped"
    );
}