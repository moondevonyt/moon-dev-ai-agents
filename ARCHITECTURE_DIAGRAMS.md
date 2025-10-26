# Moon Dev EDA Implementation - Architecture & Data Flow Diagrams

**Generated**: 2025-10-26  
**Version**: 1.0.0  
**Purpose**: Visual architecture and data flow documentation using Mermaid diagrams

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Component Architecture](#2-component-architecture)
3. [Data Flow Diagrams](#3-data-flow-diagrams)
4. [Event Flow Sequences](#4-event-flow-sequences)
5. [Deployment Architecture](#5-deployment-architecture)
6. [Agent Interaction Diagrams](#6-agent-interaction-diagrams)

---

## 1. System Architecture Overview

### 1.1 High-Level System Architecture

```mermaid
graph TB
    subgraph "External Systems"
        EX1[HyperLiquid Exchange]
        EX2[Solana DEX]
        EX3[Social Media APIs]
        EX4[Market Data Feeds]
    end

    subgraph "Ingestion Layer"
        MD[Market Data Adapter]
        SA[Sentiment Adapter]
        LA[Liquidation Monitor]
    end

    subgraph "Message Broker - Kafka Cluster"
        K1[Kafka Broker 1]
        K2[Kafka Broker 2]
        K3[Kafka Broker 3]
        ZK[Zookeeper]
        
        K1 -.-> ZK
        K2 -.-> ZK
        K3 -.-> ZK
    end

    subgraph "Agent Layer"
        RA[Risk Agent]
        TA[Trading Agent]
        SA2[Sentiment Agent]
        CA[Consensus Agent]
    end

    subgraph "Execution Layer"
        EE[Execution Engine]
        OM[Order Manager]
        RM[Risk Manager]
    end

    subgraph "Storage Layer"
        ES[(Event Store<br/>TimescaleDB)]
        CACHE[(Cache Layer<br/>Redis)]
    end

    subgraph "API Layer"
        API[FastAPI Server]
        WS[WebSocket Server]
    end

    subgraph "Monitoring"
        PROM[Prometheus]
        GRAF[Grafana]
        ALERT[Alertmanager]
    end

    %% External to Ingestion
    EX1 -->|WebSocket| MD
    EX2 -->|RPC| MD
    EX3 -->|REST API| SA
    EX4 -->|WebSocket| LA

    %% Ingestion to Kafka
    MD -->|Publish Events| K1
    SA -->|Publish Events| K2
    LA -->|Publish Events| K3

    %% Kafka to Agents
    K1 -->|Subscribe| RA
    K1 -->|Subscribe| TA
    K2 -->|Subscribe| SA2
    K1 -->|Subscribe| CA

    %% Agents to Kafka
    RA -->|Emit Events| K2
    TA -->|Emit Events| K2
    SA2 -->|Emit Events| K3
    CA -->|Emit Events| K1


    %% Kafka to Execution
    K1 -->|Subscribe| EE
    
    %% Execution to Storage
    EE -->|Write| ES
    EE -->|Update| CACHE
    
    %% Execution to Exchange
    EE -->|Place Orders| EX1
    EE -->|Execute Swaps| EX2
    
    %% Storage to API
    ES -->|Query| API
    CACHE -->|Read| API
    
    %% API to Clients
    API -->|REST| WS
    WS -->|Real-time Updates| API
    
    %% Monitoring
    K1 -.->|Metrics| PROM
    RA -.->|Metrics| PROM
    TA -.->|Metrics| PROM
    EE -.->|Metrics| PROM
    PROM -->|Visualize| GRAF
    PROM -->|Alerts| ALERT

    style K1 fill:#ff9900
    style K2 fill:#ff9900
    style K3 fill:#ff9900
    style ES fill:#4a90e2
    style CACHE fill:#e24a4a
    style EE fill:#50c878
    style API fill:#9b59b6
```

### 1.2 Layered Architecture View

```mermaid
graph LR
    subgraph "Presentation Layer"
        UI[Web Dashboard]
        MOB[Mobile App]
        CLI[CLI Tools]
    end

    subgraph "API Gateway Layer"
        REST[REST API]
        WS[WebSocket API]
        GQL[GraphQL Optional]
    end

    subgraph "Application Layer"
        AGENTS[Agent Services]
        EXEC[Execution Services]
        BACK[Backtesting Services]
    end

    subgraph "Event Processing Layer"
        KAFKA[Kafka Message Broker]
        STREAM[Stream Processing]
    end

    subgraph "Data Layer"
        TSDB[(TimescaleDB)]
        REDIS[(Redis Cache)]
        S3[(S3 Backups)]
    end

    subgraph "Infrastructure Layer"
        K8S[Kubernetes]
        PROM[Prometheus]
        GRAF[Grafana]
    end

    UI --> REST
    MOB --> WS
    CLI --> REST
    
    REST --> AGENTS
    WS --> AGENTS
    REST --> EXEC
    
    AGENTS --> KAFKA
    EXEC --> KAFKA
    BACK --> KAFKA
    
    KAFKA --> TSDB
    KAFKA --> REDIS
    
    AGENTS -.-> PROM
    EXEC -.-> PROM
    
    K8S -.-> AGENTS
    K8S -.-> EXEC
    K8S -.-> KAFKA

    style KAFKA fill:#ff9900
    style TSDB fill:#4a90e2
    style REDIS fill:#e24a4a
```

---

## 2. Component Architecture

### 2.1 Core Event System Components

```mermaid
graph TB
    subgraph "Event Producer"
        EP[EventProducer Class]
        EP_PUB[publish method]
        EP_BATCH[publish_batch method]
        EP_RETRY[retry_logic]
        EP_METRICS[metrics_collector]
        
        EP --> EP_PUB
        EP --> EP_BATCH
        EP_PUB --> EP_RETRY
        EP_PUB --> EP_METRICS
    end

    subgraph "Event Consumer"
        EC[EventConsumer Class]
        EC_SUB[subscribe method]
        EC_HAND[event_handler decorator]
        EC_OFF[offset_manager]
        EC_DLQ[dead_letter_queue]
        
        EC --> EC_SUB
        EC --> EC_HAND
        EC_SUB --> EC_OFF
        EC_SUB --> EC_DLQ
    end

    subgraph "Event Store"
        EST[EventStore Class]
        EST_INS[insert_event]
        EST_BATCH[insert_batch]
        EST_QUERY[query_by_date_range]
        EST_COMP[compression]
        
        EST --> EST_INS
        EST --> EST_BATCH
        EST --> EST_QUERY
        EST_INS --> EST_COMP
    end

    subgraph "Cache Layer"
        CL[CacheLayer Class]
        CL_GET[get/set/delete]
        CL_PORT[get_portfolio]
        CL_CONS[consistency_check]
        CL_FALL[fallback_to_db]
        
        CL --> CL_GET
        CL --> CL_PORT
        CL_GET --> CL_CONS
        CL_CONS --> CL_FALL
    end

    EP_PUB -->|Kafka Protocol| KAFKA[Kafka Broker]
    KAFKA -->|Consumer Group| EC_SUB
    EST_INS -->|SQL| TSDB[(TimescaleDB)]
    CL_GET -->|Redis Protocol| REDIS[(Redis)]

    style EP fill:#90ee90
    style EC fill:#87ceeb
    style EST fill:#dda0dd
    style CL fill:#f08080
```

### 2.2 Agent Architecture

```mermaid
classDiagram
    class BaseAgent {
        +kafka_servers: List~str~
        +consumer_group: str
        +topics: List~str~
        +producer: EventProducer
        +start()
        +stop()
        +process_event(event)
        #emit_event(event)
    }

    class RiskAgent {
        +max_leverage: float
        +liquidation_threshold: float
        +calculate_leverage()
        +check_liquidation_distance()
        +emit_risk_alert()
        +force_close_position()
    }

    class TradingAgent {
        +llm_client: Anthropic
        +indicators: TechnicalIndicators
        +calculate_indicators()
        +generate_signal()
        +query_llm_async()
        +parse_signal()
    }

    class SentimentAgent {
        +time_windows: List~int~
        +aggregate_sentiment()
        +calculate_velocity()
        +emit_sentiment_event()
    }

    class ConsensusAgent {
        +consensus_threshold: float
        +signal_window: int
        +aggregate_signals()
        +calculate_weighted_score()
        +emit_consensus()
    }

    BaseAgent <|-- RiskAgent
    BaseAgent <|-- TradingAgent
    BaseAgent <|-- SentimentAgent
    BaseAgent <|-- ConsensusAgent

    BaseAgent --> EventProducer
    BaseAgent --> EventConsumer
```

### 2.3 Execution Engine Architecture

```mermaid
graph TB
    subgraph "Execution Engine"
        EE[ExecutionEngine]
        VAL[Risk Validator]
        SIZE[Position Sizer]
        ORDER[Order Manager]
        FILL[Fill Monitor]
        
        EE --> VAL
        VAL --> SIZE
        SIZE --> ORDER
        ORDER --> FILL
    end

    subgraph "Exchange Adapters"
        HL[HyperLiquid Adapter]
        SOL[Solana Adapter]
        BASE[Base Adapter Interface]
        
        BASE <|-- HL
        BASE <|-- SOL
    end

    subgraph "Order Types"
        MARKET[Market Order]
        LIMIT[Limit Order]
        STOP[Stop Loss]
        TP[Take Profit]
    end

    KAFKA[Kafka: signal.generated] -->|Subscribe| EE
    
    VAL -->|Check Constraints| CACHE[(Redis Cache)]
    SIZE -->|Calculate Size| CACHE
    
    ORDER -->|Route| HL
    ORDER -->|Route| SOL
    
    HL -->|REST API| EX1[HyperLiquid]
    SOL -->|RPC| EX2[Solana]
    
    FILL -->|Emit| KAFKA2[Kafka: trade.executed]
    FILL -->|Update| CACHE
    FILL -->|Persist| TSDB[(TimescaleDB)]

    ORDER --> MARKET
    ORDER --> LIMIT
    ORDER --> STOP
    ORDER --> TP

    style EE fill:#50c878
    style VAL fill:#ff6b6b
    style ORDER fill:#4ecdc4
```

---

## 3. Data Flow Diagrams

### 3.1 End-to-End Trade Execution Flow

```mermaid
sequenceDiagram
    participant EX as Exchange
    participant MD as Market Data
    participant K as Kafka
    participant RA as Risk Agent
    participant TA as Trading Agent
    participant CA as Consensus
    participant EE as Execution Engine
    participant CACHE as Redis Cache
    participant DB as TimescaleDB

    Note over EX,DB: t=0ms: Market Event Occurs
    
    EX->>MD: WebSocket: Price Update
    MD->>K: Publish: price.tick
    Note over K: Event in Kafka (t=5ms)
    
    par Parallel Agent Processing
        K->>RA: Consume: price.tick
        K->>TA: Consume: price.tick
    end
    
    Note over RA: t=10ms: Risk Evaluation
    RA->>CACHE: Get Portfolio
    CACHE-->>RA: Portfolio State
    RA->>RA: Calculate Leverage
    alt Risk OK
        RA->>K: Emit: risk.ok
    else Risk Alert
        RA->>K: Emit: risk.alert
    end
    
    Note over TA: t=20ms: Signal Generation
    TA->>TA: Calculate Indicators
    TA->>TA: Queue LLM (async)
    TA->>K: Emit: signal.generated
    
    Note over CA: t=100ms: Consensus
    K->>CA: Consume: Multiple Signals
    CA->>CA: Aggregate & Score
    alt Consensus Reached
        CA->>K: Emit: trade.consensus_approved
    else No Consensus
        CA->>K: Emit: signal.consensus_failed
    end
    
    Note over EE: t=120ms: Execution
    K->>EE: Consume: consensus_approved
    EE->>CACHE: Validate Risk
    CACHE-->>EE: Risk OK
    EE->>EE: Calculate Position Size
    EE->>EX: REST: Place Order
    EX-->>EE: Order Accepted
    EE->>K: Emit: trade.placed
    
    Note over EX: t=150ms: Fill
    EX->>EE: WebSocket: Fill Notification
    EE->>K: Emit: trade.executed
    EE->>CACHE: Update Position
    EE->>DB: Persist Event
    
    Note over EX,DB: Total Latency: 150-200ms
```

### 3.2 Risk Alert and Force Close Flow

```mermaid
sequenceDiagram
    participant K as Kafka
    participant RA as Risk Agent
    participant CACHE as Redis
    participant EE as Execution Engine
    participant EX as Exchange
    participant ALERT as Alert System

    K->>RA: price.tick (Sudden Drop)
    RA->>CACHE: Get Portfolio
    CACHE-->>RA: Current Positions
    
    RA->>RA: Calculate Leverage
    RA->>RA: Check Liquidation Distance
    
    alt Critical Risk (< 10% buffer)
        RA->>K: Emit: risk.critical
        RA->>ALERT: Send Discord Alert
        
        K->>EE: Consume: risk.critical
        EE->>EE: Validate Signal
        EE->>EX: Market Close Order (Priority)
        EX-->>EE: Order Filled
        
        EE->>K: Emit: position.closed
        EE->>CACHE: Update Portfolio
        EE->>ALERT: Confirm Close
        
    else Warning (< 20% buffer)
        RA->>K: Emit: risk.alert
        RA->>ALERT: Send Warning
        
    else OK
        RA->>K: Emit: risk.ok
    end
```

### 3.3 Backtesting Data Flow

```mermaid
graph LR
    subgraph "Backtest Initialization"
        USER[User Request]
        PARAMS[Backtest Parameters]
        USER --> PARAMS
    end

    subgraph "Historical Data"
        DB[(TimescaleDB)]
        QUERY[Query Events]
        EVENTS[Historical Events]
        
        PARAMS --> QUERY
        QUERY --> DB
        DB --> EVENTS
    end

    subgraph "Backtest Execution"
        ENGINE[Backtest Engine]
        REPLAY[Event Replay]
        AGENTS[Agent Instances]
        
        EVENTS --> ENGINE
        ENGINE --> REPLAY
        REPLAY --> AGENTS
    end

    subgraph "Results Processing"
        TRADES[Simulated Trades]
        CALC[Performance Calculator]
        METRICS[Metrics]
        
        AGENTS --> TRADES
        TRADES --> CALC
        CALC --> METRICS
    end

    subgraph "Report Generation"
        REPORT[Backtest Report]
        HTML[HTML Report]
        JSON[JSON Export]
        
        METRICS --> REPORT
        REPORT --> HTML
        REPORT --> JSON
    end

    HTML --> USER
    JSON --> USER

    style ENGINE fill:#9b59b6
    style CALC fill:#3498db
    style REPORT fill:#2ecc71
```

---

## 4. Event Flow Sequences

### 4.1 Multi-Agent Consensus Flow

```mermaid
sequenceDiagram
    participant K as Kafka
    participant TA as Trading Agent
    participant SA as Sentiment Agent
    participant CA as Chart Agent
    participant CONS as Consensus Agent
    participant EE as Execution Engine

    Note over K,EE: Multiple Agents Generate Signals

    K->>TA: price.tick
    TA->>TA: Technical Analysis
    TA->>K: signal.generated (score: 75)

    K->>SA: sentiment.update
    SA->>SA: Aggregate Sentiment
    SA->>K: signal.generated (score: 82)

    K->>CA: price.tick
    CA->>CA: Chart Pattern Analysis
    CA->>K: signal.generated (score: 68)

    Note over CONS: Consensus Window (5 seconds)
    
    K->>CONS: Consume All Signals
    CONS->>CONS: Calculate Weighted Score
    CONS->>CONS: Score = (75*0.4 + 82*0.3 + 68*0.3) = 74.6
    
    alt Score > Threshold (70%)
        CONS->>K: trade.consensus_approved
        K->>EE: Execute Trade
    else Score < Threshold
        CONS->>K: signal.consensus_failed
        Note over EE: No Action
    end
```

### 4.2 Event Sourcing and State Reconstruction

```mermaid
graph TB
    subgraph "Event Log (Immutable)"
        E1[Event 1: trade.executed<br/>BTC +1.0 @ 43000]
        E2[Event 2: trade.executed<br/>ETH +10.0 @ 2500]
        E3[Event 3: position.closed<br/>BTC -1.0 @ 44000]
        E4[Event 4: trade.executed<br/>SOL +100 @ 95]
        
        E1 --> E2
        E2 --> E3
        E3 --> E4
    end

    subgraph "State Projection (Cache)"
        S1[Portfolio State]
        POS[Positions:<br/>ETH: 10.0<br/>SOL: 100]
        BAL[Balance: $15,000]
        PNL[Realized PnL: +$1,000]
        
        S1 --> POS
        S1 --> BAL
        S1 --> PNL
    end

    subgraph "Reconstruction"
        REPLAY[Replay Events]
        REBUILD[Rebuild State]
        
        E1 -.->|Replay| REPLAY
        E2 -.->|Replay| REPLAY
        E3 -.->|Replay| REPLAY
        E4 -.->|Replay| REPLAY
        
        REPLAY --> REBUILD
        REBUILD --> S1
    end

    E4 -->|Latest Event| S1

    style E1 fill:#e8f4f8
    style E2 fill:#e8f4f8
    style E3 fill:#e8f4f8
    style E4 fill:#e8f4f8
    style S1 fill:#ffe8e8
```

### 4.3 WebSocket Real-Time Updates

```mermaid
sequenceDiagram
    participant CLIENT as Dashboard Client
    participant WS as WebSocket Server
    participant CACHE as Redis Cache
    participant K as Kafka
    participant AGENT as Trading Agent

    CLIENT->>WS: Connect: /ws/portfolio/user123
    WS->>CACHE: Get Initial State
    CACHE-->>WS: Portfolio Data
    WS->>CLIENT: initial_state

    Note over K,AGENT: Trade Executed

    AGENT->>K: Emit: trade.executed
    K->>CACHE: Update Portfolio
    CACHE->>WS: Notify: State Changed
    WS->>CLIENT: portfolio_update (delta)

    Note over CLIENT: Real-time UI Update

    loop Every 5 seconds
        WS->>CACHE: Get Latest State
        CACHE-->>WS: Portfolio Data
        WS->>CLIENT: portfolio_update
    end

    CLIENT->>WS: Disconnect
    WS->>WS: Cleanup Connection
```

---

## 5. Deployment Architecture

### 5.1 Kubernetes Deployment

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: moon-dev-eda"
            subgraph "Kafka StatefulSet"
                K1[kafka-0]
                K2[kafka-1]
                K3[kafka-2]
                PVC1[(PVC 100GB)]
                PVC2[(PVC 100GB)]
                PVC3[(PVC 100GB)]
                
                K1 --- PVC1
                K2 --- PVC2
                K3 --- PVC3
            end

            subgraph "Agent Deployments"
                RA1[risk-agent-0]
                RA2[risk-agent-1]
                TA1[trading-agent-0]
                TA2[trading-agent-1]
                SA1[sentiment-agent-0]
            end

            subgraph "Execution Deployment"
                EE1[execution-engine-0]
                EE2[execution-engine-1]
            end

            subgraph "API Deployment"
                API1[api-server-0]
                API2[api-server-1]
                API3[api-server-2]
                LB[LoadBalancer Service]
                
                LB --> API1
                LB --> API2
                LB --> API3
            end

            subgraph "Data StatefulSets"
                TS1[timescaledb-0]
                TS2[timescaledb-1]
                TSPVC1[(PVC 500GB)]
                TSPVC2[(PVC 500GB)]
                
                TS1 --- TSPVC1
                TS2 --- TSPVC2
                
                R1[redis-0]
                R2[redis-1]
                R3[redis-2]
            end

            subgraph "Monitoring"
                PROM[prometheus]
                GRAF[grafana]
                ALERT[alertmanager]
            end
        end

        subgraph "Ingress"
            ING[Ingress Controller]
            ING --> LB
        end
    end

    subgraph "External"
        USERS[Users]
        EXCHANGE[Exchanges]
    end

    USERS -->|HTTPS| ING
    EE1 -->|API| EXCHANGE
    EE2 -->|API| EXCHANGE

    style K1 fill:#ff9900
    style K2 fill:#ff9900
    style K3 fill:#ff9900
    style TS1 fill:#4a90e2
    style TS2 fill:#4a90e2
    style R1 fill:#e24a4a
    style R2 fill:#e24a4a
    style R3 fill:#e24a4a
```

### 5.2 Network Architecture

```mermaid
graph TB
    subgraph "Public Internet"
        USERS[Users/Clients]
    end

    subgraph "DMZ"
        ALB[Application Load Balancer]
        WAF[Web Application Firewall]
        
        USERS --> WAF
        WAF --> ALB
    end

    subgraph "Application Tier (Private Subnet)"
        API[API Servers]
        AGENTS[Agent Services]
        
        ALB --> API
    end

    subgraph "Message Tier (Private Subnet)"
        KAFKA[Kafka Cluster]
        
        API --> KAFKA
        AGENTS --> KAFKA
    end

    subgraph "Data Tier (Private Subnet)"
        TSDB[(TimescaleDB)]
        REDIS[(Redis)]
        
        API --> REDIS
        API --> TSDB
        AGENTS --> REDIS
        AGENTS --> TSDB
    end

    subgraph "External Services"
        EXCHANGE[Exchanges]
        LLM[LLM APIs]
        
        AGENTS --> EXCHANGE
        AGENTS --> LLM
    end

    subgraph "Monitoring (Private Subnet)"
        PROM[Prometheus]
        GRAF[Grafana]
        
        API -.->|Metrics| PROM
        AGENTS -.->|Metrics| PROM
        KAFKA -.->|Metrics| PROM
        PROM --> GRAF
    end

    style ALB fill:#ff9900
    style KAFKA fill:#ff9900
    style TSDB fill:#4a90e2
    style REDIS fill:#e24a4a
```

---

## 6. Agent Interaction Diagrams

### 6.1 Agent Communication Pattern

```mermaid
graph TB
    subgraph "Event-Driven Communication"
        K[Kafka Message Broker]
    end

    subgraph "Agents (No Direct Calls)"
        RA[Risk Agent]
        TA[Trading Agent]
        SA[Sentiment Agent]
        CA[Consensus Agent]
        EA[Execution Agent]
    end

    RA -->|Emit: risk.alert| K
    TA -->|Emit: signal.generated| K
    SA -->|Emit: sentiment.update| K
    CA -->|Emit: consensus.approved| K
    EA -->|Emit: trade.executed| K

    K -->|Subscribe| RA
    K -->|Subscribe| TA
    K -->|Subscribe| SA
    K -->|Subscribe| CA
    K -->|Subscribe| EA

    style K fill:#ff9900
    style RA fill:#ff6b6b
    style TA fill:#4ecdc4
    style SA fill:#95e1d3
    style CA fill:#f38181
    style EA fill:#50c878
```

### 6.2 Agent State Machine

```mermaid
stateDiagram-v2
    [*] --> Initializing
    Initializing --> Connecting: Load Config
    Connecting --> Ready: Kafka Connected
    Connecting --> Error: Connection Failed
    
    Ready --> Processing: Event Received
    Processing --> Emitting: Logic Complete
    Emitting --> Ready: Event Published
    
    Processing --> Error: Processing Failed
    Error --> Ready: Retry Success
    Error --> [*]: Max Retries
    
    Ready --> Stopping: Shutdown Signal
    Stopping --> [*]: Cleanup Complete
```

### 6.3 Consensus Mechanism

```mermaid
graph TB
    subgraph "Signal Collection Window (5 seconds)"
        S1[Signal 1: Trading Agent<br/>Score: 75, Weight: 0.4]
        S2[Signal 2: Sentiment Agent<br/>Score: 82, Weight: 0.3]
        S3[Signal 3: Chart Agent<br/>Score: 68, Weight: 0.3]
    end

    subgraph "Consensus Calculation"
        CALC[Weighted Average:<br/>75*0.4 + 82*0.3 + 68*0.3 = 74.6]
        THRESH{Score > 70%?}
        
        S1 --> CALC
        S2 --> CALC
        S3 --> CALC
        CALC --> THRESH
    end

    subgraph "Decision"
        APPROVE[Consensus Approved]
        REJECT[Consensus Failed]
        
        THRESH -->|Yes| APPROVE
        THRESH -->|No| REJECT
    end

    subgraph "Action"
        EXEC[Execute Trade]
        NOOP[No Action]
        
        APPROVE --> EXEC
        REJECT --> NOOP
    end

    style CALC fill:#3498db
    style APPROVE fill:#2ecc71
    style REJECT fill:#e74c3c
```

---

## Summary

These diagrams provide comprehensive visual documentation of the Moon Dev EDA implementation:

1. **System Architecture**: Shows the complete system with all components and their interactions
2. **Component Architecture**: Details internal structure of core components
3. **Data Flow**: Illustrates how data moves through the system
4. **Event Sequences**: Shows timing and ordering of events
5. **Deployment**: Kubernetes and network architecture
6. **Agent Interactions**: How agents communicate via events

All diagrams are rendered using Mermaid and can be viewed in any Markdown viewer that supports Mermaid syntax.

---

**Generated**: 2025-10-26  
**Version**: 1.0.0  
**Status**: Complete
