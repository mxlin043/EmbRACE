// One clip per model and task type, all recorded for this paper. Each clip
// plays the motion at the speed the character moved, so none carries a speed
// label.
const BASELINE_MODELS = ["gpt", "claude", "gemini", "qwen", "qwen_ft"];

const BASELINE_TYPES = [
  "Basic",
  "Exploration",
  "Dynamic_Spatial-Semantic",
  "Multi-stage",
  "Interaction_Open-Door",
  "Interaction_Pick-and-Drop"
];

// Main update function
function updateBaselineVideos() {
  const type = document.getElementById("baseline-type").value;
  if (!BASELINE_TYPES.includes(type)) {
    console.warn(`Unknown task type ${type}`);
    return;
  }

  const columns = {
    gpt: { videoId: "gpt-video", labelId: "gpt-label" },
    claude: { videoId: "claude-video", labelId: "claude-label" },
    gemini: { videoId: "gemini-video", labelId: "gemini-label" },
    qwen: { videoId: "qwen-video", labelId: "qwen-label" },
    qwen_ft: { videoId: "qwenft-video", labelId: "qwen_ft-label" }
  };

  BASELINE_MODELS.forEach(model => {
    const videoElem = document.getElementById(columns[model].videoId);
    const sourceElem = videoElem.querySelector("source");
    sourceElem.src = `static/baselines/${type}/${model}.mp4`;
    videoElem.load();

    // No clip is played back accelerated, so the speed chip stays hidden.
    const labelElem = document.getElementById(columns[model].labelId);
    if (labelElem) {
      labelElem.innerText = "";
      labelElem.style.display = "none";
    }
  });
}

console.log("Offline baseline viewer loaded.");
