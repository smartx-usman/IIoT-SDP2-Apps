from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def setup_tracer(service_name, trace_agent_host, trace_agent_port, trace_sampling_rate):
    resource = Resource(attributes={SERVICE_NAME: service_name})
    exporter = OTLPSpanExporter(endpoint=f"{trace_agent_host}:{trace_agent_port}", insecure=True)
    sampler = TraceIdRatioBased(1 / trace_sampling_rate)

    provider = TracerProvider(resource=resource, sampler=sampler)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(__name__)
