from aiohttp import web
import os

async def health_check(request):
    return web.Response(text="OK")

def create_health_app():
    app = web.Application()
    app.router.add_get('/health', health_check)
    return app

async def start_health_server():
    app = create_health_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Health check server running on port 8080")
