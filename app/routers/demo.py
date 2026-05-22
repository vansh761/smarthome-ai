from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Demo"])


@router.get("/demo", response_class=HTMLResponse)
def demo_page():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Smart Home Intelligence System</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #0f0f0f; color: #fff; }
            h1 { color: #1D9E75; }
            h2 { color: #60A5FA; margin-top: 30px; }
            .endpoint { background: #1a1a1a; padding: 10px 15px; border-radius: 8px; margin: 8px 0; border-left: 3px solid #1D9E75; }
            .tag { background: #1D9E75; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            a { color: #60A5FA; }
            .stat { display: inline-block; background: #1a1a1a; padding: 10px 20px; border-radius: 8px; margin: 5px; text-align: center; }
            .stat-n { font-size: 24px; font-weight: bold; color: #1D9E75; }
            .stat-l { font-size: 12px; color: #888; }
        </style>
    </head>
    <body>
        <h1>AI Smart Home Intelligence System</h1>
        <p>Privacy-first predictive well-being platform for Indian homes.</p>

        <div>
            <div class="stat"><div class="stat-n">23</div><div class="stat-l">Languages</div></div>
            <div class="stat"><div class="stat-n">20</div><div class="stat-l">Health Conditions</div></div>
            <div class="stat"><div class="stat-n">30+</div><div class="stat-l">API Endpoints</div></div>
            <div class="stat"><div class="stat-n">₹0</div><div class="stat-l">Hardware Needed</div></div>
        </div>

        <h2>Quick Test — Try it now</h2>

        <div class="endpoint">
            <span class="tag">GET</span>
            <a href="/weather/place?name=Delhi">/weather/place?name=Delhi</a>
            — Real weather for any Indian city, village, or colony
        </div>
        <div class="endpoint">
            <span class="tag">GET</span>
            <a href="/sleep/optimal">/sleep/optimal</a>
            — Research-backed optimal sleep environment
        </div>
        <div class="endpoint">
            <span class="tag">GET</span>
            <a href="/evaluation/benchmark">/evaluation/benchmark</a>
            — System benchmark and honest accuracy claims
        </div>
        <div class="endpoint">
            <span class="tag">GET</span>
            <a href="/automation/modes">/automation/modes</a>
            — Manual / Assisted / Full AI modes
        </div>
        <div class="endpoint">
            <span class="tag">GET</span>
            <a href="/transparency/principles">/transparency/principles</a>
            — Ethical AI principles
        </div>

        <h2>Full API Documentation</h2>
        <p><a href="/docs">Interactive API Docs (Swagger UI)</a></p>
        <p><a href="/redoc">ReDoc Documentation</a></p>

        <h2>Source Code</h2>
        <p>GitHub repository link here after publishing</p>
    </body>
    </html>
    """