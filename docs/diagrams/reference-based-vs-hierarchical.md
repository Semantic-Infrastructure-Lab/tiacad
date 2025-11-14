# Reference-Based vs Hierarchical Assembly

This diagram illustrates the key difference between TiaCAD's reference-based composition model and traditional CAD's hierarchical assembly model.

## Traditional CAD (Hierarchical)

```mermaid
graph TD
    Assembly[Assembly: Guitar Hanger]
    SubAsm1[Sub-Assembly: Mount]
    SubAsm2[Sub-Assembly: Hook]
    Part1[Part: Base Plate]
    Part2[Part: Screw Holes]
    Part3[Part: Hook Body]
    Part4[Part: Hook Cap]

    Assembly --> SubAsm1
    Assembly --> SubAsm2
    SubAsm1 --> Part1
    SubAsm1 --> Part2
    SubAsm2 --> Part3
    SubAsm2 --> Part4

    style Assembly fill:#e1f5ff
    style SubAsm1 fill:#fff4e1
    style SubAsm2 fill:#fff4e1
    style Part1 fill:#e8f5e9
    style Part2 fill:#e8f5e9
    style Part3 fill:#e8f5e9
    style Part4 fill:#e8f5e9
```

**Characteristics:**
- Parent-child relationships
- Nested hierarchy
- Parts "belong to" assemblies
- Rigid structure

## TiaCAD (Reference-Based)

```mermaid
graph LR
    base[Part: base]
    pillar[Part: pillar]
    cap[Part: cap]

    anchor1[Anchor: base.face_top]
    anchor2[Anchor: pillar.face_top]

    base -.->|provides| anchor1
    pillar -.->|provides| anchor2

    anchor1 -->|positions| pillar
    anchor2 -->|positions| cap

    style base fill:#e8f5e9
    style pillar fill:#e8f5e9
    style cap fill:#e8f5e9
    style anchor1 fill:#fff3e0
    style anchor2 fill:#fff3e0
```

**Characteristics:**
- All parts are peers (no parent-child)
- Spatial anchors define relationships
- Parts are independent
- Flexible composition

## Key Differences

| Aspect | Traditional CAD | TiaCAD |
|--------|----------------|--------|
| Structure | Tree (hierarchical) | Graph (peer-based) |
| Relationships | Parent owns child | Part references anchor |
| Organization | Assembly → Sub-assembly → Part | Part → Part → Part |
| Positioning | Mate constraints | Spatial anchors |
| Flexibility | Rigid hierarchy | Flexible references |

## Mental Model

**Traditional CAD:** "This part belongs in this assembly"
**TiaCAD:** "This part is positioned at this anchor"

Think of TiaCAD like marking spots on a workbench where things go, rather than organizing parts into nested folders.
