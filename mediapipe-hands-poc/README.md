# MediaPipe Hands POC

This folder contains a small local webcam demo built from the MediaPipe Hands JavaScript solution described in the official docs:

- https://mediapipe.readthedocs.io/en/latest/solutions/hands.html

## What it does

- Opens your webcam in the browser
- Tracks up to 4 hands
- Draws the 21 hand landmarks and connector lines
- Lets you tune the main detection and tracking options live

## Run it

From this folder:

```bash
npm install
npm start
```

Then open:

- http://localhost:4173

## Notes

- `localhost` is important because browsers allow webcam access there.
- The doc page above is the legacy MediaPipe Solutions documentation. This proof of concept intentionally uses that same JavaScript Hands solution so the behavior matches the example the docs describe.
