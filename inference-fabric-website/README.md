# Inference Fabric website
Responsive static project showcase for the Distributed Multi-Model AI Inference Fabric.

## Run locally
1. Keep the Docker gateway running at `http://127.0.0.1:8001`.
2. From this folder run `python -m http.server 8080` and open `http://127.0.0.1:8080`.
3. Use Live Demo to send a request to the local API. If browser CORS blocks localhost requests, use the PowerShell command in the main project README.

## Deploy
Deploy this folder as a static site on GitHub Pages, Netlify, Vercel, or another static host. The live demo currently targets a local API; for public visitors, deploy a secured API endpoint and update the API base URL.

## Accuracy notes
Benchmark figures are small sequential CPU runs from the project notes. Scheduler scores are synthetic proxy costs, not inference latency. The latest verified inference succeeds, but the scheduler reports `round_robin_fallback` because metrics are not currently available.


## Academic presentation updates
The page includes the project team, guide, institution, course, and academic year as supplied by the team. The cloud-computing quotation is original project copy.

## End-to-end demonstration checklist
- Start the Docker gateway and worker services used by the project.
- Open the website using `python -m http.server 8080` and visit `http://127.0.0.1:8080`.
- In **Operations**, select **Check local API status**.
- In **Live demo**, send a text request to `http://127.0.0.1:8001`.
- Confirm the returned JSON includes the model result and execution status.

Important: a static website cannot itself start Docker containers. The API demonstration requires the backend to be running. Browser CORS policy may prevent a page served from port 8080 from calling the API on port 8001. If that happens, use the PowerShell request in the main project README to verify the backend, or configure CORS in the gateway for the local demo origin. Do not expose a development API publicly without appropriate authentication, network controls, and CORS configuration.


## Interactive model demo
The demo supports DistilBERT text sentiment, TinyLlama text generation, and YOLOv8n object detection. Select YOLO to upload a JPG, PNG, or WebP image (up to 10 MB). The browser sends the image as `image_base64` to the API. The page can show detection labels and draw boxes when the API returns `bbox` values as `[x1, y1, x2, y2]`.

For local use, run the gateway at `http://127.0.0.1:8001` and serve this folder over HTTP. For public hosting, set the API base URL to a publicly reachable HTTPS endpoint and configure backend CORS to allow the deployed site's exact origin. A static frontend host does not host the inference backend.
