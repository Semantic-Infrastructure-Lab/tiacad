# TiaCAD Export Format Analysis

## Current State (2025-11-02)

TiaCAD currently supports:
- ✅ **STL** (old, tessellation-only)
- ✅ **STEP** (CAD standard, parametric)
- ✅ **3MF** (modern 3D printing, multi-material) ← **BEST FOR 3D PRINTING**

## Format Comparison

### STL (STereoLithography) - 1987
**Status:** ❌ **LEGACY - AVOID**

**Pros:**
- Universal support (every slicer reads it)
- Simple format

**Cons:**
- ❌ No color/material information
- ❌ No units (ambiguous mm vs inches)
- ❌ No metadata
- ❌ Tessellation only (loses exact geometry)
- ❌ File size bloat (binary better than ASCII, but still large)
- ❌ No multi-part assemblies
- ❌ Cannot represent curves exactly

**Use Case:** Only for legacy tool compatibility

---

### 3MF (3D Manufacturing Format) - 2015
**Status:** ✅ **MODERN STANDARD - ALREADY IMPLEMENTED**

**Pros:**
- ✅ Multi-material & multi-color support **← TiaCAD HAS THIS!**
- ✅ Material properties (PLA, ABS, TPU metadata)
- ✅ Units embedded in format
- ✅ Compressed (ZIP-based, ~50% smaller than STL)
- ✅ Assembly support
- ✅ Metadata & thumbnails
- ✅ Industry standard (Microsoft, Autodesk, HP, Ultimaker)
- ✅ Modern slicer support (PrusaSlicer, OrcaSlicer, BambuStudio, Cura 5+)

**Cons:**
- Some old slicers don't support it (but they're dying out)

**Use Case:** **PRIMARY EXPORT FOR 3D PRINTING** ← **WE ALREADY HAVE THIS!**

**TiaCAD Integration:** Fully implemented with color system support

---

### STEP (ISO 10303) - 1994
**Status:** ✅ **CAD STANDARD - ALREADY IMPLEMENTED**

**Pros:**
- ✅ Exact geometry (not tessellated)
- ✅ Parametric data (curves, surfaces, solids)
- ✅ CAD tool interoperability (Fusion 360, SolidWorks, FreeCAD)
- ✅ Assembly support
- ✅ Units & tolerances

