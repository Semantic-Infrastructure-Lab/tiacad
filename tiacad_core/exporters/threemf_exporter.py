"""
3MF Exporter for TiaCAD

Exports TiaCAD models to 3MF format with full multi-material support.

3MF (3D Manufacturing Format) is the modern standard for 3D printing,
supporting:
- Multi-material/multi-color printing
- Material properties and metadata
- Assembly information
- Print settings

This exporter leverages TiaCAD's color system to create production-ready
3MF files that work with modern slicers (PrusaSlicer, BambuStudio, OrcaSlicer).
"""

import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ThreeMFExportError(Exception):
    """Error during 3MF export"""
    pass


class ThreeMFExporter:
    """
    Export TiaCAD parts to 3MF format with materials.

    Uses lib3mf (official 3MF Consortium library) for standards-compliant
    3MF file generation.
    """

    def __init__(self):
        """Initialize 3MF exporter"""
        self._check_lib3mf()

    def _check_lib3mf(self):
        """Check if lib3mf is available, provide helpful error if not"""
        try:
            import lib3mf
            self.lib3mf = lib3mf
            self.wrapper = lib3mf.Wrapper()
            logger.debug("lib3mf loaded successfully")
        except ImportError as e:
            raise ThreeMFExportError(
                "lib3mf library not installed. Install with: pip install lib3mf"
            ) from e

    def export(
        self,
        parts_registry,
        output_path: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Export all parts to 3MF file with materials.

        Args:
            parts_registry: PartRegistry with all parts to export
            output_path: Path to output .3mf file
            metadata: Optional document metadata

        Raises:
            ThreeMFExportError: If export fails
        """
        try:
            # Create new 3MF model
            model = self.wrapper.CreateModel()

            # Collect unique materials from all parts
            material_map = self._create_material_groups(model, parts_registry)

            # Add each part as a mesh object
            part_objects = []
            for part_name in parts_registry.list_parts():
                part = parts_registry.get(part_name)

                # Create mesh object from CadQuery geometry
                mesh_object = self._create_mesh_object(model, part, part_name)

                # Assign material if part has color/material
                if 'color' in part.metadata or 'material' in part.metadata:
                    self._assign_material(
                        mesh_object,
                        part,
                        material_map
                    )

                part_objects.append(mesh_object)

            # Add all parts to build
            self._add_to_build(model, part_objects)

            # Add metadata if provided
            if metadata:
                self._add_metadata(model, metadata)

            # Write 3MF file
            writer = model.QueryWriter("3mf")
            writer.WriteToFile(str(output_path))

            logger.info(
                f"Exported {len(part_objects)} parts to {output_path} "
                f"with {len(material_map)} materials"
            )

        except Exception as e:
            raise ThreeMFExportError(
                f"Failed to export 3MF: {str(e)}"
            ) from e

    def _create_material_groups(self, model, parts_registry) -> Dict[str, Tuple]:
        """
        Create BaseMaterialGroup with all unique materials.

        Returns:
            material_map: Dict mapping material_key -> (resource_id, property_id)
        """
        # Collect unique materials
        unique_materials = {}

        for part_name in parts_registry.list_parts():
            part = parts_registry.get(part_name)

            # Determine material key
            if 'material' in part.metadata:
                # Named material from library
                mat_key = f"mat_{part.metadata['material']}"
                if mat_key not in unique_materials:
                    # Get RGBA from metadata
                    if 'color' in part.metadata:
                        r, g, b, a = part.metadata['color']
                        unique_materials[mat_key] = {
                            'name': part.metadata['material'],
                            'color': (r, g, b, a)
                        }

            elif 'color' in part.metadata:
                # Color-only (no named material)
                r, g, b, a = part.metadata['color']
                # Create key from color
                mat_key = f"color_{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                if mat_key not in unique_materials:
                    unique_materials[mat_key] = {
                        'name': f"Color RGB({int(r*255)},{int(g*255)},{int(b*255)})",
                        'color': (r, g, b, a)
                    }

        # No materials? Return empty map
        if not unique_materials:
            logger.debug("No materials found, using default gray")
            return {}

        # Create BaseMaterialGroup
        material_group = model.AddBaseMaterialGroup()
        group_resource_id = material_group.GetResourceID()

        # Add each material to the group
        material_map = {}
        for mat_key, mat_info in unique_materials.items():
            # Create lib3mf Color
            r, g, b, a = mat_info['color']
            color = self.lib3mf.Color()
            color.Red = int(r * 255)
            color.Green = int(g * 255)
            color.Blue = int(b * 255)
            color.Alpha = int(a * 255)

            # Add material and get PropertyID
            property_id = material_group.AddMaterial(
                mat_info['name'],
                color
            )

            # Store mapping
            material_map[mat_key] = (group_resource_id, property_id)

            logger.debug(
                f"Added material '{mat_info['name']}' "
                f"(RGB: {int(r*255)}, {int(g*255)}, {int(b*255)})"
            )

        return material_map

    def _create_mesh_object(self, model, part, part_name: str):
        """
        Create mesh object from CadQuery geometry.

        Args:
            model: lib3mf Model
            part: Part object with CadQuery geometry
            part_name: Name of the part

        Returns:
            MeshObject with triangulated geometry
        """
        # Create mesh object
        mesh_object = model.AddMeshObject()
        mesh_object.SetName(part_name)

        # Get mesh from CadQuery geometry using built-in tessellate()
        try:
            # Get CadQuery shape
            shape = part.geometry.val()

            # Tessellate with tolerance (smaller = finer mesh)
            # 0.1 is a good balance between quality and file size
            cq_vertices, cq_triangles = shape.tessellate(0.1)

            # Convert CadQuery vertices to lib3mf Position objects
            vertices = []
            for v in cq_vertices:
                vertex = self.lib3mf.Position()
                # Set coordinates individually (c_float_Array_3)
                vertex.Coordinates[0] = float(v.x)
                vertex.Coordinates[1] = float(v.y)
                vertex.Coordinates[2] = float(v.z)
                vertices.append(vertex)

            # Convert CadQuery triangles to lib3mf Triangle objects
            triangles = []
            for tri in cq_triangles:
                triangle = self.lib3mf.Triangle()
                # Set indices individually (c_uint_Array_3)
                triangle.Indices[0] = tri[0]
                triangle.Indices[1] = tri[1]
                triangle.Indices[2] = tri[2]
                triangles.append(triangle)

            # Set geometry data in mesh object
            mesh_object.SetGeometry(vertices, triangles)

            logger.debug(
                f"Created mesh for '{part_name}': "
                f"{len(vertices)} vertices, {len(triangles)} triangles"
            )

        except Exception as e:
            raise ThreeMFExportError(
                f"Failed to create mesh for part '{part_name}': {str(e)}"
            ) from e

        return mesh_object

    def _assign_material(self, mesh_object, part, material_map: Dict):
        """
        Assign material to mesh object.

        Args:
            mesh_object: lib3mf MeshObject
            part: Part with metadata
            material_map: Material mapping dictionary
        """
        # Determine material key (same logic as _create_material_groups)
        if 'material' in part.metadata:
            mat_key = f"mat_{part.metadata['material']}"
        elif 'color' in part.metadata:
            r, g, b, a = part.metadata['color']
            mat_key = f"color_{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        else:
            return  # No material to assign

        # Get material IDs
        if mat_key in material_map:
            resource_id, property_id = material_map[mat_key]

            # Assign material to object
            mesh_object.SetObjectLevelProperty(resource_id, property_id)

            logger.debug(
                f"Assigned material '{mat_key}' to '{mesh_object.GetName()}'"
            )

    def _add_to_build(self, model, part_objects: List):
        """Add all parts to the build plate"""
        for obj in part_objects:
            # Create build item
            build_item = model.AddBuildItem(obj, self.wrapper.GetIdentityTransform())
            logger.debug(f"Added '{obj.GetName()}' to build")

    def _add_metadata(self, model, metadata: Dict):
        """Add document metadata to 3MF"""
        # Add common metadata fields
        if 'name' in metadata:
            # lib3mf metadata can be added here
            # Note: lib3mf has limited metadata support in base spec
            logger.debug(f"Document name: {metadata['name']}")

        if 'description' in metadata:
            logger.debug(f"Description: {metadata['description']}")


def export_3mf(
    parts_registry,
    output_path: str,
    metadata: Optional[Dict] = None
) -> None:
    """
    Convenience function to export parts to 3MF.

    Args:
        parts_registry: PartRegistry with parts to export
        output_path: Path to output .3mf file
        metadata: Optional document metadata

    Raises:
        ThreeMFExportError: If export fails

    Example:
        >>> from tiacad_core.exporters.threemf_exporter import export_3mf
        >>> export_3mf(doc.parts, "output.3mf", doc.metadata)
    """
    exporter = ThreeMFExporter()
    exporter.export(parts_registry, output_path, metadata)
