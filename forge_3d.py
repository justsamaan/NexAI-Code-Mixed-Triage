"""
forge_3d.py
===========
3D Workstation Forge & Bottom-Up Parser State Derivation Model
--------------------------------------------------------------
Implements:
1. Formal 5-stage bottom-up parser state derivation pipeline:
   - S0 -> S1: Lexical Smelter & Script Ingestion (Vulcan the Smelter Golem)
   - S1 -> S2: Dialect & Code-Mix Anvil (Gildor the Dialect Imp)
   - S2 -> S3: Semantic Translation Crucible (Brog the Blacksmith Dwarf)
   - S3 -> S4: Intent & Urgency Gem-Cutter (Pyra the Urgency Sprite)
   - S4 -> S5: Dispatch & Agent Beacon (Hermes the Dispatch Automaton -> ACCEPT)
2. Interactive WebGL Three.js 3D Forge Visualization with animated creatures,
   traveling prompt packet crystal, ember particles, and station HUD.
3. Free-navigation derivation table generator.
"""

import json
import re
import html
import ai_engine


# -----------------------------------------------------------------------------
# 1. Bottom-Up Parser State Derivation Pipeline
# -----------------------------------------------------------------------------

CREATURES = {
    1: {
        "id": "vulcan",
        "name": "Vulcan",
        "title": "Smelter Golem",
        "avatar": "🌋",
        "station": "Lexical Smelter & Script Ingestion",
        "action": "SHIFT",
        "role": "Scans raw character stream, extracts script (Latin / Devanagari / Telugu / Tamil), and tokenizes words into lexical stack.",
        "color": "#f97316"
    },
    2: {
        "id": "gildor",
        "name": "Gildor",
        "title": "Dialect Imp",
        "avatar": "🔍",
        "station": "Dialect & Code-Mix Anvil",
        "action": "REDUCE",
        "role": "Cross-references Indic code-mix dictionaries, determines dialect ratio (Hinglish / Tanglish / Tenglish / English).",
        "color": "#10b981"
    },
    3: {
        "id": "brog",
        "name": "Brog",
        "title": "Blacksmith Dwarf",
        "avatar": "🔨",
        "station": "Semantic Translation Crucible",
        "action": "REDUCE",
        "role": "Pounds code-mixed phrases on his anvil into normalized, grammatically coherent English semantics.",
        "color": "#38bdf8"
    },
    4: {
        "id": "pyra",
        "name": "Pyra",
        "title": "Urgency Sprite",
        "avatar": "🔥",
        "station": "Intent & Urgency Gem-Cutter",
        "action": "REDUCE",
        "role": "Reflects customer emotion through an illuminated crystal prism, classifying Intent, Urgency, and Calibrated Confidence.",
        "color": "#ec4899"
    },
    5: {
        "id": "hermes",
        "name": "Hermes",
        "title": "Dispatch Automaton",
        "avatar": "📜",
        "station": "Dispatch & Agent Beacon",
        "action": "ACCEPT",
        "role": "Synthesizes final localized agent reply draft and routes ticket to specialized human queue or autonomous resolution.",
        "color": "#eab308"
    }
}