**Cons:**
- Complex format
- Large files
- Not for 3D printing (slicers don't read it directly)

**Use Case:** CAD tool exchange, further editing

---

### glTF 2.0 (GL Transmission Format) - 2017
**Status:** 🤔 **CONSIDER FOR WEB/VISUALIZATION**

**Pros:**
- Modern web standard (Three.js, Babylon.js)
- PBR materials (physically-based rendering)
- Animations & skinning
- Compact binary format (GLB)
- JSON-based (human-readable)

**Cons:**
- Not for 3D printing (visualization focus)
- Tessellated (not exact CAD geometry)

**Use Case:** Web viewers, AR/VR, game engines

---

### OBJ (Wavefront) - 1990s
**Status:** ❌ **LEGACY**

**Pros:**
- Simple text format
- Materials via MTL files
- Wide support

**Cons:**
- No exact geometry
- No assemblies
- No units
- Large files
- Materials are a separate file (breaks easily)

**Use Case:** Legacy 3D modeling tools

---

### AMF (Additive Manufacturing Format) - 2011
**Status:** ⚠️ **OBSOLETE - REPLACED BY 3MF**

**Pros:**
- Multi-material
- Curved triangles (better than STL)

**Cons:**
- ❌ Never gained wide adoption
- ❌ 3MF superseded it
- ❌ Poor slicer support

**Use Case:** None - use 3MF instead

---

### PLY (Polygon File Format)
**Status:** ⚠️ **NICHE**

**Pros:**
- Point cloud support
- Color per vertex

**Cons:**
- No parametric geometry
- Not CAD-focused
- Limited tool support

**Use Case:** 3D scanning, point clouds

---

## Recommendations

### ✅ Keep Current Exports
TiaCAD's current format support is **excellent**:

1. **3MF** - PRIMARY for 3D printing (multi-material capable!)
2. **STEP** - For CAD tool exchange
3. **STL** - Legacy compatibility only

### 🎯 Potential Additions (Ranked by Value)

#### 1. **glTF/GLB** ⭐⭐⭐
**Value:** HIGH for web integration
**Effort:** ~6-8 hours
**Use Case:**
- Web-based model viewers
- Documentation (embed 3D models in HTML)
- AR/VR applications
- Social media sharing (Sketchfab, etc.)

**Implementation:**
```python
# Using trimesh (already in CadQuery ecosystem)
import trimesh

def export_gltf(self, output_path: str, part_name: Optional[str] = None):
    part = self._get_export_part(part_name)
    mesh = part.geometry.val().toTrimesh()
    mesh.export(output_path, file_type='gltf')
```

#### 2. **SVG Cross-Sections** ⭐⭐
**Value:** MEDIUM for laser cutting / 2D workflows
**Effort:** ~8-10 hours
**Use Case:**
- Laser cutting templates
- Technical drawings
- Documentation
- CNC router patterns

**Implementation:**
- Slice model at Z-height
- Export 2D profile as SVG

#### 3. **VRML/X3D** ⭐
**Value:** LOW (mostly obsolete)
**Effort:** ~4 hours
**Use Case:** Legacy scientific visualization

---

## Format Decision Matrix

| Format | 3D Printing | CAD Exchange | Web Viewing | Exact Geometry | Multi-Material | TiaCAD Support |
|--------|------------|--------------|-------------|----------------|----------------|----------------|
| **STL** | ⚠️ Legacy | ❌ No | ❌ No | ❌ Tessellation | ❌ No | ✅ YES |
| **3MF** | ✅ BEST | ⚠️ Some | ❌ No | ❌ Tessellation | ✅ YES | ✅ **YES** |
| **STEP** | ❌ No | ✅ BEST | ❌ No | ✅ Parametric | ⚠️ Limited | ✅ YES |
| **glTF** | ❌ No | ❌ No | ✅ BEST | ❌ Tessellation | ✅ PBR | ❌ No |
| **OBJ** | ❌ No | ❌ No | ⚠️ Old | ❌ Tessellation | ⚠️ MTL | ❌ No |

---

## Conclusion

### **TiaCAD Already Has The Best Formats!** 🎉

Your current export support is **excellent**:

1. **3MF** - Modern 3D printing standard with multi-material ← **KEEP PROMOTING THIS!**
2. **STEP** - CAD interchange ← **KEEP**
3. **STL** - Legacy fallback ← **KEEP but de-emphasize**

### Recommended Next Step

**DON'T add new formats yet.** Instead:

1. **Make 3MF the default export** (it's objectively better than STL)
2. **Document 3MF advantages** in user-facing docs
3. **Add examples showing multi-material 3MF exports**

### If You MUST Add Something

**Add glTF/GLB export** for web integration:
- Enables web-based model previews
- Good for documentation sites
- Modern standard with great library support

**Implementation Path:**
```bash
# Already have the dependencies
pip install trimesh  # May already be installed via CadQuery

# Export is trivial
mesh = cadquery_geometry.toTrimesh()
mesh.export("model.glb", file_type='glb')
```

---

## 3MF vs STL: The Numbers

| Metric | STL | 3MF |
|--------|-----|-----|
| **File Size** | 10 MB | 5 MB (50% smaller) |
| **Multi-Material** | ❌ No | ✅ Yes |
| **Colors** | ❌ No | ✅ Yes |
| **Metadata** | ❌ No | ✅ Yes |
| **Units** | ❌ Ambiguous | ✅ Explicit |
| **Slicer Support** | 100% (legacy) | 95% (modern) |

**Verdict:** Use 3MF unless you NEED legacy tool support.

---

## TiaCAD Export Recommendation

**Update your examples and docs to showcase 3MF:**

```yaml
# Guitar hanger example - export as 3MF with multi-material
export:
  default_part: assembly
  parts:
    - name: plate_with_holes
      description: Mounting plate
      material: PLA
      color: "#FF5733"
    - name: left_arm
      description: Left arm
      material: TPU
      color: "#33FF57"  # ← Different material/color!
```

Then:
```bash
tiacad build guitar_hanger.yaml --output hanger.3mf
# Open in PrusaSlicer → materials automatically assigned! 🎉
```

---

## Summary

**Status:** ✅ TiaCAD's export support is **excellent** - no urgent need for changes

**Current Strengths:**
- 3MF with multi-material (modern, best-in-class)
- STEP for CAD (industry standard)
- STL for legacy (universal compatibility)

**Potential Future Addition:**
- glTF/GLB for web visualization (moderate value, easy to add)

**Don't Bother With:**
- OBJ (obsolete)
- AMF (dead standard)
- VRML/X3D (niche)

**Action Item:**
- **Promote 3MF as your primary export format in docs**
- Show off the multi-material capabilities!
- Maybe add a "why 3MF is better than STL" section to user docs

---

*Analysis completed: 2025-11-02*
*Current TiaCAD export support: 3 formats, all excellent choices*
