import {
  DrawingUtils,
  FilesetResolver,
  GestureRecognizer,
} from "./node_modules/@mediapipe/tasks-vision/vision_bundle.mjs";

const MODEL_ASSET_PATH =
  "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task";

const videoElement = document.querySelector(".input_video");
const stageElement = document.querySelector(".video-stage");
const canvasElement = document.querySelector(".output_canvas");
const canvasCtx = canvasElement.getContext("2d");
const drawingUtils = new DrawingUtils(canvasCtx);

const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");
const fileButton = document.getElementById("fileButton");
const fileInput = document.getElementById("fileInput");
const statusText = document.getElementById("statusText");

const controls = {
  gestureDetection: document.getElementById("gestureDetection"),
  maxHands: document.getElementById("maxHands"),
  minDetectionConfidence: document.getElementById("minDetectionConfidence"),
  minTrackingConfidence: document.getElementById("minTrackingConfidence"),
};

const controlValues = {
  gestureResult: document.getElementById("gestureResultValue"),
  gestureResults: document.getElementById("gestureResults"),
  maxHands: document.getElementById("maxHandsValue"),
  minDetectionConfidence: document.getElementById("minDetectionConfidenceValue"),
  minTrackingConfidence: document.getElementById("minTrackingConfidenceValue"),
};

const CANONICAL_GESTURE_ORDER = [
  "Open_Palm",
  "Closed_Fist",
  "Thumb_Up",
  "Thumb_Down",
  "Pointing_Up",
  "Victory",
  "ILoveYou",
  "None",
];

const GESTURE_LABELS = {
  Open_Palm: "Open palm",
  Closed_Fist: "Closed fist",
  Thumb_Up: "Thumbs up",
  Thumb_Down: "Thumbs down",
  Pointing_Up: "Pointing up",
  Victory: "Victory",
  ILoveYou: "I love you",
  None: "None",
};

let gestureRecognizer;
let camera;
let currentSource;
let isRunning = false;
let lastVideoTime = -1;

function toNumber(value) {
  return Number.parseFloat(value);
}

function updateStatus(state, message) {
  statusText.dataset.state = state;
  statusText.textContent = message;
}

function syncStageAspectRatio(width, height) {
  const aspectRatio = `${width} / ${height}`;
  stageElement.style.aspectRatio = aspectRatio;
  canvasElement.style.aspectRatio = aspectRatio;
}

function formatGestureLabel(label) {
  return GESTURE_LABELS[label] ?? label.replaceAll("_", " ");
}

function renderGestureResults(message, handResults = []) {
  if (message) {
    controlValues.gestureResults.innerHTML = `<div class="gesture-empty">${message}</div>`;
    return;
  }

  const markup = handResults
    .map(({ handednessLabel, topGestureLabel, categories }, index) => {
      const rows = CANONICAL_GESTURE_ORDER.map((canonicalLabel) => {
        const category = categories.find((item) => item.categoryName === canonicalLabel);
        const score = category?.score ?? 0;
        return `
          <div class="probability-item">
            <div class="probability-head">
              <span>${formatGestureLabel(canonicalLabel)}</span>
              <span class="probability-value">${Math.round(score * 100)}%</span>
            </div>
            <div class="probability-track">
              <div class="probability-fill" style="width: ${score * 100}%"></div>
            </div>
          </div>
        `;
      }).join("");

      return `
        <section class="gesture-card">
          <div class="gesture-card-head">
            <span class="gesture-card-title">Hand ${index + 1} · ${handednessLabel}</span>
            <span class="gesture-card-result">${topGestureLabel}</span>
          </div>
          <div class="probability-list">${rows}</div>
        </section>
      `;
    })
    .join("");

  controlValues.gestureResults.innerHTML = markup;
}

function syncControlLabels() {
  controlValues.gestureResult.textContent = controls.gestureDetection.checked ? "Ready" : "Off";
  renderGestureResults(
    controls.gestureDetection.checked
      ? "Start the camera to see per-hand gesture classifications."
      : "Enable gesture detection to see per-hand results.",
  );
  controlValues.maxHands.textContent = controls.maxHands.value;
  controlValues.minDetectionConfidence.textContent = toNumber(
    controls.minDetectionConfidence.value,
  ).toFixed(2);
  controlValues.minTrackingConfidence.textContent = toNumber(
    controls.minTrackingConfidence.value,
  ).toFixed(2);
}

function currentOptions() {
  return {
    numHands: Number.parseInt(controls.maxHands.value, 10),
    minHandDetectionConfidence: toNumber(controls.minDetectionConfidence.value),
    minHandPresenceConfidence: Math.max(
      0.1,
      toNumber(controls.minDetectionConfidence.value) - 0.05,
    ),
    minTrackingConfidence: toNumber(controls.minTrackingConfidence.value),
    cannedGesturesClassifierOptions: {
      scoreThreshold: 0,
      maxResults: CANONICAL_GESTURE_ORDER.length,
    },
  };
}

async function applyOptions() {
  syncControlLabels();

  if (!gestureRecognizer) {
    return;
  }

  await gestureRecognizer.setOptions(currentOptions());
  if (isRunning) {
    updateStatus("live", "Live");
  }
}

