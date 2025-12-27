# OpenAI Agents SDK Reference

> Context7을 통해 수집한 OpenAI Agent Builder 및 Agents SDK 공식 문서 정리

## 목차
1. [개요](#개요)
2. [핵심 개념](#핵심-개념)
3. [Python SDK](#python-sdk)
4. [JavaScript/TypeScript SDK](#javascripttypescript-sdk)
5. [Agent Builder (Visual Canvas)](#agent-builder-visual-canvas)
6. [Swarm (Legacy)](#swarm-legacy)

---

## 개요

### OpenAI Agents SDK란?

OpenAI Agents SDK는 **멀티 에이전트 워크플로우**를 구축하기 위한 경량화된 프레임워크입니다.

**핵심 특징:**
- **Agents**: 지시사항(instructions)과 도구(tools)로 구성된 LLM
- **Handoffs**: 에이전트 간 제어 전환을 위한 특수 도구 호출
- **Guardrails**: 입/출력 유효성 검사를 위한 안전장치
- **Tracing**: 에이전트 실행 추적, 디버깅, 최적화

**지원 플랫폼:**
- Python 3.9+
- Node.js 22+, Deno, Bun
- 브라우저 (Voice Agents)

---

## 핵심 개념

### 1. Agent (에이전트)

에이전트는 지시사항, 도구, 가드레일, 핸드오프가 설정된 LLM입니다.

```python
# Python
from agents import Agent

agent = Agent(
    name="Assistant",
    instructions="You are a helpful assistant.",
    tools=[...],
    handoffs=[...],
    model="gpt-4.1",
)
```

```typescript
// TypeScript
import { Agent } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
  tools: [...],
  handoffs: [...],
  model: 'gpt-4o',
});
```

### 2. Handoffs (핸드오프)

에이전트가 다른 에이전트에게 대화를 위임하는 메커니즘입니다.

```python
# Python - 기본 핸드오프
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

triage_agent = Agent(
    name="Triage agent",
    handoffs=[billing_agent, handoff(refund_agent)]
)
```

```typescript
// TypeScript - 커스텀 핸드오프
import { Agent, handoff } from '@openai/agents';
import { z } from 'zod';

const handoffObj = handoff(agent, {
  onHandoff: (ctx, input) => console.log('Handoff:', input),
  inputType: z.object({ reason: z.string() }),
  toolNameOverride: 'transfer_to_specialist',
});
```

### 3. Tools (도구)

에이전트가 외부 기능을 호출할 수 있게 하는 함수입니다.

```python
# Python
from agents import Agent, function_tool

@function_tool
async def get_weather(city: str) -> str:
    """Get weather for a city"""
    return f"Weather in {city}: Sunny, 72°F"

agent = Agent(
    name="Weather Agent",
    tools=[get_weather],
)
```

```typescript
// TypeScript
import { tool } from '@openai/agents';
import { z } from 'zod';

const getWeatherTool = tool({
  name: 'get_weather',
  description: 'Get the weather for a city',
  parameters: z.object({ city: z.string() }),
  execute: async ({ city }) => `Weather in ${city}: Sunny`,
});
```

### 4. Guardrails (가드레일)

입력/출력을 검증하는 안전장치입니다.

```python
# Python
from agents import Agent, InputGuardrail, OutputGuardrail

agent = Agent(
    name="Safe Agent",
    input_guardrails=[InputGuardrail(...)],
    output_guardrails=[OutputGuardrail(...)],
)
```

```typescript
// TypeScript
const agent = new Agent({
  name: 'Safe Agent',
  inputGuardrails: [{
    name: 'Content Filter',
    execute: async ({ input }) => ({
      tripwireTriggered: containsBadContent(input),
    }),
  }],
  outputGuardrails: [{
    name: 'PII Detection',
    execute: async ({ agentOutput }) => ({
      tripwireTriggered: /\d{3}-\d{3}-\d{4}/.test(agentOutput),
    }),
  }],
});
```

### 5. Sessions (세션/메모리)

대화 기록을 저장하고 관리합니다.

```python
# Python - SQLite 세션
from agents import Agent, Runner, SQLiteSession

session = SQLiteSession("user_123", "conversations.db")

result = await Runner.run(
    agent,
    "What is the weather?",
    session=session
)

# 세션 관리
items = await session.get_items()
await session.add_items([...])
await session.pop_item()
await session.clear_session()
```

### 6. MCP (Model Context Protocol)

외부 MCP 서버의 도구를 에이전트에 연결합니다.

```python
# Python
from agents import Agent
from agents.mcp import MCPServerStdio

server = MCPServerStdio(command="node", args=["mcp-server.js"])

agent = Agent(
    name="MCP Agent",
    mcp_servers=[server],
)
```

```typescript
// TypeScript
import { MCPServerStdio } from "@modelcontextprotocol/sdk/client/stdio.js";

const mcpServer = new MCPServerStdio({
  command: "node",
  args: ["path/to/mcp-server.js"]
});

const agent = new Agent({
  name: "Agent",
  mcpServers: [mcpServer]
});
```

---

## Python SDK

### 설치

```bash
pip install openai-agents
```

### 기본 사용법

```python
import asyncio
from agents import Agent, Runner

async def main():
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant.",
    )

    result = await Runner.run(agent, "Hello, how are you?")
    print(result.final_output)

asyncio.run(main())
```

### 멀티 에이전트 워크플로우

```python
from agents import Agent, Runner

# 전문가 에이전트들
history_agent = Agent(
    name="History Tutor",
    instructions="You provide assistance with historical queries.",
    handoff_description="Specialist in history"
)

math_agent = Agent(
    name="Math Tutor",
    instructions="You provide help with math problems.",
    handoff_description="Specialist in mathematics"
)

# 트리아지 에이전트
triage_agent = Agent(
    name="Triage Agent",
    instructions="Route to the appropriate specialist.",
    handoffs=[history_agent, math_agent],
)

# 실행
result = await Runner.run(triage_agent, "What caused World War 1?")
print(result.final_output)
```

### Context 사용

```python
from dataclasses import dataclass
from agents import Agent, Runner, RunContextWrapper, function_tool

@dataclass
class UserContext:
    name: str
    user_id: int

@function_tool
async def get_user_info(ctx: RunContextWrapper[UserContext]) -> str:
    return f"User: {ctx.context.name}, ID: {ctx.context.user_id}"

agent = Agent[UserContext](
    name="User Agent",
    tools=[get_user_info],
)

result = await Runner.run(
    agent,
    "Who am I?",
    context=UserContext(name="John", user_id=123)
)
```

### Model 설정

```python
from agents import Agent, ModelSettings

agent = Agent(
    name="Creative Agent",
    instructions="Be creative.",
    model="gpt-4.1",
    model_settings=ModelSettings(temperature=0.9),
)
```

### Voice/Realtime Agent

```python
from agents.realtime import RealtimeAgent, RealtimeRunner

agent = RealtimeAgent(
    name="Voice Assistant",
    instructions="You are a friendly voice assistant.",
)

runner = RealtimeRunner(agent)

async with runner.run() as session:
    async for event in session:
        if event.type == "audio":
            # 오디오 처리
            pass
```

---

## JavaScript/TypeScript SDK

### 설치

```bash
npm install @openai/agents zod
# 또는
pnpm add @openai/agents zod
```

### 기본 사용법

```typescript
import { Agent, run } from '@openai/agents';

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are a helpful assistant.',
});

async function main() {
  const result = await run(agent, 'Hello!');
  console.log(result.finalOutput);
}

main();
```

### Runner로 실행

```typescript
import { Agent, Runner } from '@openai/agents';

const runner = new Runner({
  model: 'gpt-4o-mini',
  modelSettings: {
    temperature: 0.7,
    maxTokens: 1000,
  },
  maxTurns: 15,
});

const agent = new Agent({
  name: 'Assistant',
  instructions: 'You are helpful.',
});

const result = await runner.run(agent, 'Explain quantum computing');
console.log(result.finalOutput);
```

### 도구 정의

```typescript
import { z } from 'zod';
import { Agent, run, tool } from '@openai/agents';

const calculatorTool = tool({
  name: 'calculator',
  description: 'Perform arithmetic operations',
  parameters: z.object({
    expression: z.string().describe('Math expression to evaluate'),
  }),
  execute: async ({ expression }) => {
    return `Result: ${eval(expression)}`;
  },
});

const agent = new Agent({
  name: 'Math Agent',
  instructions: 'Help with math problems.',
  tools: [calculatorTool],
});
```

### Agent를 Tool로 사용

```typescript
const subAgent = new Agent({
  name: 'SubAgent',
  instructions: 'You handle specific tasks.',
});

const mainAgent = new Agent({
  name: 'MainAgent',
  tools: [subAgent.asTool()],  // 에이전트를 도구로 변환
});
```

### 핸드오프 정의

```typescript
import { Agent, handoff } from '@openai/agents';

const billingAgent = new Agent({ name: 'Billing Agent' });
const supportAgent = new Agent({ name: 'Support Agent' });

// Agent.create으로 타입 안전한 핸드오프 설정
const triageAgent = Agent.create({
  name: 'Triage Agent',
  handoffs: [billingAgent, handoff(supportAgent)],
});
```

### Voice Agent (Realtime)

```typescript
import { RealtimeAgent, RealtimeSession } from '@openai/agents/realtime';

const agent = new RealtimeAgent({
  name: 'Voice Bot',
  instructions: 'Greet users warmly.',
  handoffs: [mathTutorAgent],
});

const session = new RealtimeSession(agent);
await session.connect();
```

---

## Agent Builder (Visual Canvas)

### 개요

Agent Builder는 **시각적 캔버스**로 멀티 스텝 에이전트 워크플로우를 구축하는 도구입니다.

**주요 기능:**
- 템플릿으로 시작하거나 처음부터 구축
- 드래그 앤 드롭 노드 편집
- 타입이 지정된 입력/출력
- 실시간 데이터로 프리뷰 실행

### AgentKit 구성요소

1. **Agent Builder**: 멀티 에이전트 워크플로우 시각적 편집기
2. **Connector Registry**: 데이터/도구 연결 관리
3. **ChatKit**: 채팅 기반 에이전트 UI 임베딩 툴킷

### 노드 유형

| 노드 | 설명 |
|------|------|
| **File Search** | 벡터 스토어에서 관련 정보 검색 (RAG) |
| **Guardrails** | PII, 탈옥, 환각 검사 및 모더레이션 |
| **MCP** | 외부/내부 도구 및 서비스와 상호작용 |
| **If/Else** | 조건부 분기 생성 |

### 배포 옵션

1. **ChatKit**: 워크플로우 ID로 앱에 임베드 (권장)
2. **Advanced Integration**: SDK 코드 복사하여 직접 실행

---

## Swarm (Legacy)

> **Note**: Swarm은 실험적/교육용 라이브러리입니다. 프로덕션에는 Agents SDK를 사용하세요.

### 기본 사용법

```python
from swarm import Swarm, Agent

client = Swarm()

def transfer_to_agent_b():
    return agent_b

agent_a = Agent(
    name="Agent A",
    instructions="You are a helpful agent.",
    functions=[transfer_to_agent_b],
)

agent_b = Agent(
    name="Agent B",
    instructions="Only speak in Haikus.",
)

response = client.run(
    agent=agent_a,
    messages=[{"role": "user", "content": "I want to talk to agent B."}]
)

print(response.messages[-1]["content"])
```

### 핸드오프와 Context 업데이트

```python
from swarm import Result

def talk_to_sales():
    return Result(
        value="Done",
        agent=sales_agent,
        context_variables={"department": "sales"}
    )

agent = Agent(functions=[talk_to_sales])

response = client.run(
    agent=agent,
    messages=[{"role": "user", "content": "Transfer me to sales"}],
    context_variables={"user_name": "John"}
)
```

---

## 공식 리소스

### 문서
- [Agent Builder Guide](https://platform.openai.com/docs/guides/agent-builder)
- [Agents Guide](https://platform.openai.com/docs/guides/agents)
- [Python SDK Docs](https://openai.github.io/openai-agents-python/)
- [JS/TS SDK Docs](https://openai.github.io/openai-agents-js/)

### GitHub
- [openai-agents-python](https://github.com/openai/openai-agents-python)
- [openai-agents-js](https://github.com/openai/openai-agents-js)
- [Swarm (Legacy)](https://github.com/openai/swarm)

### 기타
- [Agent Builder UI](https://platform.openai.com/agent-builder)
- [Building Agents Track](https://developers.openai.com/tracks/building-agents/)
- [Practical Guide to Building Agents (PDF)](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)
