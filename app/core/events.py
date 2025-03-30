from shared_architecture.utils.service_helpers import connection_manager

async def startup_event():
    connection_manager.initialize()

async def shutdown_event():
    connection_manager.close()