function onResults(results) {
  const width = results.image.videoWidth || results.image.width;
  const height = results.image.videoHeight || results.image.height;

  if (!width || !height) {
    return;
  }

  if (canvasElement.width !== width || canvasElement.height !== height) {
    canvasElement.width = width;
    canvasElement.height = height;
    syncStageAspectRatio(width, height);
  }

  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);

  // Mirror the preview so hand motion feels natural in a selfie-style view.
  canvasCtx.translate(canvasElement.width, 0);
  canvasCtx.scale(-1, 1);
  canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

  if (results.landmarks) {
    results.landmarks.forEach((landmarks) => {
      drawingUtils.drawConnectors(landmarks, GestureRecognizer.HAND_CONNECTIONS, {
        color: "#f8fafc",
        lineWidth: 3,
      });
      drawingUtils.drawLandmarks(landmarks, {
        color: "#ffffff",
        fillColor: "#ffffff",
        lineWidth: 1,
        radius: 2.5,
      });
    });
  }

  canvasCtx.restore();

  if (!controls.gestureDetection.checked) {
    controlValues.gestureResult.textContent = "Off";
    renderGestureResults("Enable gesture detection to see per-hand results.");
    return;
  }

  if (!results.gestures?.length) {
    controlValues.gestureResult.textContent = "Ready";
    renderGestureResults("No hands recognized in frame.");
    return;
  }

  const handResults = results.gestures.map((categories, index) => {
    const handednessLabel = results.handedness[index]?.[0]?.categoryName ?? "Unknown";
    const topGesture = categories[0]?.categoryName ?? "None";
    return {
      handednessLabel,
      topGestureLabel: formatGestureLabel(topGesture),
      categories,
    };
  });

  controlValues.gestureResult.textContent = `${handResults.length} hand${handResults.length === 1 ? "" : "s"}`;
  renderGestureResults("", handResults);
}

async function ensureGestureRecognizer() {
  if (gestureRecognizer) {
    return gestureRecognizer;
  }

  const vision = await FilesetResolver.forVisionTasks("./node_modules/@mediapipe/tasks-vision/wasm");
  gestureRecognizer = await GestureRecognizer.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: MODEL_ASSET_PATH,
    },
    runningMode: "VIDEO",
    ...currentOptions(),
  });

  return gestureRecognizer;
}

function createCameraSource() {
  let stream = null;
  return {
    onEnded: null,
    async start(videoEl) {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 960 },
          height: { ideal: 540 },
          facingMode: "user",
        },
        audio: false,
      });
      videoEl.srcObject = stream;
      const videoTrack = stream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.addEventListener("ended", () => this.onEnded?.());
      }
      await videoEl.play();
    },
    stop(videoEl) {
      stream?.getTracks().forEach((track) => track.stop());
      videoEl.srcObject = null;
      stream = null;
    },
  };
}

function createVideoFileSource(file) {
  let objectUrl = null;
  return {
    onEnded: null,
    async start(videoEl) {
      objectUrl = URL.createObjectURL(file);
      videoEl.src = objectUrl;
      videoEl.addEventListener("ended", () => this.onEnded?.(), { once: true });
      await videoEl.play();
    },
    stop(videoEl) {
      videoEl.pause();
      videoEl.src = "";
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
        objectUrl = null;
      }
    },
  };
}

async function startPipeline(source) {
  if (isRunning) {
    return;
  }

  startButton.disabled = true;
  fileButton.disabled = true;
  updateStatus("idle", "Starting");
  controlValues.gestureResult.textContent = controls.gestureDetection.checked ? "Loading" : "Off";

  try {
    await ensureGestureRecognizer();
    await source.start(videoElement);

    currentSource = source;
    currentSource.onEnded = stopPipeline;

    lastVideoTime = -1;
    camera = { rafId: 0 };

    const renderFrame = () => {
      if (!isRunning || videoElement.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
        camera.rafId = requestAnimationFrame(renderFrame);
        return;
      }

      if (videoElement.currentTime !== lastVideoTime) {
        lastVideoTime = videoElement.currentTime;
        const results = gestureRecognizer.recognizeForVideo(videoElement, performance.now());
        onResults({
          image: videoElement,
          landmarks: results.landmarks,
          handedness: results.handedness,
          gestures: results.gestures,
        });
      }

      camera.rafId = requestAnimationFrame(renderFrame);
    };

    isRunning = true;
    stopButton.disabled = false;
    camera.rafId = requestAnimationFrame(renderFrame);
    updateStatus("live", "Live");
  } catch (error) {
    console.error(error);
    updateStatus("error", "Error");
    renderGestureResults("Could not initialize the gesture recognizer.");
    startButton.disabled = false;
    fileButton.disabled = false;
  }
}

function stopPipeline() {
  if (camera?.rafId) {
    cancelAnimationFrame(camera.rafId);
  }

  currentSource?.stop(videoElement);
  currentSource = null;
  camera = null;
  isRunning = false;
  startButton.disabled = false;
  fileButton.disabled = false;
  stopButton.disabled = true;
  syncControlLabels();
  updateStatus("idle", "Idle");
}

startButton.addEventListener("click", () => startPipeline(createCameraSource()));
stopButton.addEventListener("click", stopPipeline);

fileButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (file) startPipeline(createVideoFileSource(file));
  fileInput.value = "";
});

Object.values(controls).forEach((control) => {
  control.addEventListener("input", () => {
    applyOptions().catch((error) => {
      console.error(error);
      updateStatus("error", "Error");
    });
  });
});

syncControlLabels();
