/* ========== Realtime Conversation JS (extracted) ========== */
/*===========chatGPT o3 model generated code=============*/
const socket = io('/realtime');
const TARGET_RATE = 24000;
const SEND_INTERVAL_MS = 50;
const FORCE_MIN_MS = 120;
const FORCE_MIN_SAMPLES = TARGET_RATE * (FORCE_MIN_MS / 1000);

let audioContext, mediaStream, sourceNode, processorNode, silentGain;
let floatBuffers = [];
let lastSendTime = 0;
let sending = false;
let totalSamples = 0, turnSamples = 0;
let appendedSinceCommit = false;
let forceStopCooldown = false;
let lastForceStopTs = 0;
let realtimeSessionActive = false;
let awaitingSession = false;
let assistantBuffer = "";

const startBtn = document.getElementById('start');
const forceStopBtn = document.getElementById('forceStop');
const disconnectBtn = document.getElementById('disconnect');
const transcriptEl = document.getElementById('transcript');
const audioOutEl = document.getElementById('audioOut');
const metersEl = document.getElementById('meters');
const assistantLineEl = document.getElementById('assistantLine');

function resampleFloat32(input, fromRate, toRate){
  if (fromRate === toRate) return input;
  const ratio = toRate / fromRate;
  const out = new Float32Array(Math.round(input.length * ratio));
  for (let i=0;i<out.length;i++){
    const src = i / ratio;
    const i0 = Math.floor(src);
    const i1 = Math.min(i0+1, input.length-1);
    const t = src - i0;
    out[i] = input[i0]*(1-t) + input[i1]*t;
  }
  return out;
}
function floatToPCM16(arr){
  const o = new Int16Array(arr.length);
  for (let i=0;i<arr.length;i++){
    let s = Math.max(-1, Math.min(1, arr[i]));
    o[i] = s < 0 ? s*0x8000 : s*0x7FFF;
  }
  return o;
}

async function ensureRealtimeSession(){
  if (realtimeSessionActive) return;
  if (!awaitingSession){
    awaitingSession = true;
    startBtn.disabled = true;
    logLine("⏳ Initialize session...");
    socket.emit('realtime_init');
  }
  await new Promise(res=>{
    const check=()=> realtimeSessionActive ? res() : setTimeout(check, 40);
    check();
  });
}

async function startWorkflow(){
  await ensureRealtimeSession();
  await startCapture();
}

async function startCapture(){
  if (sending) return;
  audioContext = new (window.AudioContext||window.webkitAudioContext)();
  mediaStream = await navigator.mediaDevices.getUserMedia({audio:true});
  sourceNode = audioContext.createMediaStreamSource(mediaStream);
  processorNode = audioContext.createScriptProcessor(2048,1,1); // TODO: migrate to AudioWorklet
  sourceNode.connect(processorNode);
  silentGain = audioContext.createGain(); silentGain.gain.value = 0;
  processorNode.connect(silentGain); silentGain.connect(audioContext.destination);

  floatBuffers=[]; lastSendTime=0; totalSamples=0; turnSamples=0;
  assistantBuffer=""; appendedSinceCommit=false; sending=true;
  assistantLineEl.textContent = "";

  processorNode.onaudioprocess = e=>{
    const input = e.inputBuffer.getChannelData(0);
    floatBuffers.push(new Float32Array(input));
    totalSamples += input.length; turnSamples += input.length;
    const now = performance.now();
    if (now - lastSendTime >= SEND_INTERVAL_MS){
      lastSendTime = now; flushAndSend(); updateMeters();
    }
  };
  setTimeout(()=>{ if (sending && totalSamples===0) logLine("⚠️ Do not detect audio frames, check microphone."); }, 600);
  startBtn.disabled = true; disconnectBtn.disabled = false; forceStopBtn.disabled = true;
  logLine("🎤 Started continuous capture (server_vad)...");
  updateMeters();
}

function flushAndSend(){
  if (!sending || floatBuffers.length===0) return;
  let length=0; for (const b of floatBuffers) length += b.length;
  const merged = new Float32Array(length);
  let off=0; for (const b of floatBuffers){ merged.set(b,off); off+=b.length; }
  floatBuffers=[];
  const resampled = resampleFloat32(merged, audioContext.sampleRate, TARGET_RATE);
  if (!resampled.length) return;
  const pcm16 = floatToPCM16(resampled);
  socket.emit('audio_chunk', pcm16.buffer);
  appendedSinceCommit = true;
  if (!forceStopCooldown) forceStopBtn.disabled = false;
}

function forceStopTurn(){
  if (!sending) return;
  if (!appendedSinceCommit){ logLine("ℹ️ Force Stop ignore, no new audio."); return; }
  if (turnSamples < FORCE_MIN_SAMPLES){ logLine("⚠️ Current audio <120ms, ignored."); return; }
  const now = Date.now();
  if (now - lastForceStopTs < 500){ logLine("ℹ️ Cooling down."); return; }
  lastForceStopTs = now; forceStopCooldown = true; forceStopBtn.disabled = true;
  flushAndSend(); socket.emit('stop');
  logLine("⏹️ Manually ended current turn, waiting for response...");
  appendedSinceCommit=false; turnSamples=0;
  setTimeout(()=>{ forceStopCooldown=false; }, 600);
}