def derive_parser_pipeline(message: str) -> dict:
    """
    Executes the full triage analysis and derives the 5 discrete bottom-up parser states.
    Returns derivation steps, token metadata, and final synthesis.
    """
    raw_msg = (message or "").strip()
    if not raw_msg:
        raw_msg = "mera order deliver nahi hua"

    # Run AI engine analysis
    analysis = ai_engine.analyze_message(raw_msg)
    detected_lang = analysis.get("detected_language", "English")
    translation = analysis.get("english_translation", raw_msg)
    intent = analysis.get("intent", "General Inquiry")
    urgency = analysis.get("urgency", "low")
    confidence = float(analysis.get("confidence", 0.85))
    draft_reply = analysis.get("draft_reply", "Thank you for contacting customer support.")
    escalate = bool(analysis.get("escalate", False))
    escalation_reason = analysis.get("escalation_reason", "")

    # Lexical tokenization
    tokens = re.findall(r"\w+|[^\w\s]", raw_msg, re.UNICODE)
    
    # Script identification
    has_devanagari = bool(re.search(r"[\u0900-\u097F]", raw_msg))
    has_telugu = bool(re.search(r"[\u0C00-\u0C7F]", raw_msg))
    has_tamil = bool(re.search(r"[\u0B80-\u0BFF]", raw_msg))
    
    if has_devanagari:
        script_label = "Devanagari Script (हिन्दी)"
    elif has_telugu:
        script_label = "Telugu Script (తెలుగు)"
    elif has_tamil:
        script_label = "Tamil Script (தமிழ்)"
    else:
        script_label = "Latin / Romanized Script"

    # Step-by-step state derivation records
    steps = [
        {
            "step": 1,
            "state_label": "S0 → S1",
            "creature": CREATURES[1]["name"],
            "title": CREATURES[1]["title"],
            "station": CREATURES[1]["station"],
            "action": "SHIFT",
            "stack": f"[$] · Ingesting {len(tokens)} tokens",
            "input_buffer": f"\"{raw_msg}\"",
            "production": f"RawPrompt → TokenList({len(tokens)}) · Script({script_label})",
            "output_payload": {
                "script": script_label,
                "tokens": tokens,
                "token_count": len(tokens),
                "char_count": len(raw_msg)
            },
            "summary": f"Vulcan melted input into {len(tokens)} lexical tokens in {script_label}."
        },
        {
            "step": 2,
            "state_label": "S1 → S2",
            "creature": CREATURES[2]["name"],
            "title": CREATURES[2]["title"],
            "station": CREATURES[2]["station"],
            "action": "REDUCE",
            "stack": f"[S1, Tokens, {script_label}]",
            "input_buffer": f"Dialect matching over {len(tokens)} tokens",
            "production": f"TokenList → Dialect({detected_lang})",
            "output_payload": {
                "detected_language": detected_lang,
                "dialect_confidence": f"{int(confidence * 100)}%",
                "code_mix_type": "Code-Mixed Romanized" if "Latin" in script_label and detected_lang != "English" else "Native / Standard"
            },
            "summary": f"Gildor matched dialect as '{detected_lang}' using Indic vocabulary heuristics."
        },
        {
            "step": 3,
            "state_label": "S2 → S3",
            "creature": CREATURES[3]["name"],
            "title": CREATURES[3]["title"],
            "station": CREATURES[3]["station"],
            "action": "REDUCE",
            "stack": f"[S2, Dialect({detected_lang})]",
            "input_buffer": f"\"{raw_msg}\"",
            "production": f"DialectPhrase → EnglishSemantic(\"{translation}\")",
            "output_payload": {
                "source": raw_msg,
                "detected_language": detected_lang,
                "english_translation": translation
            },
            "summary": f"Brog hammered the code-mixed phrasing into: \"{translation}\""
        },
        {
            "step": 4,
            "state_label": "S3 → S4",
            "creature": CREATURES[4]["name"],
            "title": CREATURES[4]["title"],
            "station": CREATURES[4]["station"],
            "action": "REDUCE",
            "stack": f"[S3, EnglishSemantic]",
            "input_buffer": f"\"{translation}\"",
            "production": f"Semantic → Intent({intent}) ⊕ Urgency({urgency.upper()})",
            "output_payload": {
                "intent": intent,
                "urgency": urgency,
                "confidence": confidence,
                "escalate": escalate,
                "escalation_reason": escalation_reason
            },
            "summary": f"Pyra classified Intent as '{intent}' with {urgency.upper()} urgency ({int(confidence * 100)}% calibrated confidence)."
        },
        {
            "step": 5,
            "state_label": "S4 → S5",
            "creature": CREATURES[5]["name"],
            "title": CREATURES[5]["title"],
            "station": CREATURES[5]["station"],
            "action": "ACCEPT",
            "stack": f"[S4, Intent({intent}), Urgency({urgency.upper()})]",
            "input_buffer": "[$]",
            "production": f"TriageState → DraftReply ⊕ DispatchTarget (ACCEPT)",
            "output_payload": {
                "draft_reply": draft_reply,
                "dispatch_route": "Human Specialist Queue" if escalate else "Autonomous AI Resolution",
                "status": "ACCEPT (Triage Complete)"
            },
            "summary": f"Hermes synthesized customer reply draft and accepted state for final delivery."
        }
    ]

    return {
        "message": raw_msg,
        "tokens": tokens,
        "script": script_label,
        "analysis": analysis,
        "steps": steps
    }


