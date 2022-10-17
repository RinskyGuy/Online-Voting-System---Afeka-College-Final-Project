const DETECTION_MODEL_URL = '../static/models/face-api/weights/'

let preloading_msg = document.getElementById('loading')
let content = document.getElementById('content')

const modal = document.getElementById('errmodal')
const video = document.getElementById("video"); // video is the id of video tag


async function onLoad(){
    await faceapi.nets.tinyFaceDetector.loadFromUri(DETECTION_MODEL_URL)
    await faceapi.nets.faceLandmark68Net.loadFromUri(DETECTION_MODEL_URL)
    await faceapi.nets.faceRecognitionNet.loadFromUri(DETECTION_MODEL_URL)
    startVideo()

    preloading_msg.hidden = true
    content.hidden = false

    video.addEventListener('play', () => {
        setInterval(async () => {
            const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions({ minConfidence: 0.3 })).withFaceLandmarks().withFaceDescriptors()
            if (detections.length>1) {
                modal.style.display = "block";
            }    
            else {
                modal.style.display = "none";
            }
            
        }, 50) 
    })  
}

function startVideo() {
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    .then(function(stream) {
        video.srcObject = stream;
        })
    .catch(function(err) {
        console.log("An error occurred! " + err);
    });
}

function stopVideo() {
    const stream = video.srcObject;
    const tracks = stream.getTracks();

    tracks.forEach(function(track) {
        track.stop();
    });

    video.srcObject = null;
}