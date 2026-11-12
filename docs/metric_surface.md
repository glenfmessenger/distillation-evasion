# vLLM metric surface (M1, observed 2026-11-10)

Scraped from `/metrics` on vLLM 0.33.0 serving Qwen/Qwen3-8B with the launch flags in
docs/environment.md. Cold = after startup, before any chat request (health checks only). Warm =
after the two smoke requests. Raw scrapes: docs/evidence/m1/m1_metrics/{cold,warm}.txt.

- Families (TYPE lines): cold 88, warm 92.
- Families that appear only after traffic: http_request_duration_seconds_created, http_request_size_bytes_created, http_requests_created, http_response_size_bytes_created.
- All `vllm:` families were already declared cold on this version; only the HTTP-layer
  `_created` timestamp families were added by traffic. The charter's warning (cold scrape
  under-reports) held for the HTTP families only. Per-request fields used by the detectors
  (`usage.*`) come from the chat response, not from this endpoint.

## Per-request fields verified in the chat response (smoke, docs/evidence/m1/smoke_records.jsonl)

| Field | Source | Observed |
|---|---|---|
| prompt_tokens / completion_tokens / total_tokens | usage | 270 / 1024 / 1294 on both requests; identity held |
| completion_tokens_details.reasoning_tokens | usage (qwen3 parser) | 1023 on both (thinking request, finish=length at max_tokens=1024) |
| prompt_tokens_details.cached_tokens | usage (prompt-token details on) | 0 on first request, 256 on the repeated-prefix request |
| TTFB (client monotonic) | client | 48 ms then 24 ms |

## `vllm:` families (72)