# -----------------------------------------------------------------------------
# 2. WebGL Three.js 3D Workstation Forge Canvas Generator
# -----------------------------------------------------------------------------

def build_threejs_forge_html(message: str, active_state: int = 5) -> str:
    """
    Renders the interactive 3D WebGL scene with 5 workstation islands, animated creatures,
    floating magma embers, connecting energy rails, and traveling prompt packet.
    """
    pipeline_data = derive_parser_pipeline(message)
    json_pipeline = json.dumps(pipeline_data)

    html_code = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NexAI 3D Workstation Forge</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
            -webkit-user-select: none;
        }}
        body, html {{
            width: 100%;
            height: 100%;
            overflow: hidden;
            background: #080a0f;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #f1f5f9;
        }}
        #canvas-container {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            z-index: 1;
        }}
        /* HUD Top Bar */
        .hud-top {{
            position: absolute;
            top: 14px;
            left: 16px;
            right: 16px;
            z-index: 10;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            pointer-events: none;
        }}
        .hud-card {{
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            border: 1px solid rgba(249, 115, 22, 0.35);
            border-radius: 10px;
            padding: 10px 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6), 0 0 15px rgba(249, 115, 22, 0.15);
            pointer-events: auto;
        }}
        .hud-title {{
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #fb923c;
            font-weight: 700;
            margin-bottom: 3px;
        }}
        .hud-value {{
            font-size: 1.05rem;
            font-weight: 700;
            color: #f8fafc;
        }}
        .hud-sub {{
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 2px;
        }}
        /* Bottom Controls Bar */
        .hud-bottom {{
            position: absolute;
            bottom: 14px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
            display: flex;
            gap: 8px;
            align-items: center;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 9999px;
            padding: 6px 14px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.7);
        }}
        .hud-btn {{
            background: #1e293b;
            color: #f1f5f9;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 0.8rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .hud-btn:hover {{
            background: #f97316;
            color: #fff;
            border-color: #fb923c;
            box-shadow: 0 0 12px rgba(249, 115, 22, 0.5);
            transform: translateY(-1px);
        }}
        .hud-btn.active {{
            background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);
            border-color: #fdba74;
            color: #fff;
            box-shadow: 0 0 14px rgba(249, 115, 22, 0.6);
        }}
        .station-indicator {{
            font-size: 0.76rem;
            color: #fdba74;
            padding: 0 4px;
        }}
        /* Instructions Overlay */
        .instruction-tag {{
            position: absolute;
            bottom: 60px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9;
            font-size: 0.76rem;
            color: #64748b;
            background: rgba(8, 10, 15, 0.7);
            padding: 4px 12px;
            border-radius: 12px;
            pointer-events: none;
        }}
    </style>
    <!-- Three.js and OrbitControls via CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="canvas-container"></div>

    <!-- Top HUD -->
    <div class="hud-top">
        <div class="hud-card" style="max-width: 380px;">
            <div class="hud-title" id="hud-station-tag">Station 5: Dispatch & Beacon</div>
            <div class="hud-value" id="hud-creature-tag">Hermes the Dispatch Automaton</div>
            <div class="hud-sub" id="hud-production-tag">TriageState → DraftReply ⊕ DispatchTarget (ACCEPT)</div>
        </div>
        <div class="hud-card" style="text-align: right; max-width: 320px;">
            <div class="hud-title">Prompt Packet</div>
            <div class="hud-value" style="font-size: 0.95rem; color: #38bdf8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" id="hud-prompt-msg">"{html.escape(pipeline_data['message'])}"</div>
            <div class="hud-sub" id="hud-status-badge" style="color: #4ade80; font-weight: 600;">Status: ACCEPT Complete</div>
        </div>
    </div>

    <div class="instruction-tag">🖱️ Left-click + drag to rotate • Scroll to zoom • Click buttons to jump workstations</div>

    <!-- Bottom Controls -->
    <div class="hud-bottom">
        <button class="hud-btn" id="btn-play">▶ Play All</button>
        <button class="hud-btn" id="btn-prev">⏮ Prev</button>
        <span class="station-indicator" id="step-counter">Step 5 of 5</span>
        <button class="hud-btn" id="btn-next">Next ⏭</button>
        <button class="hud-btn" id="btn-reset">🔄 Reset</button>
        <div style="width: 1px; height: 18px; background: rgba(255,255,255,0.2); margin: 0 4px;"></div>
        <button class="hud-btn" onclick="jumpToStation(1)">S1: Vulcan</button>
        <button class="hud-btn" onclick="jumpToStation(2)">S2: Gildor</button>
        <button class="hud-btn" onclick="jumpToStation(3)">S3: Brog</button>
        <button class="hud-btn" onclick="jumpToStation(4)">S4: Pyra</button>
        <button class="hud-btn active" onclick="jumpToStation(5)">S5: Hermes</button>
    </div>

    <script>
        const pipelineData = {json_pipeline};
        const steps = pipelineData.steps;

        // --- 1. Three.js Scene Setup ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x080a0f, 0.018);

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 18, 38);

        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: false }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.maxPolarAngle = Math.PI / 2.1;
        controls.minDistance = 8;
        controls.maxDistance = 65;

        // --- 2. Lighting ---
        const ambientLight = new THREE.AmbientLight(0x1e293b, 1.2);
        scene.add(ambientLight);

        const forgeSun = new THREE.DirectionalLight(0xff7700, 1.6);
        forgeSun.position.set(10, 30, 20);
        forgeSun.castShadow = true;
        scene.add(forgeSun);

        const blueRimLight = new THREE.DirectionalLight(0x38bdf8, 0.9);
        blueRimLight.position.set(-20, 20, -15);
        scene.add(blueRimLight);

        // --- 3. Magma Ember Floating Particles ---
        const particleCount = 450;
        const particleGeometry = new THREE.BufferGeometry();
        const particlePositions = new Float32Array(particleCount * 3);
        const particleSpeeds = new Float32Array(particleCount);

        for (let i = 0; i < particleCount; i++) {{
            particlePositions[i * 3] = (Math.random() - 0.5) * 60;
            particlePositions[i * 3 + 1] = Math.random() * 25 - 5;
            particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 40;
            particleSpeeds[i] = 0.02 + Math.random() * 0.035;
        }}
        particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
        const particleMaterial = new THREE.PointsMaterial({{
            color: 0xf97316,
            size: 0.35,
            transparent: true,
            opacity: 0.75,
            blending: THREE.AdditiveBlending
        }});
        const emberParticles = new THREE.Points(particleGeometry, particleMaterial);
        scene.add(emberParticles);

        // --- 4. Central Citadel Platform & Magma Veins ---
        const citadelGeo = new THREE.CylinderGeometry(23, 25, 2, 40);
        const citadelMat = new THREE.MeshStandardMaterial({{
            color: 0x0f172a,
            roughness: 0.75,
            metalness: 0.3
        }});
        const citadel = new THREE.Mesh(citadelGeo, citadelMat);
        citadel.position.y = -1.5;
        citadel.receiveShadow = true;
        scene.add(citadel);

        // Molten ring
        const lavaRingGeo = new THREE.TorusGeometry(22, 0.45, 16, 60);
        const lavaRingMat = new THREE.MeshBasicMaterial({{ color: 0xea580c }});
        const lavaRing = new THREE.Mesh(lavaRingGeo, lavaRingMat);
        lavaRing.rotation.x = Math.PI / 2;
        lavaRing.position.y = -0.4;
        scene.add(lavaRing);

        // --- 5. Five Workstation Islands ---
        const stationCoords = [
            {{ x: -16, y: 0, z: 2, name: "Vulcan", color: 0xf97316 }},
            {{ x: -8,  y: 0, z: -3, name: "Gildor", color: 0x10b981 }},
            {{ x: 0,   y: 0, z: -5, name: "Brog",   color: 0x38bdf8 }},
            {{ x: 8,   y: 0, z: -3, name: "Pyra",   color: 0xec4899 }},
            {{ x: 16,  y: 0, z: 2, name: "Hermes", color: 0xeab308 }}
        ];

        const stationGroups = [];
        const islandPlates = [];

        stationCoords.forEach((st, idx) => {{
            const group = new THREE.Group();
            group.position.set(st.x, st.y, st.z);

            // Island base pedestal
            const baseGeo = new THREE.CylinderGeometry(3.2, 3.8, 1.2, 24);
            const baseMat = new THREE.MeshStandardMaterial({{
                color: 0x1e293b,
                roughness: 0.5,
                metalness: 0.4
            }});
            const baseMesh = new THREE.Mesh(baseGeo, baseMat);
            baseMesh.position.y = 0.6;
            baseMesh.receiveShadow = true;
            group.add(baseMesh);

            // Glowing ring on pedestal
            const ringGeo = new THREE.TorusGeometry(3.0, 0.12, 12, 32);
            const ringMat = new THREE.MeshBasicMaterial({{ color: st.color }});
            const ringMesh = new THREE.Mesh(ringGeo, ringMat);
            ringMesh.rotation.x = Math.PI / 2;
            ringMesh.position.y = 1.25;
            group.add(ringMesh);

            // Island light
            const light = new THREE.PointLight(st.color, 0.8, 8);
            light.position.set(0, 3, 0);
            group.add(light);

            scene.add(group);
            stationGroups.push({{ group, light, ringMesh, coords: st }});
        }});

        // --- 6. Energy Rails connecting Station 1 to 5 ---
        for (let i = 0; i < stationCoords.length - 1; i++) {{
            const p1 = stationCoords[i];
            const p2 = stationCoords[i + 1];

            const curve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(p1.x, 1.2, p1.z),
                new THREE.Vector3((p1.x + p2.x) / 2, 2.0, (p1.z + p2.z) / 2),
                new THREE.Vector3(p2.x, 1.2, p2.z)
            ]);

            const tubeGeo = new THREE.TubeGeometry(curve, 20, 0.1, 8, false);
            const tubeMat = new THREE.MeshBasicMaterial({{
                color: 0xf97316,
                transparent: true,
                opacity: 0.65
            }});
            const tube = new THREE.Mesh(tubeGeo, tubeMat);
            scene.add(tube);
        }}

        // --- 7. The 5 Animated Tiny Creatures ---
        const creatures = [];

        // Creature 1: Vulcan (Smelter Golem) - Station 1
        (function buildVulcan() {{
            const stGroup = stationGroups[0].group;
            const cGroup = new THREE.Group();
            cGroup.position.set(0, 1.3, 0);

            // Heavy basalt body
            const bodyGeo = new THREE.DodecahedronGeometry(1.2, 0);
            const bodyMat = new THREE.MeshStandardMaterial({{ color: 0x78350f, roughness: 0.7 }});
            const body = new THREE.Mesh(bodyGeo, bodyMat);
            body.position.y = 1.3;
            cGroup.add(body);

            // Fiery core
            const eyeGeo = new THREE.SphereGeometry(0.2, 8, 8);
            const eyeMat = new THREE.MeshBasicMaterial({{ color: 0xf97316 }});
            const eye = new THREE.Mesh(eyeGeo, eyeMat);
            eye.position.set(0, 1.6, 0.9);
            cGroup.add(eye);

            // Smelter crucible in front
            const potGeo = new THREE.CylinderGeometry(0.9, 0.7, 0.9, 16);
            const potMat = new THREE.MeshStandardMaterial({{ color: 0x27272a, roughness: 0.4 }});
            const pot = new THREE.Mesh(potGeo, potMat);
            pot.position.set(0, 0.45, 1.4);
            cGroup.add(pot);

            // Lava inside pot
            const lavaGeo = new THREE.CircleGeometry(0.85, 16);
            const lavaMat = new THREE.MeshBasicMaterial({{ color: 0xea580c }});
            const lava = new THREE.Mesh(lavaGeo, lavaMat);
            lava.rotation.x = -Math.PI / 2;
            lava.position.set(0, 0.91, 1.4);
            cGroup.add(lava);

            stGroup.add(cGroup);
            creatures.push({{ group: cGroup, type: "vulcan", basePos: cGroup.position.clone() }});
        }})();

        // Creature 2: Gildor (Dialect Imp) - Station 2
        (function buildGildor() {{
            const stGroup = stationGroups[1].group;
            const cGroup = new THREE.Group();
            cGroup.position.set(0, 2.0, 0);

            // Slender emerald body
            const bodyGeo = new THREE.OctahedronGeometry(0.8, 0);
            const bodyMat = new THREE.MeshStandardMaterial({{ color: 0x059669, roughness: 0.3, metalness: 0.4 }});
            const body = new THREE.Mesh(bodyGeo, bodyMat);
            cGroup.add(body);

            // Scanning lens ring
            const lensGeo = new THREE.TorusGeometry(0.9, 0.08, 8, 24);
            const lensMat = new THREE.MeshBasicMaterial({{ color: 0x34d399 }});
            const lens = new THREE.Mesh(lensGeo, lensMat);
            lens.position.set(0, 0, 0.8);
            cGroup.add(lens);

            // Wings
            const wingGeo = new THREE.PlaneGeometry(1.2, 0.6);
            const wingMat = new THREE.MeshBasicMaterial({{ color: 0x6ee7b7, side: THREE.DoubleSide, transparent: true, opacity: 0.7 }});
            const leftWing = new THREE.Mesh(wingGeo, wingMat);
            leftWing.position.set(-0.9, 0.2, -0.3);
            leftWing.rotation.y = -Math.PI / 4;
            cGroup.add(leftWing);

            const rightWing = leftWing.clone();
            rightWing.position.set(0.9, 0.2, -0.3);
            rightWing.rotation.y = Math.PI / 4;
            cGroup.add(rightWing);

            stGroup.add(cGroup);
            creatures.push({{ group: cGroup, type: "gildor", leftWing, rightWing, lens, basePos: cGroup.position.clone() }});
        }})();

        // Creature 3: Brog (Blacksmith Dwarf) - Station 3
        (function buildBrog() {{
            const stGroup = stationGroups[2].group;
            const cGroup = new THREE.Group();
            cGroup.position.set(0, 1.2, 0);

            // Dwarf torso & helmet
            const torsoGeo = new THREE.CylinderGeometry(0.7, 0.8, 1.3, 8);
            const torsoMat = new THREE.MeshStandardMaterial({{ color: 0x475569, metalness: 0.8, roughness: 0.3 }});
            const torso = new THREE.Mesh(torsoGeo, torsoMat);
            torso.position.y = 0.8;
            cGroup.add(torso);

            // Helmet with horns
            const helmGeo = new THREE.ConeGeometry(0.8, 0.7, 8);
            const helmMat = new THREE.MeshStandardMaterial({{ color: 0x94a3b8, metalness: 0.9 }});
            const helm = new THREE.Mesh(helmGeo, helmMat);
            helm.position.y = 1.7;
            cGroup.add(helm);

            // Iron Anvil in front
            const anvilBaseGeo = new THREE.BoxGeometry(1.6, 0.8, 1.0);
            const anvilMat = new THREE.MeshStandardMaterial({{ color: 0x1e293b, metalness: 0.9, roughness: 0.2 }});
            const anvil = new THREE.Mesh(anvilBaseGeo, anvilMat);
            anvil.position.set(0, 0.4, 1.4);
            cGroup.add(anvil);

            // Hammer arm
            const armGroup = new THREE.Group();
            armGroup.position.set(0.8, 1.2, 0.3);
            const handleGeo = new THREE.CylinderGeometry(0.08, 0.08, 1.4);
            const handleMat = new THREE.MeshStandardMaterial({{ color: 0xb45309 }});
            const handle = new THREE.Mesh(handleGeo, handleMat);
            handle.position.y = 0.5;
            armGroup.add(handle);

            const hammerHeadGeo = new THREE.BoxGeometry(0.5, 0.5, 0.8);
            const hammerHeadMat = new THREE.MeshStandardMaterial({{ color: 0x38bdf8, metalness: 0.9 }});
            const hammerHead = new THREE.Mesh(hammerHeadGeo, hammerHeadMat);
            hammerHead.position.set(0, 1.2, 0);
            armGroup.add(hammerHead);

            cGroup.add(armGroup);
            stGroup.add(cGroup);
            creatures.push({{ group: cGroup, type: "brog", armGroup, basePos: cGroup.position.clone() }});
        }})();

        // Creature 4: Pyra (Urgency Sprite) - Station 4
        (function buildPyra() {{
            const stGroup = stationGroups[3].group;
            const cGroup = new THREE.Group();
            cGroup.position.set(0, 2.0, 0);

            // Glowing fairy core
            const coreGeo = new THREE.IcosahedronGeometry(0.7, 0);
            const coreMat = new THREE.MeshStandardMaterial({{ color: 0xec4899, roughness: 0.2, metalness: 0.8 }});
            const core = new THREE.Mesh(coreGeo, coreMat);
            cGroup.add(core);

            // Gyroscopic Ring 1
            const ring1Geo = new THREE.TorusGeometry(1.2, 0.06, 8, 32);
            const ring1Mat = new THREE.MeshBasicMaterial({{ color: 0xf43f5e }});
            const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
            cGroup.add(ring1);

            // Gyroscopic Ring 2
            const ring2Geo = new THREE.TorusGeometry(1.5, 0.06, 8, 32);
            const ring2Mat = new THREE.MeshBasicMaterial({{ color: 0xfbbf24 }});
            const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
            cGroup.add(ring2);

            stGroup.add(cGroup);
            creatures.push({{ group: cGroup, type: "pyra", ring1, ring2, core, basePos: cGroup.position.clone() }});
        }})();

        // Creature 5: Hermes (Dispatch Automaton) - Station 5
        (function buildHermes() {{
            const stGroup = stationGroups[4].group;
            const cGroup = new THREE.Group();
            cGroup.position.set(0, 1.8, 0);

            // Clockwork brass body
            const bodyGeo = new THREE.CylinderGeometry(0.6, 0.4, 1.5, 6);
            const bodyMat = new THREE.MeshStandardMaterial({{ color: 0xd97706, metalness: 0.9, roughness: 0.2 }});
            const body = new THREE.Mesh(bodyGeo, bodyMat);
            cGroup.add(body);

            // Antenna
            const antGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.9);
            const antMat = new THREE.MeshBasicMaterial({{ color: 0xfef08a }});
            const ant = new THREE.Mesh(antGeo, antMat);
            ant.position.y = 1.2;
            cGroup.add(ant);

            // Upward beacon column
            const beamGeo = new THREE.CylinderGeometry(0.4, 0.8, 12, 16);
            const beamMat = new THREE.MeshBasicMaterial({{
                color: 0xfacc15,
                transparent: true,
                opacity: 0.35,
                side: THREE.DoubleSide
            }});
            const beam = new THREE.Mesh(beamGeo, beamMat);
            beam.position.y = 6.0;
            cGroup.add(beam);

            stGroup.add(cGroup);
            creatures.push({{ group: cGroup, type: "hermes", ant, beam, basePos: cGroup.position.clone() }});
        }})();

        // --- 8. The Traveling Prompt Packet Crystal ---
        const packetGeo = new THREE.IcosahedronGeometry(0.7, 0);
        const packetMat = new THREE.MeshStandardMaterial({{
            color: 0x38bdf8,
            emissive: 0x0284c7,
            roughness: 0.1,
            metalness: 0.9
        }});
        const promptPacket = new THREE.Mesh(packetGeo, packetMat);
        promptPacket.castShadow = true;
        scene.add(promptPacket);

        const packetLight = new THREE.PointLight(0x38bdf8, 1.8, 12);
        promptPacket.add(packetLight);

        // Position crystal initially at Hermes (Station 5) or chosen active station
        let currentStep = {active_state};
        let isPlaying = false;
        let playTimer = null;

        function setPacketStation(idx, animate = true) {{
            currentStep = Math.max(1, Math.min(5, idx));
            const targetCoord = stationCoords[currentStep - 1];
            const targetPos = new THREE.Vector3(targetCoord.x, 3.2, targetCoord.z);

            if (!animate) {{
                promptPacket.position.copy(targetPos);
            }}

            // Update HUD
            const sInfo = steps[currentStep - 1];
            document.getElementById('hud-station-tag').innerText = `Station ${{sInfo.step}}: ${{sInfo.station}}`;
            document.getElementById('hud-creature-tag').innerText = `${{sInfo.creature}} the ${{sInfo.title}}`;
            document.getElementById('hud-production-tag').innerText = sInfo.production;
            document.getElementById('step-counter').innerText = `Step ${{currentStep}} of 5`;

            // Active button state
            const buttons = document.querySelectorAll('.hud-bottom .hud-btn');
            buttons.forEach(b => {{
                if (b.innerText.startsWith(`S${{currentStep}}:`)) {{
                    b.classList.add('active');
                }} else if (b.innerText.startsWith('S')) {{
                    b.classList.remove('active');
                }}
            }});

            // Highlight ring
            stationGroups.forEach((stg, i) => {{
                stg.light.intensity = (i === currentStep - 1) ? 2.5 : 0.6;
                stg.ringMesh.scale.setScalar(i === currentStep - 1 ? 1.25 : 1.0);
            }});
        }}

        setPacketStation(currentStep, false);

        window.jumpToStation = function(idx) {{
            setPacketStation(idx, true);
        }};

        document.getElementById('btn-next').onclick = () => {{
            setPacketStation(currentStep === 5 ? 1 : currentStep + 1);
        }};
        document.getElementById('btn-prev').onclick = () => {{
            setPacketStation(currentStep === 1 ? 5 : currentStep - 1);
        }};
        document.getElementById('btn-reset').onclick = () => {{
            setPacketStation(1);
        }};
        document.getElementById('btn-play').onclick = function() {{
            isPlaying = !isPlaying;
            this.innerText = isPlaying ? "⏸ Pause" : "▶ Play All";
            if (isPlaying) {{
                playTimer = setInterval(() => {{
                    if (currentStep < 5) {{
                        setPacketStation(currentStep + 1);
                    }} else {{
                        setPacketStation(1);
                    }}
                }}, 1800);
            }} else {{
                clearInterval(playTimer);
            }}
        }};

        // --- 9. Animation Render Loop ---
        let clock = new THREE.Clock();

        function animate() {{
            requestAnimationFrame(animate);
            const delta = clock.getDelta();
            const time = clock.getElapsedTime();

            // OrbitControls update
            controls.update();

            // Embers drift upwards
            const positions = emberParticles.geometry.attributes.position.array;
            for (let i = 0; i < particleCount; i++) {{
                positions[i * 3 + 1] += particleSpeeds[i];
                if (positions[i * 3 + 1] > 20) {{
                    positions[i * 3 + 1] = -4;
                }}
            }}
            emberParticles.geometry.attributes.position.needsUpdate = true;

            // Prompt Packet smooth lerp to current station
            const targetCoord = stationCoords[currentStep - 1];
            const targetY = 3.0 + Math.sin(time * 3.5) * 0.4;
            promptPacket.position.x += (targetCoord.x - promptPacket.position.x) * 0.08;
            promptPacket.position.z += (targetCoord.z - promptPacket.position.z) * 0.08;
            promptPacket.position.y += (targetY - promptPacket.position.y) * 0.08;
            promptPacket.rotation.x += 0.02;
            promptPacket.rotation.y += 0.03;

            // Animate creatures
            creatures.forEach((c) => {{
                if (c.type === "vulcan") {{
                    c.group.position.y = c.basePos.y + Math.sin(time * 2.0) * 0.1;
                }} else if (c.type === "gildor") {{
                    c.group.position.y = c.basePos.y + Math.sin(time * 3.0) * 0.25;
                    c.leftWing.rotation.z = Math.sin(time * 12.0) * 0.4;
                    c.rightWing.rotation.z = -Math.sin(time * 12.0) * 0.4;
                    c.lens.rotation.z += 0.03;
                }} else if (c.type === "brog") {{
                    // Brog hammer swing
                    const swing = Math.sin(time * 4.0);
                    c.armGroup.rotation.x = swing > 0.3 ? swing * 0.9 : 0;
                }} else if (c.type === "pyra") {{
                    c.ring1.rotation.x += 0.04;
                    c.ring1.rotation.y += 0.03;
                    c.ring2.rotation.y += 0.05;
                    c.group.position.y = c.basePos.y + Math.cos(time * 3.0) * 0.2;
                }} else if (c.type === "hermes") {{
                    c.beam.rotation.y += 0.02;
                    c.ant.rotation.y += 0.06;
                }}
            }});

            renderer.render(scene, camera);
        }}

        animate();

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
</body>
</html>"""
    return html_code
