// Preloaded real index.json (static)
const REAL_INDEX = {
  "Navigation": {
    "gpt": { "file": "gpt_4.mp4", "speed": 4 },
    "claude": { "file": "claude_4.mp4", "speed": 4 },
    "gemini": { "file": "gemini_4.mp4", "speed": 4 },
    "qwen": { "file": "qwen_4.mp4", "speed": 4 },
    "qwen_ft": { "file": "qwen_ft_4.mp4", "speed": 4 }
  },

  "Interaction": {
    "gpt": { "file": "gpt_4.mp4", "speed": 4 },
    "claude": { "file": "claude_4.mp4", "speed": 4 },
    "gemini": { "file": "gemini_4.mp4", "speed": 4 },
    "qwen": { "file": "qwen_4.mp4", "speed": 4 },
    "qwen_ft": { "file": "qwen_ft_4.mp4", "speed": 4 }
  }
};

// Main update function
function updateRealVideos() {
  const type = document.getElementById("real-type").value;

  const models = [
    { name: "gpt", videoId: "gpt-video-real" },
    { name: "claude", videoId: "claude-video-real" },
    { name: "gemini", videoId: "gemini-video-real" },
    { name: "qwen", videoId: "qwen-video-real" },
    { name: "qwen_ft", videoId: "qwenft-video-real" }
  ];

  models.forEach(model => {
    const entry = REAL_INDEX[type]?.[model.name];
    const videoElem = document.getElementById(model.videoId);
    const sourceElem = videoElem.querySelector("source");

    if (entry && entry.file) {
      const videoPath = `static/real/${type}/${entry.file}`;
      sourceElem.src = videoPath;
      // A first-frame poster, so the cell shows the scene before anyone presses play and
      // never sits blank while the clip loads.
      videoElem.poster = videoPath.replace(/\.mp4$/, ".jpg");
      videoElem.load();
    } else {
      sourceElem.src = "";
      videoElem.removeAttribute("poster");
      videoElem.load();
      console.warn(`No entry for ${model.name} in ${type}`);
    }
  });
}

console.log("Real viewer loaded (IDs isolated from baseline).");
