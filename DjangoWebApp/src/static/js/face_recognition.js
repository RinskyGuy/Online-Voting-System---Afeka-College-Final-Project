const THRESHOLD = 0.53 // can see threshold decision in face_rec_threshold.html file

let preloading_msg = document.getElementById('preloading')
let postloading_msg = document.getElementById('postloading')

let detection_err = document.getElementById('detection_err')
let access_err = document.getElementById('access_err')

const modal = document.getElementById('suceedmodal')

const DETECTION_MODEL_URL = '../static/models/face-api/weights/'
const RECOGNITION_MODEL_URL = '../static/models/tfjs_vgg/model.json'
const MODEL_URL = '../static/models/tfjs/model.json'

const video = document.getElementById("video"); // video is the id of video tag
const cropped = document.getElementById("cropped"); // canvas is the id of canvas tag

let isPlaying = false;

async function onLoad(faceVectors){

    const recognitionModel =  await tf.loadLayersModel(RECOGNITION_MODEL_URL)
    const modelc =  await tf.loadLayersModel(MODEL_URL)

    await faceapi.nets.tinyFaceDetector.loadFromUri(DETECTION_MODEL_URL)
    await faceapi.nets.faceLandmark68Net.loadFromUri(DETECTION_MODEL_URL)
    await faceapi.nets.faceRecognitionNet.loadFromUri(DETECTION_MODEL_URL)
    startVideo()
    preloading_msg.hidden = true
    postloading_msg.hidden = false
    
    video.addEventListener('play', () => {
        setInterval(async () => {
            const detections = await faceapi.detectAllFaces(video, new faceapi.TinyFaceDetectorOptions({ minConfidence: 0.3 })).withFaceLandmarks().withFaceDescriptors()
          

            if (detections.length>1) {
                detection_err.hidden = false
            }    
            else {
                detection_err.hidden = true
            }
        
            if (detections.length==1) {
                faceImage = getFaceImage(detections[0])
                vector = recognitionModel.predict(faceImage)
                minDist = getMinDist(vector, faceVectors)
                console.log(minDist)
                if (minDist<=THRESHOLD) {
                    modal.style.display = "block";
                }
                video.pause();
            }
            
        }, 50) 
    })  
}

function startVideo() {
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    .then(function(stream) {
        video.srcObject = stream;
        access_err.hidden = true;
        })
    .catch(function(err) {
        console.log("An error occurred! " + err);
        access_err.hidden = false;
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

function getFaceImage(detection) {
    // crop face from video frame
    cropped.getContext('2d').clearRect(0, 0, cropped.width, cropped.height)
    cropped.getContext('2d').drawImage(video, 
        detection.alignedRect._box._x, 
        detection.alignedRect._box._y, 
        detection.alignedRect._box._width, 
        detection.alignedRect._box._height, 
        0, 
        0, 
        cropped.width, 
        cropped.height)

    // get tensor from face image
    var imageData = cropped.getContext('2d').getImageData(0, 0, cropped.width, cropped.height)
    var tfImage = tf.browser.fromPixels(imageData, 3).toFloat().expandDims(0)
    return tfImage
}

function euclideanDist(vector1, vector2) {
    return vector1.map((x, i) => Math.abs( x - vector2[i] ) ** 2) // square the difference
    .reduce((sum, now) => sum + now) // sum
    ** (1/2)
}

function cosineSimilarity(vector1, vector2) {
    a = 0
    b = 0
    c = 0

    for(i = 0; i < vector1.length; i++) {
        a += vector1[i]*vector2[i]
        b += vector1[i]*vector1[i]
        c += vector2[i]*vector2[i]
    }

    return a/(Math.sqrt(b)*Math.sqrt(c))
}

function getMinDist(vector, faceVectors) {
    var minDist = -1
    var dist

    for (var docType in faceVectors){
        dist = cosineSimilarity(vector.dataSync(), faceVectors[docType])
        if (minDist==-1 || dist<minDist) {
            minDist = dist
        }
    }

    return minDist
}