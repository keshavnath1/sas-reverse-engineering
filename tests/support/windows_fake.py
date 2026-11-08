"""Independent hostile memory-only Windows fixture preserves retained object identities across replacement.

This is not Windows, NTFS, an OS emulator, or native qualification evidence; no source/store path is opened."""

from dataclasses import dataclass, field

from support.cp2_vectors import RAW_OTHER, RAW_VARIANTS
from sas_re._filesystem._windows_native import (
    DirectoryEntry,
    ObjectIdentity,
    ObjectInfo,
    VolumeInfo,
)


DIRECTORY = 0x10
REPARSE = 0x400


@dataclass
class Node:
    label: str
    number: int
    directory: bool = False
    data: bytes = b""
    children: dict = field(default_factory=dict)
    links: int = 1
    delete_pending: bool = False
    attributes: int = 0
    reparse_tag: int = 0
    created: int = 100
    modified: int = 200
    changed: int = 300
    serial: int = 0x19742
    filesystem: str = "NTFS"
    volume_flags: int = 0x400AC
    reported_size: int | None = None
    deny_metadata: bool = False
    deny_data: bool = False
    deny_entries: bool = False
    native_unsafe: bool = False

    @property
    def file_id(self):
        return self.number.to_bytes(16, "little")

    def info(self):
        return ObjectInfo(
            ObjectIdentity(self.serial, self.file_id),
            self.directory,
            len(self.data) if self.reported_size is None else self.reported_size,
            self.links,
            self.delete_pending,
            self.attributes,
            self.created,
            self.modified,
            self.changed,
            self.reparse_tag,
        )


