#!/usr/bin/env python3
"""Milestone 0, Task 0.1 - host topology profiling + salted parameters.

Usage: python3 src/profile_env.py --student-id 12345678
Writes results/host_profile.json and results/salted_params.json.
Linux: /proc/cpuinfo + /sys ; macOS: sysctl ; fallback: platform / psutil.
"""
import argparse
import glob
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from salt import get_student_params  # noqa: E402

UNITS = {"": 1, "K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}


def sh(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout.strip()
    except Exception:
        return ""


def sysctl(key):
    return sh("sysctl", "-n", key) or None


def parse_size(s):
    """'48K', '2048K', '32M', '48 KiB (1 instance)' -> bytes."""
    if not s:
        return None
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*([KMG]?)", str(s).strip(), re.I)
    return int(float(m.group(1)) * UNITS[m.group(2).upper()]) if m else None


INTEL = {  # (family, model) -> microarchitecture (best-effort lookup)
    (6, 63): "Haswell-EP", (6, 79): "Broadwell-EP", (6, 85): "Skylake-SP / Cascade Lake",
    (6, 94): "Skylake-client", (6, 142): "Kaby/Coffee Lake", (6, 158): "Kaby/Coffee Lake",
    (6, 106): "Ice Lake-SP", (6, 108): "Ice Lake-SP", (6, 125): "Ice Lake-client",
    (6, 140): "Tiger Lake", (6, 141): "Tiger Lake", (6, 151): "Alder Lake",
    (6, 154): "Alder Lake", (6, 183): "Raptor Lake", (6, 191): "Raptor Lake",
    (6, 143): "Sapphire Rapids", (6, 207): "Emerald Rapids", (6, 173): "Granite Rapids",
    (6, 170): "Meteor Lake", (6, 189): "Lunar Lake", (6, 197): "Arrow Lake",
}
AMD = {23: "Zen / Zen+ / Zen 2", 25: "Zen 3 / Zen 4", 26: "Zen 5"}


def guess_microarch(vendor, family, model):
    try:
        family, model = int(family), int(model)
    except (TypeError, ValueError):
        return "unknown"
    if "Intel" in (vendor or ""):
        return INTEL.get((family, model), f"unknown Intel (family {family}, model {model})")
    if "AMD" in (vendor or ""):
        return AMD.get(family, f"unknown AMD (family {family})")
    return "unknown"


def linux_cpuinfo():
    info = {}
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if not line.strip():
                    if info:
                        break
                    continue
                k, _, v = line.partition(":")
                info[k.strip()] = v.strip()
    except OSError:
        pass
    return info


def linux_physical_cores():
    ids = set()
    for d in glob.glob("/sys/devices/system/cpu/cpu[0-9]*"):
        try:
            pkg = open(d + "/topology/physical_package_id").read().strip()
            core = open(d + "/topology/core_id").read().strip()
            ids.add((pkg, core))
        except OSError:
            pass
    return len(ids) or None


def linux_caches():
    out = {"l1d": None, "l1i": None, "l2": None, "l3": None, "line": None}
    for d in sorted(glob.glob("/sys/devices/system/cpu/cpu0/cache/index*")):
        def rd(n):
            try:
                return open(f"{d}/{n}").read().strip()
            except OSError:
                return None
        lvl, typ, size, line = rd("level"), rd("type"), parse_size(rd("size")), rd("coherency_line_size")
        if line:
            out["line"] = int(line)
        if lvl == "1" and typ == "Data":
            out["l1d"] = size
        elif lvl == "1" and typ == "Instruction":
            out["l1i"] = size
        elif lvl == "2":
            out["l2"] = size
        elif lvl == "3":
            out["l3"] = size
    if out["l1d"] is None:  # fallback: lscpu
        for line in sh("lscpu").splitlines():
            k, _, v = line.partition(":")
            key = {"l1d cache": "l1d", "l1i cache": "l1i", "l2 cache": "l2",
                   "l3 cache": "l3"}.get(k.strip().lower())
            if key:
                out[key] = parse_size(v)
    return out


def mac_caches():
    def g(*keys):
        for k in keys:
            v = sysctl(k)
            if v:
                return parse_size(v)
        return None
    line = sysctl("hw.cachelinesize")
    return {"l1d": g("hw.perflevel0.l1dcachesize", "hw.l1dcachesize"),
            "l1i": g("hw.perflevel0.l1icachesize", "hw.l1icachesize"),
            "l2": g("hw.perflevel0.l2cachesize", "hw.l2cachesize"),
            "l3": g("hw.l3cachesize"), "line": int(line) if line else None}


def freq_info(model_name, cpuinfo):
    """base GHz, max GHz, source string."""
    base = src = mx = None
    try:
        base = int(open("/sys/devices/system/cpu/cpu0/cpufreq/base_frequency").read()) / 1e6
        src = "sysfs base_frequency"
    except (OSError, ValueError):
        pass
    try:
        mx = int(open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").read()) / 1e6
    except (OSError, ValueError):
        pass
    if base is None:
        m = re.search(r"@\s*([\d.]+)\s*GHz", model_name or "")
        if m:
            base, src = float(m.group(1)), "model-name string"
    if base is None and platform.system() == "Darwin":
        hz = sysctl("hw.cpufrequency")
        if hz:
            base, src = int(hz) / 1e9, "sysctl hw.cpufrequency"
    if base is None and cpuinfo.get("cpu MHz"):
        base, src = float(cpuinfo["cpu MHz"]) / 1000, "/proc/cpuinfo cpu MHz (current, approximate)"
    if base is None:
        try:
            import psutil
            f = psutil.cpu_freq()
            if f:
                base, src = (f.max or f.current) / 1000, "psutil"
        except Exception:
            pass
    return base, mx, src


def collect():
    system = platform.system()
    logical = os.cpu_count()
    try:
        usable = len(os.sched_getaffinity(0))
    except AttributeError:
        usable = logical
    cpuinfo, flags = {}, []
    if system == "Linux":
        cpuinfo = linux_cpuinfo()
        model = cpuinfo.get("model name")
        if not model:
            model = (sh("lscpu").split("Model name:")[-1].splitlines() or ["unknown"])[0].strip()
        arch = guess_microarch(cpuinfo.get("vendor_id"), cpuinfo.get("cpu family"), cpuinfo.get("model"))
        physical = linux_physical_cores()
        caches = linux_caches()
        flags = cpuinfo.get("flags", cpuinfo.get("Features", "")).split()
        stepping = cpuinfo.get("stepping")
    elif system == "Darwin":
        model = sysctl("machdep.cpu.brand_string") or platform.processor()
        if platform.machine() == "arm64":
            arch = "Apple Silicon (arm64)"
        else:
            arch = guess_microarch("Intel", sysctl("machdep.cpu.family"), sysctl("machdep.cpu.model"))
        p = sysctl("hw.physicalcpu")
        physical = int(p) if p else None
        caches = mac_caches()
        flags = (sysctl("machdep.cpu.features") or "").lower().split()
        stepping = sysctl("machdep.cpu.stepping")
    else:
        model, arch, stepping = platform.processor() or "unknown", "unknown", None
        physical, caches = None, {"l1d": None, "l1i": None, "l2": None, "l3": None, "line": None}
    if physical is None:
        try:
            import psutil
            physical = psutil.cpu_count(logical=False)
        except Exception:
            physical = logical
    base, mx, src = freq_info(model, cpuinfo)
    smt = bool(logical and physical and logical > physical)
    simd = [f for f in ("sse4_2", "avx", "avx2", "fma", "avx512f", "avx512bw", "amx_tile", "neon", "asimd")
            if f in flags]
    mem = None
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal"):
                mem = int(line.split()[1]) * 1024
                break
    except OSError:
        pass
    try:
        import numpy
        np_v = numpy.__version__
    except ImportError:
        np_v = None
    return {
        "cpu": {
            "model_name": model, "vendor": cpuinfo.get("vendor_id"), "microarchitecture": arch,
            "family": cpuinfo.get("cpu family"), "model": cpuinfo.get("model"), "stepping": stepping,
            "base_freq_ghz": base, "base_freq_source": src, "max_freq_ghz": mx,
            "physical_cores": physical, "logical_threads": logical,
            "smt_hyperthreading": smt, "usable_cpus_for_this_process": usable,
            "simd_flags": simd,
        },
        "cache": {
            "l1d_bytes": caches["l1d"], "l1i_bytes": caches["l1i"], "l2_bytes": caches["l2"],
            "l3_shared_bytes": caches["l3"], "cache_line_bytes": caches["line"] or 64,
        },
        "memory_total_bytes": mem,
        "os": {"system": system, "kernel_release": platform.release(),
               "kernel_version": platform.version(), "machine": platform.machine(),
               "platform": platform.platform()},
        "python": {"implementation": platform.python_implementation(), "version": platform.python_version(),
                   "compiler": platform.python_compiler(), "numpy": np_v},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student-id", required=True, help="8-digit student ID")
    ap.add_argument("--out-dir", default=str(ROOT / "results"))
    a = ap.parse_args()
    if not re.fullmatch(r"\d{8}", a.student_id):
        print("warning: student id is not 8 digits", file=sys.stderr)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    prof = collect()
    (out / "host_profile.json").write_text(json.dumps(prof, indent=2))
    params = get_student_params(a.student_id)
    (out / "salted_params.json").write_text(json.dumps(params, indent=2))
    c, k = prof["cpu"], prof["cache"]
    print(f"CPU: {c['model_name']}  [{c['microarchitecture']}]  base {c['base_freq_ghz']} GHz")
    print(f"cores: {c['physical_cores']} physical / {c['logical_threads']} logical (SMT={c['smt_hyperthreading']})")
    print(f"cache: L1d={k['l1d_bytes']} L2={k['l2_bytes']} L3={k['l3_shared_bytes']} line={k['cache_line_bytes']}")
    print("salted params:", params)


if __name__ == "__main__":
    main()
