import time
import logging


def process_message(message, store, tracer, action_generator, table_valid, table_invalid, valid_range, datastore):
    with tracer.start_as_current_span("analyzer") as span:
        try:
            start = time.perf_counter()
            trace_id = format(span.get_span_context().trace_id, "032x")
            process_ts = int(time.time())

            temperature = int(message['temperature'])
            humidity = float(message['humidity'])
            reading_ts = int(str(message['measurement_ts'])[:-3])

            if temperature < valid_range[0] or temperature > valid_range[1]:
                with tracer.start_as_current_span("store") as s:
                    s.set_attribute('store_name', datastore)
                    store.store_data(
                        table=table_invalid,
                        reading_ts=reading_ts,
                        process_ts=process_ts,
                        sensor=message['sensor'],
                        temperature=temperature,
                        humidity=humidity
                    )
                    logging.warning(f"Anomalous data: {temperature} from {message['sensor']}, trace_id={trace_id}")
            else:
                action_generator.get_actuator_action(message['sensor'], temperature, reading_ts)
                with tracer.start_as_current_span("store") as s:
                    s.set_attribute('store_name', datastore)
                    store.store_data(
                        table=table_valid,
                        reading_ts=reading_ts,
                        process_ts=process_ts,
                        sensor=message['sensor'],
                        temperature=temperature,
                        humidity=humidity
                    )
                    logging.info(f"Normal data: {temperature} from {message['sensor']}, trace_id={trace_id}")

        except Exception as e:
            logging.error(f"Error processing message from {message['sensor']}: {str(e)}")

        end = time.perf_counter()
        duration = round((end - start) * 1000, 4)
        log_level = logging.error if duration > 20 else logging.warning if duration > 15 else logging.info
        log_level(f"Processing time: {duration}ms, sensor={message['sensor']}, trace_id={trace_id}")
        span.set_attribute('sensor', message['sensor'])
        span.set_attribute('processing_time', duration)
