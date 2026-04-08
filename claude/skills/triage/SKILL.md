---
name: triage
description: Use when facing hard systems integration problems — architecture mismatches, broken toolchains, multi-layer debugging, pre-built binaries that fail, or multi-hop remote execution. Provides a systematic 5-phase methodology for decomposing, diagnosing, and adapting.
---

# Triage — Systems Integration Problem Solving

**When to use:** A pre-built solution fails. A binary won't run. A toolchain is broken. You're debugging across multiple layers (host → container → VM → process). Something that "should just work" doesn't.

**Origin:** Extracted from successfully building x86_64 spice-vdagent for a macOS QEMU VM when the pre-built ARM64 binary failed and the Swift toolchain was broken — required rewriting in Objective-C and compiling from source through a 3-layer SSH chain.

---

## Phase 1: Map the Stack

**Before touching anything, draw the full system architecture.**

1. **List every layer** from your machine to the target:
   ```
   Example: local machine → SSH → Docker container → QEMU VM → guest OS → process
   ```

2. **Identify boundary crossings:**
   - Network (TCP, Unix socket, virtio)
   - IPC (pipes, shared memory, D-Bus)
   - Device nodes (`/dev/*`)
   - File mounts (bind mounts, NFS, 9p)

3. **Name each component** and its role in the pipeline:
   ```
   Example: VNC Client ←→ QEMU VNC ←→ chardev ←→ virtio-serial ←→ daemon ←→ agent ←→ clipboard
   ```

4. **Document access methods** for each layer (SSH creds, docker exec, QEMU monitor, etc.)

**Output:** A text diagram you can reference throughout. This is your map.

---

## Phase 2: Verify Bottom-Up

**Start at the lowest layer. Confirm it works. Move up.**

### Verification checklist per layer:

| Check | Command Pattern | What It Proves |
|-------|----------------|----------------|
| Binary architecture | `file /path/to/binary` | Matches target CPU (x86_64, arm64, etc.) |
| Shared libraries | `ldd` (Linux) or `otool -L` (macOS) | Dependencies exist and resolve |
| Device exists | `ls -la /dev/device` | Kernel driver loaded, device node present |
| Socket exists | `ls -la /path/to/socket` | Daemon created its IPC endpoint |
| Process running | `ps aux \| grep name` | Component is alive |
| Port listening | `ss -tlnp` or `netstat -an` | Network service is bound |
| Connectivity | `nc -z host port` | Can reach the next layer |
| Protocol status | Monitor/status command | Components are talking (e.g., QEMU `info qtree`) |

### Rules:

- **Do NOT skip layers.** If layer N isn't verified, don't debug layer N+1.
- **Log what you find.** "Layer 3: device exists, daemon running, socket present, agent NOT connected."
- **The first layer that fails is your starting point.**

---

## Phase 3: Identify the Break

**Classify the failure. The category determines the fix.**

| Failure Type | Symptoms | Example |
|-------------|----------|---------|
| **Architecture mismatch** | "Bad CPU type", "cannot execute binary", wrong ELF class | ARM64 binary on x86_64 host |
| **Missing dependency** | "library not found", "symbol not found", unresolved imports | Missing .so/.dylib at runtime |
| **Broken toolchain** | Compilation errors from SDK/compiler version mismatch | Swift SDK built with different compiler version |
| **Permission denied** | EACCES, "operation not permitted" | Process can't open device or socket |
| **Network/connectivity** | Connection refused, timeout, "no route to host" | Firewall, NAT, wrong port |
| **Protocol mismatch** | "no matching security types", version mismatch | VNC encryption requirements differ |
| **Missing component** | "command not found", file doesn't exist | Package not installed |
| **Configuration error** | Wrong paths, wrong flags, wrong options | Daemon started with wrong device path |

---

## Phase 4: Adapt

**Decision tree — pick the fix strategy based on failure type.**

### Architecture Mismatch
```
Pre-built binary wrong arch?
├── Source available? → Build from source for correct target
│   ├── Build system works? → Use it (make, cmake, autotools)
│   └── Build system broken? → Manual compilation (cc/clang with explicit flags)
└── Source unavailable? → Find alternative package or emulation layer
```