class FakeWindows:
    """Read-only API double with an independent all-handles/read-order oracle."""

    def __init__(self, testcase, variant="lf"):
        self.testcase = testcase
        self.sequence = 0
        self.events = []
        self.active = {}
        self.next_handle = 100
        self.before = None
        self.after = None
        self.entries_override = None
        self.close_failure = False
        self.closed = []
        self.root = self.node("volume", directory=True)
        self.anchor = self.node("Synthetic", directory=True)
        self.source = self.node("Sources", directory=True)
        self.logs = self.node("Logs", directory=True)
        self.includes = self.node("includes", directory=True)
        self.root.children["Synthetic"] = self.anchor
        self.anchor.children.update(Sources=self.source, Logs=self.logs)
        self.output_parent = self.node("NewOutput", directory=True)
        self.store = self.node("store", directory=True)
        self.output_parent.children["store"] = self.store
        self.anchor.children["NewOutput"] = self.output_parent
        self.source.children["includes"] = self.includes
        self.expected = {"src:main.sas": RAW_VARIANTS[variant], **RAW_OTHER}
        self.files = {}
        for key, parent, name in (
            ("src:main.sas", self.source, "main.sas"),
            ("src:includes/common.sas", self.includes, "common.sas"),
            ("logs:run.log", self.logs, "run.log"),
        ):
            self.files[key] = self.node(name, data=self.expected[key])
            parent.children[name] = self.files[key]
        self.expected_nodes = set(id(node) for node in self.files.values())
        self.root_handle = self._handle(self.root, False)

    def node(self, label, *, directory=False, data=b""):
        self.sequence += 1
        return Node(label, self.sequence, directory, data, attributes=DIRECTORY if directory else 0)

    def _handle(self, node, data):
        handle = self.next_handle
        self.next_handle += 1
        self.active[handle] = [node, data, 0]
        return handle

    def _event(self, operation, *arguments):
        self.events.append((operation, *arguments))
        if self.before:
            self.before(operation, *arguments)

    def _done(self, operation, result, *arguments):
        if self.after:
            self.after(operation, result, *arguments)
        return result

    def open_child(self, parent, name, *, directory, read_data=False):
        self._event("open", parent, name, directory, read_data)
        self.testcase.assertIs(type(name), str)
        self.testcase.assertTrue(name and name not in {".", ".."})
        self.testcase.assertFalse(any(item in name for item in ("/", "\\", ":", "\x00")))
        owner = self.active[parent][0]
        self.testcase.assertTrue(owner.directory)
        if name not in owner.children:
            raise FileNotFoundError("synthetic missing name")
        node = owner.children[name]
        if node.deny_metadata or (read_data and node.deny_data):
            raise PermissionError("synthetic denied access")
        if node.directory != directory or node.native_unsafe:
            raise OSError("synthetic native object refusal")
        if read_data:
            # This oracle is independent of any candidate ready/stage marker.
            inspected = {event[1] for event in self.events if event[0] == "inspect"}
            bound = {id(self.active[h][0]) for h in inspected if h in self.active}
            self.testcase.assertTrue(
                self.expected_nodes <= bound, "Data handle opened before all file metadata"
            )
            scanned = {
                id(self.active[event[1]][0])
                for event in self.events
                if event[0] == "entries" and event[1] in self.active
            }
            self.testcase.assertTrue(
                {id(self.source), id(self.logs), id(self.includes)} <= scanned,
                "Data handle opened before complete membership",
            )
        return self._done("open", self._handle(node, read_data), parent, name, directory, read_data)

    def inspect(self, handle):
        self._event("inspect", handle)
        node = self.active[handle][0]
        if node.native_unsafe:
            raise OSError("synthetic non-disk or inheritable handle")
        return self._done("inspect", node.info(), handle)

    def volume(self, handle):
        self._event("volume", handle)
        node = self.active[handle][0]
        value = VolumeInfo(node.filesystem, node.serial & 0xFFFFFFFF, 255, node.volume_flags)
        return self._done("volume", value, handle)

    def entries(self, handle):
        self._event("entries", handle)
        node = self.active[handle][0]
        self.testcase.assertTrue(node.directory)
        if node.deny_entries:
            raise PermissionError("synthetic denied listing")
        result = tuple(
            DirectoryEntry(
                name, child.file_id, child.attributes, len(child.data), child.reparse_tag
            )
            for name, child in node.children.items()
        )
        if self.entries_override:
            result = self.entries_override(node, result)
        return self._done("entries", result, handle)

    def read(self, handle, limit):
        self._event("read", handle, limit)
        held = {id(entry[0]) for entry in self.active.values() if entry[1]}
        self.testcase.assertTrue(
            self.expected_nodes <= held, "Source byte read before every required read handle"
        )
        node, data, position = self.active[handle]
        self.testcase.assertTrue(data)
        self.testcase.assertFalse(node.directory)
        self.testcase.assertGreater(limit, 0)
        self.testcase.assertLessEqual(limit, 65536)
        result = node.data[position : position + limit]
        self.active[handle][2] += len(result)
        return self._done("read", result, handle, limit)

    def rewind(self, handle):
        self._event("rewind", handle)
        self.testcase.assertTrue(self.active[handle][1])
        self.active[handle][2] = 0

    def close(self, handle):
        self._event("close", handle)
        self.testcase.assertNotIn(handle, self.closed, "A handle close was retried")
        self.closed.append(handle)
        del self.active[handle]
        if self.close_failure:
            self.close_failure = False
            raise OSError("synthetic uncertain close after release")

    def reads(self):
        return [event for event in self.events if event[0] == "read"]

    def data_opens(self):
        return [event for event in self.events if event[0] == "open" and event[4]]

    def snapshot(self):
        """Independent bytes/metadata/name inventory; never invokes candidate code."""

        def visit(node, ancestors):
            if id(node) in ancestors:
                return ("alias", node.number)
            return (
                node.number,
                node.directory,
                node.data,
                node.links,
                node.delete_pending,
                node.attributes,
                node.reparse_tag,
                node.created,
                node.modified,
                node.changed,
                node.serial,
                tuple(
                    (name, visit(child, ancestors | {id(node)}))
                    for name, child in sorted(node.children.items())
                ),
            )

        return visit(self.root, set())
