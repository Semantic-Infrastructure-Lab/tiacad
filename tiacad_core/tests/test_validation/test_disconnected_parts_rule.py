"""
Unit tests for DisconnectedPartsRule's trust-render annotation support (TCAD-UX-5
follow-on): the reported issue's world_position should land on the smallest
disconnected group -- the "orphan" a modeler actually needs to look at -- not
the main body the rest of the assembly is attached to.
"""

from tiacad_core.geometry.cadquery_backend import CadQueryBackend
from tiacad_core.part import Part, PartRegistry
from tiacad_core.validation.rules.disconnected_parts_rule import DisconnectedPartsRule


class TestDisconnectedPartsWorldPosition:
    def test_orphan_part_position_is_reported(self):
        backend = CadQueryBackend()
        registry = PartRegistry()
        # Two touching boxes (one component) at the origin...
        registry.add(Part("main_a", backend.create_box(10, 10, 10), backend=backend))
        registry.add(Part(
            "main_b",
            backend.translate(backend.create_box(10, 10, 10), (10, 0, 0)),
            backend=backend,
        ))
        # ...and one box far away, disconnected from both.
        orphan = backend.translate(backend.create_box(4, 4, 4), (1000, 1000, 1000))
        registry.add(Part("orphan", orphan, backend=backend))

        class MockDoc:
            parts = registry

        issues = DisconnectedPartsRule().check(MockDoc())

        assert len(issues) == 1
        issue = issues[0]
        assert issue.world_position is not None
        # The smallest disconnected group is the single orphan part, centered
        # near (1002, 1002, 1002) -- far from the main pair at the origin.
        assert issue.world_position[0] > 900

    def test_connected_assembly_has_no_issue(self):
        backend = CadQueryBackend()
        registry = PartRegistry()
        registry.add(Part("a", backend.create_box(10, 10, 10), backend=backend))
        registry.add(Part(
            "b",
            backend.translate(backend.create_box(10, 10, 10), (10, 0, 0)),
            backend=backend,
        ))

        class MockDoc:
            parts = registry

        issues = DisconnectedPartsRule().check(MockDoc())
        assert issues == []
