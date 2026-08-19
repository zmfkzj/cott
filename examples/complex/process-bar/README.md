# process-bar

## Purpose
Show a flow that separates byte-payload validation, processing, and output assembly while preserving original metadata.

## Key points
- The Cott contract rejects empty bytes with `InvalidPayload`, then constructs output containing the original size and type after the byte-processing stage with network effects.
- The current Python binding's `process_payload_bytes` returns the bytes unchanged, and `process_bar` likewise only checks empty input before making output from the input bytes and metadata.
