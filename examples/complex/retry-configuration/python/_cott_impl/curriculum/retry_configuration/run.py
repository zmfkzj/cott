from curriculum.retry_configuration_types import RetryConfiguration, RetryCount


def run() -> RetryConfiguration:
    return RetryConfiguration(attempts=RetryCount(value=3), backoff_ms=250)
