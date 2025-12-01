# Reference Chain Dependencies

This diagram shows how parts reference each other's anchors, creating dependency chains.

## Simple Reference Chain

```mermaid
graph LR
    subgraph "Parts (Independent)"
        platform[Part: platform<br/>box 100×5×100]
        pillar[Part: pillar<br/>cylinder r=5, h=50]
        cap[Part: cap<br/>box 15×5×15]
    end

    subgraph "Anchors (Auto-Generated)"
        platform_top[platform.face_top]
        pillar_top[pillar.face_top]
    end

    subgraph "Dependencies"
        pillar -->|references| platform_top
        cap -->|references| pillar_top
    end

    platform -.->|provides| platform_top
    pillar -.->|provides| pillar_top

    style platform fill:#4caf50,color:#fff
    style pillar fill:#2196f3,color:#fff
    style cap fill:#ff9800,color:#fff
    style platform_top fill:#fff3e0
    style pillar_top fill:#fff3e0
```

## Complex Assembly with Multiple References

```mermaid
graph TD
    subgraph "Parts"
        base[base]
        left_pillar[left_pillar]
        right_pillar[right_pillar]
        crossbar[crossbar]
        hook[hook]
    end

    subgraph "Anchors"
        base_top[base.face_top]
        base_left[base.face_left]
        base_right[base.face_right]
        left_top[left_pillar.face_top]
        right_top[right_pillar.face_top]
        crossbar_center[crossbar.center]
    end

    base -.-> base_top
    base -.-> base_left
    base -.-> base_right

    left_pillar -->|references| base_left
    left_pillar -.-> left_top

    right_pillar -->|references| base_right
    right_pillar -.-> right_top

    crossbar -->|references| left_top
    crossbar -->|references| right_top
    crossbar -.-> crossbar_center

    hook -->|references| crossbar_center

    style base fill:#4caf50,color:#fff
    style left_pillar fill:#2196f3,color:#fff
    style right_pillar fill:#2196f3,color:#fff
    style crossbar fill:#ff9800,color:#fff
    style hook fill:#e91e63,color:#fff
```

## Dependency Resolution Order

TiaCAD resolves references in the order parts are defined:

```yaml
parts:
  # 1. base - no dependencies, created first
  base:
    primitive: box
    parameters: {width: 100, height: 5, depth: 100}

  # 2. pillar - depends on base, created second
  pillar:
    primitive: cylinder
    parameters: {radius: 5, height: 50}
    translate:
      to: base.face_top  # ✅ base exists, reference resolved

  # 3. cap - depends on pillar, created third
  cap:
    primitive: box
    parameters: {width: 15, height: 5, depth: 15}
    translate:
      to: pillar.face_top  # ✅ pillar exists, reference resolved
```

## Invalid Reference Chains

### Circular Dependency (❌ Error)

```yaml
parts:
  part_a:
    translate:
      to: part_b.face_top  # ❌ part_b doesn't exist yet!

  part_b:
    translate:
      to: part_a.face_top  # ❌ Circular reference!
```

**Error:** `Circular dependency detected: part_a → part_b → part_a`

### Forward Reference (❌ Error)

```yaml
parts:
  tower:
    translate:
      to: base.face_top  # ❌ base doesn't exist yet!

  base:
    primitive: box
```

**Error:** `Reference 'base.face_top' not found (part 'base' not defined yet)`

## Valid Dependency Patterns

### Linear Chain ✅

```mermaid
graph LR
    A[Part A] --> B[Part B]
    B --> C[Part C]
    C --> D[Part D]

    style A fill:#4caf50,color:#fff
    style B fill:#2196f3,color:#fff
    style C fill:#ff9800,color:#fff
    style D fill:#e91e63,color:#fff
```

**Order matters:** A → B → C → D

### Tree Structure ✅

```mermaid
graph TD
    Root[Root]
    Root --> Child1[Child 1]
    Root --> Child2[Child 2]
    Root --> Child3[Child 3]
    Child1 --> Grandchild1[Grandchild 1]
    Child2 --> Grandchild2[Grandchild 2]

    style Root fill:#4caf50,color:#fff
    style Child1 fill:#2196f3,color:#fff
    style Child2 fill:#2196f3,color:#fff
    style Child3 fill:#2196f3,color:#fff
```

**All children reference root, grandchildren reference children**

### Diamond (Multi-Reference) ✅

```mermaid
graph TD
    Base[Base]
    Left[Left Support]
    Right[Right Support]
    Top[Top Platform]

    Base --> Left
    Base --> Right
    Left --> Top
    Right --> Top

    style Base fill:#4caf50,color:#fff
    style Left fill:#2196f3,color:#fff
    style Right fill:#2196f3,color:#fff
    style Top fill:#ff9800,color:#fff
```

**Top references both left and right supports**

## Custom Anchors in Reference Chains

You can define custom anchors that reference other parts:

```yaml
parts:
  base:
    primitive: box
    parameters: {width: 100, height: 5, depth: 100}

  pillar:
    primitive: cylinder
    parameters: {radius: 5, height: 50}
    translate:
      to: base.face_top

anchors:
  # Custom anchor that combines multiple references
  assembly_top:
    from: pillar.face_top
    offset: [0, 0, 10]

  # Another part can reference this custom anchor
  flag:
    primitive: box
    parameters: {width: 2, height: 20, depth: 2}
    translate:
      to: assembly_top  # References custom anchor
```

## Dependency Graph Visualization

```mermaid
graph TD
    subgraph "Definition Order (YAML)"
        def1["1. base (no deps)"]
        def2["2. pillar (→ base)"]
        def3["3. cap (→ pillar)"]
    end

    subgraph "Execution Order"
        exec1["1. Create base"]
        exec2["2. Generate base anchors"]
        exec3["3. Create pillar using base.face_top"]
        exec4["4. Generate pillar anchors"]
        exec5["5. Create cap using pillar.face_top"]
    end

    def1 --> exec1
    exec1 --> exec2
    def2 --> exec3
    exec2 --> exec3
    exec3 --> exec4
    def3 --> exec5
    exec4 --> exec5

    style exec1 fill:#4caf50,color:#fff
    style exec3 fill:#2196f3,color:#fff
    style exec5 fill:#ff9800,color:#fff
```

## Best Practices

### ✅ DO: Define parts in dependency order

```yaml
parts:
  foundation:  # No dependencies
    ...
  walls:       # Depends on foundation
    translate: {to: foundation.face_top}
  roof:        # Depends on walls
    translate: {to: walls.face_top}
```

### ✅ DO: Use descriptive part names

```yaml
parts:
  mounting_plate:  # Clear name
    ...
  left_bracket:    # Clear spatial relationship
    translate: {to: mounting_plate.face_left}
```

### ❌ DON'T: Create circular dependencies

```yaml
parts:
  a:
    translate: {to: b.center}  # ❌ b doesn't exist yet
  b:
    translate: {to: a.center}  # ❌ Circular!
```

### ❌ DON'T: Reference undefined parts

```yaml
parts:
  top:
    translate: {to: base.face_top}  # ❌ base not defined yet
  base:
    ...
```

## Summary

| Concept | Key Point |
|---------|-----------|
| **Independence** | Parts don't "own" other parts |
| **References** | Parts reference spatial anchors |
| **Order** | Define parts before referencing them |
| **Chains** | References can chain: A → B → C |
| **Validation** | TiaCAD detects circular dependencies |
| **Flexibility** | Same part can be referenced by multiple others |
