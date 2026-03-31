const canvas = document.getElementById('sim-canvas');
const ctx = canvas.getContext('2d');

const valKe = document.getElementById('val-ke');
const valPx = document.getElementById('val-px');
const valPy = document.getElementById('val-py');
const valPmag = document.getElementById('val-pmag');

const configHost = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsHost = `${configHost}//${window.location.host}/ws`;
const socket = new WebSocket(wsHost);

let bodies = [];

// Graph data buffers
const keData = [];
const pxData = [];
const pyData = [];
const pmagData = [];
const maxDataPoints = 300;

const canvasKe = document.getElementById('graph-ke');
const ctxKe = canvasKe.getContext('2d');
const canvasMom = document.getElementById('graph-mom');
const ctxMom = canvasMom.getContext('2d');

socket.onopen = () => {
    console.log("Connected to Physics Engine WebSocket");
};

socket.onmessage = (event) => {
    try {
        const state = JSON.parse(event.data);
        bodies = state.bodies;
        
        // Update telemetry text
        valKe.innerText = state.telemetry.ke.toFixed(3);
        valPx.innerText = state.telemetry.px.toFixed(3);
        valPy.innerText = state.telemetry.py.toFixed(3);
        valPmag.innerText = state.telemetry.pmag.toFixed(3);

        // Update telemetry graphs
        keData.push(state.telemetry.ke);
        pxData.push(state.telemetry.px);
        pyData.push(state.telemetry.py);
        pmagData.push(state.telemetry.pmag);
        
        if(keData.length > maxDataPoints) keData.shift();
        if(pxData.length > maxDataPoints) pxData.shift();
        if(pyData.length > maxDataPoints) pyData.shift();
        if(pmagData.length > maxDataPoints) pmagData.shift();

        // draw graphs
        drawGraph(ctxKe, canvasKe.width, canvasKe.height, [
            {data: keData, color: 'rgb(255, 200, 80)'} 
        ]);
        drawGraph(ctxMom, canvasMom.width, canvasMom.height, [
            {data: pxData, color: 'rgb(0, 230, 200)'}, 
            {data: pyData, color: 'rgb(255, 90, 170)'}, 
            {data: pmagData, color: 'rgb(140, 180, 255)'} 
        ]);

        requestAnimationFrame(drawSimulation);
    } catch (e) {
        console.error("Error parsing WebSocket message", e);
    }
};

socket.onclose = () => {
    console.warn("WebSocket closed.");
};

function drawGraph(ctxG, w, h, datasets) {
    ctxG.clearRect(0, 0, w, h);
    if(datasets.length === 0 || datasets[0].data.length < 2) return;
    
    let min = Infinity, max = -Infinity;
    for(let ds of datasets) {
        for(let v of ds.data) {
            if(v < min) min = v;
            if(v > max) max = v;
        }
    }
    
    let span = max - min;
    // ensure graphs don't explode when values are tiny (like 0.0)
    if(span < 0.1 && ctxG.canvas.id === 'graph-ke') {
         span = 0.1;
         let mid = (min+max)/2;
         min = mid - 0.05; max = mid + 0.05;
    }
    if (span < 1e-9) { span = 2; min -= 1; max += 1; }
    
    min -= span*0.05; max += span*0.05;
    span = max - min;
    
    for(let ds of datasets) {
        ctxG.strokeStyle = ds.color;
        ctxG.lineWidth = 1.5;
        ctxG.beginPath();
        for(let i=0; i<ds.data.length; i++) {
            let x = (i / (maxDataPoints - 1)) * w;
            let y = h - ((ds.data[i] - min) / span) * h;
            if(i === 0) ctxG.moveTo(x, y);
            else ctxG.lineTo(x, y);
        }
        ctxG.stroke();
    }
}

function drawSimulation() {
    // Fill the background natively so it matches physics bounds 100%
    ctx.fillStyle = "#111827";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for(let b of bodies) {
        ctx.fillStyle = b.color;
        ctx.save();
        ctx.translate(b.x, b.y);
        ctx.rotate(b.angle);

        ctx.beginPath();
        if(b.type === 'ball') {
            ctx.arc(0, 0, b.radius, 0, Math.PI * 2);
        } else if (b.type === 'polygon' && b.verts) {
            ctx.moveTo(b.verts[0][0], b.verts[0][1]);
            for(let i=1; i<b.verts.length; i++) {
                ctx.lineTo(b.verts[i][0], b.verts[i][1]);
            }
            ctx.closePath();
        }
        ctx.fill();

        ctx.strokeStyle = "rgba(255,255,255,0.7)";
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.restore();
    }
    
    // Draw rigid boundary frame
    ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
    ctx.lineWidth = 4;
    ctx.strokeRect(0, 0, canvas.width, canvas.height);
}

// GUI UI Sync
function toggleInput(checkboxId, inputId) {
    const chk = document.getElementById(checkboxId);
    const inp = document.getElementById(inputId);
    inp.disabled = chk.checked;
    chk.addEventListener('change', () => {
        inp.disabled = chk.checked;
    });
}
toggleInput('chk-radius-rnd', 'inp-radius');
toggleInput('chk-density-rnd', 'inp-density');
toggleInput('chk-speed-rnd', 'inp-speed');

function getProp(chkId, inpId, isFloat=true) {
    if(document.getElementById(chkId).checked) return null;
    let v = document.getElementById(inpId).value;
    return isFloat ? parseFloat(v) : parseInt(v);
}

document.getElementById('btn-add-ball').addEventListener('click', () => {
    socket.send(JSON.stringify({
        action: 'add_ball',
        radius: getProp('chk-radius-rnd', 'inp-radius'),
        density: getProp('chk-density-rnd', 'inp-density'),
        speed: getProp('chk-speed-rnd', 'inp-speed')
    }));
});

document.getElementById('btn-add-poly').addEventListener('click', () => {
    socket.send(JSON.stringify({
        action: 'add_poly',
        edges: parseInt(document.getElementById('inp-edges').value) || null,
        radius: getProp('chk-radius-rnd', 'inp-radius'),
        density: getProp('chk-density-rnd', 'inp-density'),
        speed: getProp('chk-speed-rnd', 'inp-speed')
    }));
});

document.getElementById('btn-clear').addEventListener('click', () => {
    socket.send(JSON.stringify({action: 'clear'}));

    // clear historical graphs
    keData.length = 0; pxData.length = 0; pyData.length = 0; pmagData.length = 0;
});

// Environment controls
document.getElementById('btn-play-pause').addEventListener('click', () => {
    socket.send(JSON.stringify({action: 'toggle_play'}));
});

function sendGravity() {
    socket.send(JSON.stringify({
        action: 'set_gravity',
        down: document.getElementById('chk-g-down').checked,
        up: document.getElementById('chk-g-up').checked,
        left: document.getElementById('chk-g-left').checked,
        right: document.getElementById('chk-g-right').checked,
    }));
}
document.getElementById('chk-g-down').addEventListener('change', sendGravity);
document.getElementById('chk-g-up').addEventListener('change', sendGravity);
document.getElementById('chk-g-left').addEventListener('change', sendGravity);
document.getElementById('chk-g-right').addEventListener('change', sendGravity);

document.getElementById('chk-elastic').addEventListener('change', (e) => {
    socket.send(JSON.stringify({
        action: 'set_elastic',
        elastic: e.target.checked
    }));
});
