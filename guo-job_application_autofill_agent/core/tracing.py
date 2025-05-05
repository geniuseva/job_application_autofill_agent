import logging
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor


# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Phoenix tracing
def init_phoenix():
    """Initialize Phoenix tracing"""
    try:
        tracer_provider = register(
            project_name="my_project",
            endpoint="http://127.0.0.1:6006/v1/traces",
            auto_instrument=False
        )
        tracer = tracer_provider.get_tracer(__name__)
        return tracer_provider, tracer
    except Exception as e:
        logger.warning(f"Failed to initialize Phoenix: {e}")
        logger.warning("Continuing without telemetry...")
        return None, None

# Initialize tracer at module level so it can be imported by other modules
tracer_provider, tracer = init_phoenix()