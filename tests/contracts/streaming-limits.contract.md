# Contract: Streaming & Limits (R11-R12)

## Scenarios
1. Stream emits progressive content events and terminal completion event.
2. Client reconnect with prior event reference does not duplicate rendered message.
3. Daily quota exceeded returns limit response with reset reference.
4. Per-minute rate exceeded returns throttling response.
5. Exceeding concurrent stream cap returns bounded refusal response.
6. Idle stream timeout closes connection predictably.

## Validation Goals
- Потоковые контракты устойчивы к сетевым разрывам.
- Лимиты не приводят к неоднозначному состоянию клиента.