function disconnectSession(){
  sending=false;
  try{ processorNode?.disconnect(); silentGain?.disconnect(); sourceNode?.disconnect(); }catch(e){}
  mediaStream?.getTracks().forEach(t=>t.stop());
  audioContext?.close();
  socket.emit('disconnect_realtime');
  realtimeSessionActive=false;
  startBtn.disabled=false; forceStopBtn.disabled=true; disconnectBtn.disabled=true;
  logLine("🔌 Disconnected session."); metersEl.textContent="";
}

function updateMeters(){
  const msTotal = totalSamples / TARGET_RATE * 1000;
  const msTurn  = turnSamples  / TARGET_RATE * 1000;
  metersEl.textContent = `Mode: server_vad | Session: ${realtimeSessionActive?'ACTIVE':'INACTIVE'} | Turn audio? ${appendedSinceCommit?'YES':'NO'} | Total ${msTotal.toFixed(0)}ms | Turn ${msTurn.toFixed(0)}ms`;
}

let audioChunks=[];
function pcm16Base64Concat(chunks){
  let total=0;
  const arrs = chunks.map(b64=>{
    const bin = atob(b64);
    const u8 = new Uint8Array(bin.length);
    for (let i=0;i<bin.length;i++) u8[i]=bin.charCodeAt(i);
    total += u8.length; return u8;
  });
  const out = new Uint8Array(total);
  let off=0; for(const a of arrs){ out.set(a,off); off+=a.length; }
  return out;
}
function pcm16ToWav(pcmBytes, sampleRate){
  const channels=1;
  const blockAlign=channels*2;
  const byteRate=sampleRate*blockAlign;
  const buffer=new ArrayBuffer(44+pcmBytes.length);
  const view=new DataView(buffer);
  let o=0; const ws=s=>{ for(let i=0;i<s.length;i++) view.setUint8(o++, s.charCodeAt(i)); };
  ws('RIFF'); view.setUint32(o,36+pcmBytes.length,true); o+=4;
  ws('WAVE'); ws('fmt '); view.setUint32(o,16,true); o+=4;
  view.setUint16(o,1,true); o+=2; view.setUint16(o,channels,true); o+=2;
  view.setUint32(o,sampleRate,true); o+=4; view.setUint32(o,byteRate,true); o+=4;
  view.setUint16(o,blockAlign,true); o+=2; view.setUint16(o,16,true); o+=2;
  ws('data'); view.setUint32(o,pcmBytes.length,true); o+=4;
  new Uint8Array(buffer,44).set(pcmBytes);
  return new Blob([buffer], {type:'audio/wav'});
}
function finalizeAndPlay(){
  if (!audioChunks.length) return;
  const pcm = pcm16Base64Concat(audioChunks);
  const wav = pcm16ToWav(pcm, TARGET_RATE);
  audioOutEl.src = URL.createObjectURL(wav);
  audioOutEl.play();
  logLine("🔈 Played James Cao's voice.");
  audioChunks=[];
}

function renderAssistant(full){
  assistantLineEl.textContent = full ? ('James Cao: ' + full) : '';
}

function logLine(text){
  transcriptEl.textContent += text + "\n";
}

startBtn.addEventListener('click', startWorkflow);
forceStopBtn.addEventListener('click', forceStopTurn);
disconnectBtn.addEventListener('click', disconnectSession);

socket.on('connect', () => logLine("✅ Socket connected."));
socket.on('realtime_session_active', () => {
  realtimeSessionActive = true; awaitingSession=false;
  logLine("✅ Realtime session active.");
  if (!sending) startBtn.disabled=false;
  updateMeters();
});
socket.on('realtime_session_closed', () => {
  realtimeSessionActive=false; awaitingSession=false;
  logLine("🔕 Realtime session closed.");
  startBtn.disabled=false; updateMeters();
});
socket.on('vad', ev => {
  if (ev.stage === 'speech_started') turnSamples=0;
  logLine(`🛈 VAD: ${ev.stage}`);
});
socket.on('buffer_committed', () => {
  logLine("✅ Buffer committed (auto/force).");
  appendedSinceCommit=false; forceStopBtn.disabled=true; turnSamples=0; updateMeters();
});
socket.on('realtime_error', ev => {
  logLine(`❌ Error: ${ev.error?.message || JSON.stringify(ev)}`);
  console.error('Realtime error', ev);
});
socket.on('transcript', delta => {
  const last = assistantBuffer.slice(-1);
  const first = delta.charAt(0);
  const asciiWord = c => /[A-Za-z0-9]/.test(c);
  const needSpace = assistantBuffer && asciiWord(last) && asciiWord(first);
  assistantBuffer += (needSpace ? ' ' : '') + delta;
  renderAssistant(assistantBuffer);
});
socket.on('user_transcript', line => {
  const safe = line.replace(/</g,"&lt;");
  transcriptEl.innerHTML += `<span class="user-line">${safe}</span>\n`;
  assistantBuffer=""; renderAssistant("");
});
socket.on('audio_out', b64 => { audioChunks.push(b64); });
socket.on('audio_segment_done', finalizeAndPlay);
socket.on('response_complete', finalizeAndPlay);
/* debug events intentionally omitted */
