# -*- coding: utf-8 -*-
"""Print exception info and readable strings near the stack of the crashing thread."""
import re
import sys
from pathlib import Path

from minidump.minidumpfile import MinidumpFile

DOCS = Path.home() / "Documents" / "Paradox Interactive" / "Hearts of Iron IV"
dump = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted((DOCS / "crashes").glob("hoi4_*"))[-1] / "minidump.dmp"
mf = MinidumpFile.parse(str(dump))
reader = mf.get_reader()

exc = mf.exception.exception_records[0]
rec = exc.ExceptionRecord
print("dump:", dump.parent.name)
print("code:", rec.ExceptionCode, "addr:", hex(rec.ExceptionAddress),
      "info:", [hex(x) for x in rec.ExceptionInformation[: rec.NumberParameters]])
tid = exc.ThreadId

hoi = next(m for m in mf.modules.modules if m.name.lower().endswith("hoi4.exe"))
print("hoi4 base:", hex(hoi.baseaddress), "crash rva:", hex(rec.ExceptionAddress - hoi.baseaddress))

thread = next(t for t in mf.threads.threads if t.ThreadId == tid)
ctx_rsp = None
try:
    ctx = thread.ContextObject
    ctx_rsp = ctx.Rsp
    regs = {r: getattr(ctx, r) for r in ("Rax", "Rbx", "Rcx", "Rdx", "Rsi", "Rdi", "R8", "R9", "Rsp", "Rip")}
    print("regs:", {k: hex(v) for k, v in regs.items()})
except Exception as e:  # noqa: BLE001
    print("no context:", e)

stack = thread.Stack
lo = stack.StartOfMemoryRange
size = stack.MemoryLocation.DataSize
start = ctx_rsp or lo
data = reader.read(start, min(0x6000, lo + size - start))


def strings_at(ptr: int):
    try:
        b = reader.read(ptr, 160)
    except Exception:  # noqa: BLE001
        return None
    m = re.match(rb"[\x20-\x7e]{5,}", b)
    return m.group().decode() if m else None


seen = set()
print("---- strings referenced from stack")
for off in range(0, len(data) - 8, 8):
    ptr = int.from_bytes(data[off: off + 8], "little")
    if ptr < 0x10000 or ptr in seen:
        continue
    seen.add(ptr)
    s = strings_at(ptr)
    if s:
        print(f"+{off:#06x} -> {s[:120]}")
for m in re.finditer(rb"[\x20-\x7e]{6,}", data):
    print("inline:", m.group()[:120].decode())
