Q1 661ff29 ; STRATA_ADAPT_OVERLAP=1
Q2 retracted -23 %/-27 % (unpinned); pinned: 0.1.44.1 -8.3 %/-14.0 %, 0.1.45 dual-ON -7.5 %/-13.6 %
Q3 +22.6 % (78.6 -> 96.4 tok/s); numa.nodeAffinity, numa.vcpu.preferHT
Q4 #30637: 50/50 SLRU replaces LRU; lands from b11732; 1-5 % better
Q5 first-request TTFT 10 s -> 60 s+; our 64-token warmup would absorb it
Q6 --build does NOT clear it; the refusal is a capability check on the engine
Q7 Vulkan (VK=1) gave 115.6-117.6 prompt / 48.5 decode; CUDA gave 28.4-28.5 / 8.9-9.5
Q8 NO - Q4_K is not named; the reply names IQ4_NL, Q6_K, IQ2_S
Q9 engine 0.1.45.3; verify round of 4 tokens 13.70 -> 12.23 ms with the same text