### Broken Toolchain
```
Compiler/SDK version mismatch?
├── Can install correct version? → Install it
└── Cannot fix toolchain?
    └── Rewrite in simpler language
        ├── Swift → Objective-C (same frameworks, clang always works)
        ├── Rust → C (when cargo/rustc version locked)
        ├── TypeScript → JavaScript (when tsc version conflicts)
        └── Complex build → Manual cc/clang invocation
```

**Key insight:** When rewriting, the goal is to use the **simplest toolchain that can access the same APIs.** Objective-C accesses the same Foundation/AppKit as Swift. C accesses the same POSIX as Rust. The language is just a syntax — the system interfaces are what matter.

### Build From Source
```
1. Clone the source repository
2. Read the build system (Makefile, CMakeLists.txt, configure.ac, Package.swift)
3. Identify actual source files needed (not all files — just what your target uses)
4. Install build dependencies (headers, libraries, pkg-config files)
5. Write a minimal build script:
   - Get compiler flags: pkg-config --cflags <lib>
   - Get linker flags: pkg-config --libs <lib>
   - Compile each .c/.m file to .o
   - Link all .o files with libraries and frameworks
6. Verify output: file <binary> should show correct architecture
```

### Multi-Hop Execution
```
Need to run commands through SSH/docker chains?
├── Simple command → Direct: docker exec container sh -c "cmd"
├── Complex command → Write script locally, transfer, execute:
│   1. cat > /tmp/script.sh << 'EOF' ... EOF
│   2. docker cp /tmp/script.sh container:/tmp/
│   3. docker exec container scp /tmp/script.sh user@vm:/tmp/
│   4. docker exec container ssh user@vm "chmod +x /tmp/script.sh && /tmp/script.sh"
└── NEVER nest quotes 3+ levels deep — always use the transfer pattern
```

### Iterative Compilation
```
Build fails with errors?
├── Fix ONLY the first error (later errors are often cascading)
├── Rebuild
├── If new error → fix it, rebuild
├── If same error → your fix was wrong, try different approach
└── Repeat until clean build
```

**Anti-pattern:** Don't try to fix 10 errors at once. Fix one. Rebuild. The error landscape changes with each fix.

---

## Phase 5: Persist and Verify

### Step 1: Manual verification first
```
1. Start the component manually in foreground with debug flags
2. Confirm it works end-to-end (not just "runs without errors")
3. Test the actual use case (clipboard works, data flows, API responds)
4. Check from the monitoring layer (QEMU monitor, process status, logs)
```

### Step 2: Make it persistent
```
Confirmed working manually?
├── Linux → systemd unit file (.service)
├── macOS → launchd plist (LaunchDaemon for root, LaunchAgent for user)
├── Container → entrypoint script or supervisor
└── All: set restart/KeepAlive, log to file, run at boot
```

### Step 3: Verify persistence
```
1. Restart the system/service
2. Confirm auto-start worked (process running, logs clean)
3. Re-test end-to-end functionality
```

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Fix all compilation errors at once | Fix first error, rebuild, repeat |
| Nest 3+ levels of shell quoting | Write script file, transfer, execute |
| Assume binary matches your platform | `file <binary>` before running |
| Debug layer N+1 before verifying layer N | Bottom-up, always |
| Make persistent before manual verification | Manual first, persist after confirmed |
| Try to force a broken toolchain to work | Rewrite in simpler language that works |
| Guess at CLI flags | Read the source for option parsing (grep `GOptionEntry`, `argparse`, `getopt`) |
| Run complex remote commands inline | Transfer a script file |

---

## Quick Reference: Diagnostic Commands

| Need | Linux | macOS |
|------|-------|-------|
| Binary arch | `file bin` | `file bin` |
| Shared deps | `ldd bin` | `otool -L bin` |
| Open files | `lsof -p PID` | `lsof -p PID` |
| Listening ports | `ss -tlnp` | `lsof -iTCP -sTCP:LISTEN` |
| Device nodes | `ls -la /dev/X` | `ls -la /dev/X` |
| Process tree | `pstree -p` | `pstree PID` |
| Kernel modules | `lsmod` | `kextstat` |
| Service status | `systemctl status X` | `launchctl list \| grep X` |
| Persistent service | `systemctl enable X` | LaunchDaemon plist |
| Compiler flags | `pkg-config --cflags lib` | `pkg-config --cflags lib` |
| Linker flags | `pkg-config --libs lib` | `pkg-config --libs lib` |
