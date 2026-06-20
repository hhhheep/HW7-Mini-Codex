// Binary Search Visual Demo

let array = [];
let target = 23;
let low = 0;
let high = 0;
let mid = 0;
let found = false;
let done = false;
let stepHistory = [];
let currentStep = -1;

const arrayInput = document.getElementById('arrayInput');
const targetInput = document.getElementById('targetInput');
const resetBtn = document.getElementById('resetBtn');
const stepBtn = document.getElementById('stepBtn');
const autoBtn = document.getElementById('autoBtn');
const arrayDisplay = document.getElementById('arrayDisplay');
const lowDisplay = document.getElementById('lowDisplay');
const midDisplay = document.getElementById('midDisplay');
const highDisplay = document.getElementById('highDisplay');
const statusDisplay = document.getElementById('statusDisplay');
const explanationBox = document.getElementById('explanationBox');

function parseArray(str) {
  return str.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
}

function init() {
  array = parseArray(arrayInput.value);
  target = parseInt(targetInput.value, 10);
  low = 0;
  high = array.length - 1;
  mid = Math.floor((low + high) / 2);
  found = false;
  done = false;
  currentStep = -1;
  stepHistory = [];
  // Record initial state
  stepHistory.push({
    low: low,
    high: high,
    mid: mid,
    found: false,
    done: false,
    explanation: "Initial state. Searching for " + target + " in the array."
  });
  render();
}

function stepForward() {
  if (done || found) {
    statusDisplay.textContent = found ? "Target found!" : "Search complete.";
    return;
  }
  if (low > high) {
    done = true;
    stepHistory.push({
      low: low,
      high: high,
      mid: mid,
      found: false,
      done: true,
      explanation: "Low has crossed high. Target not found."
    });
    currentStep = stepHistory.length - 1;
    render();
    return;
  }
  mid = Math.floor((low + high) / 2);
  let explanation = "";
  if (array[mid] === target) {
    found = true;
    explanation = "Found target " + target + " at index " + mid + ".";
  } else if (array[mid] < target) {
    explanation = "Array[" + mid + "] = " + array[mid] + " < " + target + ", so search right half.";
    low = mid + 1;
  } else {
    explanation = "Array[" + mid + "] = " + array[mid] + " > " + target + ", so search left half.";
    high = mid - 1;
  }
  stepHistory.push({
    low: low,
    high: high,
    mid: mid,
    found: found,
    done: done,
    explanation: explanation
  });
  currentStep = stepHistory.length - 1;
  render();
}

function render() {
  if (stepHistory.length === 0) return;
  const state = stepHistory[currentStep];
  low = state.low;
  high = state.high;
  mid = state.mid;
  found = state.found;
  done = state.done;

  // Update array display
  arrayDisplay.innerHTML = '';
  for (let i = 0; i < array.length; i++) {
    const cell = document.createElement('div');
    cell.className = 'array-cell';
    cell.textContent = array[i];
    if (i === low && low <= high && !found) {
      cell.classList.add('low');
    }
    if (i === mid && !found) {
      cell.classList.add('mid');
    }
    if (i === high && high >= low && !found) {
      cell.classList.add('high');
    }
    if (found && i === mid) {
      cell.classList.add('found');
    }
    arrayDisplay.appendChild(cell);
  }

  // Update info panel
  lowDisplay.textContent = low;
  midDisplay.textContent = mid;
  highDisplay.textContent = high;
  if (found) {
    statusDisplay.textContent = "Found at index " + mid;
  } else if (done) {
    statusDisplay.textContent = "Not found";
  } else {
    statusDisplay.textContent = "Searching...";
  }
  explanationBox.textContent = state.explanation;
}

function reset() {
  init();
  currentStep = 0;
  render();
}

// Auto run
let autoInterval = null;
function autoRun() {
  if (autoInterval) {
    clearInterval(autoInterval);
    autoInterval = null;
    autoBtn.textContent = "Auto Run";
    return;
  }
  autoBtn.textContent = "Stop";
  autoInterval = setInterval(() => {
    if (done || found) {
      clearInterval(autoInterval);
      autoInterval = null;
      autoBtn.textContent = "Auto Run";
      return;
    }
    stepForward();
  }, 1000);
}

// Event listeners
resetBtn.addEventListener('click', reset);
stepBtn.addEventListener('click', stepForward);
autoBtn.addEventListener('click', autoRun);
arrayInput.addEventListener('change', reset);
targetInput.addEventListener('change', reset);

// Initialize
init();
currentStep = 0;
render();