- `vllm:admission_rejections_created` (gauge, 2 samples warm)
- `vllm:admission_rejections_total` (counter, 2 samples warm)
- `vllm:cache_config_info` (gauge, 1 samples warm)
- `vllm:e2e_request_latency_seconds` (histogram, 24 samples warm)
- `vllm:e2e_request_latency_seconds_created` (gauge, 1 samples warm)
- `vllm:engine_sleep_state` (gauge, 3 samples warm)
- `vllm:estimated_flops_per_gpu_created` (gauge, 1 samples warm)
- `vllm:estimated_flops_per_gpu_total` (counter, 1 samples warm)
- `vllm:estimated_read_bytes_per_gpu_created` (gauge, 1 samples warm)
- `vllm:estimated_read_bytes_per_gpu_total` (counter, 1 samples warm)
- `vllm:estimated_write_bytes_per_gpu_created` (gauge, 1 samples warm)
- `vllm:estimated_write_bytes_per_gpu_total` (counter, 1 samples warm)
- `vllm:external_prefix_cache_hits_created` (gauge, 1 samples warm)
- `vllm:external_prefix_cache_hits_total` (counter, 1 samples warm)
- `vllm:external_prefix_cache_queries_created` (gauge, 1 samples warm)
- `vllm:external_prefix_cache_queries_total` (counter, 1 samples warm)
- `vllm:generation_tokens_created` (gauge, 1 samples warm)
- `vllm:generation_tokens_total` (counter, 1 samples warm)
- `vllm:inter_token_latency_seconds` (histogram, 22 samples warm)
- `vllm:inter_token_latency_seconds_created` (gauge, 1 samples warm)
- `vllm:iteration_tokens_total` (histogram, 16 samples warm)
- `vllm:iteration_tokens_total_created` (gauge, 1 samples warm)
- `vllm:kv_cache_usage_perc` (gauge, 1 samples warm)
- `vllm:mm_cache_hits_created` (gauge, 1 samples warm)
- `vllm:mm_cache_hits_total` (counter, 1 samples warm)
- `vllm:mm_cache_queries_created` (gauge, 1 samples warm)
- `vllm:mm_cache_queries_total` (counter, 1 samples warm)
- `vllm:num_preemptions_created` (gauge, 1 samples warm)
- `vllm:num_preemptions_total` (counter, 1 samples warm)
- `vllm:num_requests_running` (gauge, 1 samples warm)
- `vllm:num_requests_waiting` (gauge, 1 samples warm)
- `vllm:num_requests_waiting_by_reason` (gauge, 2 samples warm)
- `vllm:prefix_cache_hits_created` (gauge, 1 samples warm)
- `vllm:prefix_cache_hits_total` (counter, 1 samples warm)
- `vllm:prefix_cache_queries_created` (gauge, 1 samples warm)
- `vllm:prefix_cache_queries_total` (counter, 1 samples warm)
- `vllm:prompt_tokens_by_source_created` (gauge, 3 samples warm)
- `vllm:prompt_tokens_by_source_total` (counter, 3 samples warm)
- `vllm:prompt_tokens_cached_by_source_created` (gauge, 5 samples warm)
- `vllm:prompt_tokens_cached_by_source_total` (counter, 5 samples warm)
- `vllm:prompt_tokens_cached_created` (gauge, 1 samples warm)
- `vllm:prompt_tokens_cached_total` (counter, 1 samples warm)
- `vllm:prompt_tokens_created` (gauge, 1 samples warm)
- `vllm:prompt_tokens_total` (counter, 1 samples warm)
- `vllm:request_decode_time_seconds` (histogram, 24 samples warm)
- `vllm:request_decode_time_seconds_created` (gauge, 1 samples warm)
- `vllm:request_generation_tokens` (histogram, 16 samples warm)
- `vllm:request_generation_tokens_created` (gauge, 1 samples warm)
- `vllm:request_inference_time_seconds` (histogram, 24 samples warm)
- `vllm:request_inference_time_seconds_created` (gauge, 1 samples warm)
- `vllm:request_max_num_generation_tokens` (histogram, 16 samples warm)
- `vllm:request_max_num_generation_tokens_created` (gauge, 1 samples warm)
- `vllm:request_num_preemptions` (histogram, 10 samples warm)
- `vllm:request_num_preemptions_created` (gauge, 1 samples warm)
- `vllm:request_params_max_tokens` (histogram, 16 samples warm)
- `vllm:request_params_max_tokens_created` (gauge, 1 samples warm)
- `vllm:request_params_n` (histogram, 8 samples warm)
- `vllm:request_params_n_created` (gauge, 1 samples warm)
- `vllm:request_prefill_kv_computed_tokens` (histogram, 16 samples warm)
- `vllm:request_prefill_kv_computed_tokens_created` (gauge, 1 samples warm)
- `vllm:request_prefill_time_seconds` (histogram, 24 samples warm)
- `vllm:request_prefill_time_seconds_created` (gauge, 1 samples warm)
- `vllm:request_prompt_tokens` (histogram, 16 samples warm)
- `vllm:request_prompt_tokens_created` (gauge, 1 samples warm)
- `vllm:request_queue_time_seconds` (histogram, 24 samples warm)
- `vllm:request_queue_time_seconds_created` (gauge, 1 samples warm)
- `vllm:request_success_created` (gauge, 5 samples warm)
- `vllm:request_success_total` (counter, 5 samples warm)
- `vllm:request_time_per_output_token_seconds` (histogram, 22 samples warm)
- `vllm:request_time_per_output_token_seconds_created` (gauge, 1 samples warm)
- `vllm:time_to_first_token_seconds` (histogram, 25 samples warm)
- `vllm:time_to_first_token_seconds_created` (gauge, 1 samples warm)

## Other families (20)

- `http_request_duration_highr_seconds` (histogram, 24 samples warm)
- `http_request_duration_highr_seconds_created` (gauge, 1 samples warm)
- `http_request_duration_seconds` (histogram, 6 samples warm)
- `http_request_duration_seconds_created` (gauge, 1 samples warm)
- `http_request_size_bytes` (summary, 2 samples warm)
- `http_request_size_bytes_created` (gauge, 1 samples warm)
- `http_requests_created` (gauge, 1 samples warm)
- `http_requests_total` (counter, 1 samples warm)
- `http_response_size_bytes` (summary, 2 samples warm)
- `http_response_size_bytes_created` (gauge, 1 samples warm)
- `process_cpu_seconds_total` (counter, 1 samples warm)
- `process_max_fds` (gauge, 1 samples warm)
- `process_open_fds` (gauge, 1 samples warm)
- `process_resident_memory_bytes` (gauge, 1 samples warm)
- `process_start_time_seconds` (gauge, 1 samples warm)
- `process_virtual_memory_bytes` (gauge, 1 samples warm)
- `python_gc_collections_total` (counter, 3 samples warm)
- `python_gc_objects_collected_total` (counter, 3 samples warm)
- `python_gc_objects_uncollectable_total` (counter, 3 samples warm)
- `python_info` (gauge, 1 samples warm)
