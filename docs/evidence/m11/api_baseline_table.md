API baseline (ServeGen per-client traces, ten-minute windows). Language tiers pooled: 314 clients, 2909 client-days, 246319 windows with >= 10 requests.
Hourly rate: per-client busiest hour quantiles {"10": 5990, "50": 44306, "90": 336157, "99": 2571937}; share of clients over the chat threshold of 26: 99.68%; 1% client-day threshold 2,760,839 requests an hour (29 exceedances); one account would need 0.00 h for 2000 requests; campaign in one hour flagged: False. P55 holds.
Cadence: CV quantiles over active windows {"1": 0.272, "5": 0.695, "25": 1.012, "50": 1.23, "75": 2.265, "95": 8.861}; 1% low-side threshold 0.272; share of windows below 0.305: 1.41%, below 0.20: 0.38%; share of clients whose median is below 0.305: 0.64%, below 0.20: 0.00%. P56 holds.

| Set | Clients | Client-days | Busiest hour p50 / p90 / p99 | Over 26 | 1% client-day thr | Active windows | CV p1 / p5 / p50 | Below 0.305 | Below 0.20 |
|---|---|---|---|---|---|---|---|---|---|
| m-large | 162 | 1396 | 23,279 / 116,230 / 934,283 | 1.00 | 484,992 | 99839 | 0.22 / 0.42 / 1.17 | 0.029 | 0.007 |
| m-mid | 109 | 1119 | 110,258 / 459,461 / 2,606,952 | 0.99 | 3,786,981 | 106385 | 0.61 / 0.90 / 1.32 | 0.003 | 0.000 |
| m-small | 43 | 394 | 100,780 / 506,499 / 4,323,693 | 1.00 | 3,242,498 | 40095 | 0.50 / 0.93 / 1.21 | 0.006 | 0.004 |
| deepseek-r1 | 73 | 73 | 1,251 / 17,715 / 46,828 | 1.00 | 47,449 | 3111 | 0.51 / 0.72 / 1.03 | 0.002 | 0.000 |
