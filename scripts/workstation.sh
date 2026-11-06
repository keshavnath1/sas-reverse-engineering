#!/bin/bash
# WS-1: inspect only. Start with a trusted Bash/parent environment (no BASH_ENV).
# Authenticate the LF launcher externally BEFORE Bash interprets it. See WS1_DESIGN.
shopt -u nocasematch
usage() { printf '%s\n' 'WS1 usage: workstation.sh {--help|--version|status}' >&2; exit 2; }
blocked() { printf 'WS1 BLOCKED: bootstrap: %s\n' "$1" >&2; exit 2; }
[[ $# == 1 ]] || usage
case "$1" in --help|--version|status) ;; *) usage ;; esac

# Provision only in an independently authenticated kit copy. No runtime override.
readonly approval_pin=''
readonly approval_file=''
[[ $approval_pin =~ ^[0-9a-f]{64}$ && -n $approval_file ]] ||
    blocked 'an independently approved installation inventory and pinned digest are required'

case ${BASH_VERSINFO[5]} in
    *-apple-darwin*) host=darwin; hash_tool=(/usr/bin/shasum -a 256); stat_fmt=(-f %z); link_fmt=(-f %l) ;;
    *-pc-msys*)      host=win32;  hash_tool=(/usr/bin/sha256sum); stat_fmt=(-c %s); link_fmt=(-c %h) ;;
    x86_64-*-linux-gnu*) host=linux; hash_tool=(/usr/bin/sha256sum); stat_fmt=(-c %s); link_fmt=(-c %h) ;; # regression host
    *) blocked 'unsupported Bash host' ;;
esac
# Reading paths in a record cannot select code: only the complete pinned bytes
# of a regular, bounded manifest from the externally verified location qualify.
case "$approval_file" in /*|[A-Za-z]:/*) ;; *) blocked 'invalid approval location' ;; esac
[[ -f $approval_file && ! -L $approval_file && -x ${hash_tool[0]} ]] ||
    blocked 'trusted inventory or host verifier unavailable'
cd / || blocked 'trusted working directory unavailable'
clean_env=(/usr/bin/env -i)
if [[ $host == win32 ]]; then
    # These OS values belong to the trusted host, not to the kit/source data.
    clean_env+=("SystemRoot=${SYSTEMROOT:-${SystemRoot:-}}" "WINDIR=${WINDIR:-}")
fi
hash_input() { "${clean_env[@]}" LC_ALL=C "${hash_tool[@]}"; }
single_link() {
    local links
    links=$("${clean_env[@]}" /usr/bin/stat "${link_fmt[@]}" "$1" 2>/dev/null) && [[ $links == 1 ]]
}
fits() {
    local size
    size=$("${clean_env[@]}" /usr/bin/stat "${stat_fmt[@]}" "$1" 2>/dev/null) || return 1
    [[ $size =~ ^[0-9]{1,10}$ ]] && (( 10#$size <= $2 ))
}
matches_file() {
    local sum
    # Only this fixed digest utility is used in command substitution; no record
    # or caller text is parsed as a command, and filenames do not enter its output.
    sum=$(hash_input 2>/dev/null < "$1") || return 1
    [[ ${sum%% *} == "$2" ]]
}

# Twelve LF-terminated lines, each <4096 characters. No pipes or temp files
# carrying manifest data to an interpreter. Never source this record.
fields=()
read_record() {
    local i line
    for ((i=0; i<12; i++)); do
        IFS= read -r -n 4096 line || return 1
        [[ -n $line && ${#line} -lt 4096 && $line != *$'\r'* ]] || return 1
        fields+=("$line")
    done
    ! IFS= read -r -n 1 line
}
single_link "$approval_file" && fits "$approval_file" 65536 && read_record 2>/dev/null < "$approval_file" ||
    blocked 'malformed approval inventory'
matches_file "$approval_file" "$approval_pin" || blocked 'approval digest mismatch'
# Enforce byte-exact LF framing, including on Bash versions which skip NULs.
framed_sum=$(printf '%s\n' "${fields[@]}" | hash_input) || blocked 'inventory framing unavailable'
[[ ${framed_sum%% *} == "$approval_pin" && ${fields[0]} == WS1-APPROVAL-1 &&
   ${fields[1]} == "$host" ]] || blocked 'invalid inventory or incompatible host'
for i in 8 9 11; do
    [[ ${fields[i]} =~ ^[0-9a-f]{64}$ ]] || blocked 'invalid installation digest'
done
[[ ${fields[10]} =~ ^[0-9]{1,8}\.[0-9]{1,8}\.[0-9]{1,8}$ ]] || blocked 'invalid package version'
py=${fields[2]}
[[ ${SAS_RE_PYTHON+x} != x || $SAS_RE_PYTHON == "$py" ]] ||
    blocked 'SAS_RE_PYTHON is not the approved executable'
case "$host:$py" in
    win32:[a-zA-Z]:/*/Scripts/python.exe|win32:/[a-zA-Z]/*/Scripts/python.exe)
        root=${py%/Scripts/python.exe} ;;
    darwin:/*/bin/python|linux:/*/bin/python) root=${py%/bin/python} ;;
    *) blocked 'invalid absolute environment interpreter path' ;;
esac
case "$py/" in *//*|*/../*|*/./*) blocked 'ambiguous environment path' ;; esac
cfg=$root/pyvenv.cfg
[[ -f $py && -x $py && -f $cfg && ! -L $cfg &&
   ! -e ${py%/*}/pyvenv.cfg && ! -L ${py%/*}/pyvenv.cfg ]] ||
    blocked 'approved virtual environment is unavailable'
listing=$approval_file.files
[[ -f $listing && ! -L $listing ]] && single_link "$listing" && fits "$listing" 8388608 &&
    matches_file "$listing" "${fields[11]}" || blocked 'approved file inventory unavailable'
if [[ $host == win32 ]]; then
    # Do not start an aliased launcher or a redirector with adjacent path
    # overrides, alternate DLLs or Python archives. The base image is trusted.
    shopt -s nocasematch
    case "$py/" in */WindowsApps/*) blocked 'Store aliases are unsupported' ;; esac
    shopt -u nocasematch
    unset GLOBIGNORE
    set +f
    shopt -u failglob
    shopt -s nullglob nocaseglob
    shadows=("$root"/*.{_pth,dll,pyd,zip} "$root"/Scripts/*.{_pth,dll,pyd,zip})
    (( ${#shadows[@]} == 0 )) || blocked 'unexpected native bootstrap files'
fi
single_link "$cfg" && fits "$cfg" 65536 || blocked 'invalid environment configuration object'
if [[ -L $py ]]; then
    # Compare actual object identity to the pinned base before opening the link for hashing.
    [[ $host != win32 && ${fields[5]} == /* && $py -ef ${fields[5]} ]] ||
        blocked 'unexpected interpreter link'
else
    single_link "$py" && fits "$py" 134217728 || blocked 'invalid interpreter object'
fi
matches_file "$py" "${fields[8]}" && matches_file "$cfg" "${fields[9]}" ||
    blocked 'interpreter or virtual environment digest mismatch'
cd -- "$root" 2>/dev/null || blocked 'approved working directory unavailable'
child_env=("${clean_env[@]}")
if [[ $host == win32 ]]; then child_env+=("MSYS2_ARG_CONV_EXCL=*"); fi

# Probe is a fixed literal; external record fields are argv data, never code.
# -S prevents site startup until the installation has been checked.
probe='import os
import sys

def require(condition):
    if not condition:
        raise SystemExit(2)

exe, base, base_exe, patch, tag, version, tree_pin, host = sys.argv[1:]
real = os.path.realpath
require(sys.flags.isolated and sys.flags.no_site and sys.flags.dont_write_bytecode)
require(sys.flags.utf8_mode and sys.implementation.name == "cpython")
require(sys.version_info[:2] == (3, 12) and ".".join(map(str, sys.version_info[:3])) == patch)
require(host == sys.platform and os.name == {"darwin": "posix", "linux": "posix", "win32": "nt"}[host])
require(os.path.isabs(exe) and exe == sys.executable)
require(real(sys.base_prefix) == base and real(sys._base_executable) == base_exe)
base_search = list(sys.path)
require(all(os.path.isabs(p) and os.path.commonpath([base, real(p)]) == base
            for p in base_search))

import hashlib
from email.parser import Parser
from importlib import metadata
from importlib.machinery import PathFinder
import json
from pathlib import Path
import re
import site
import stat
import sysconfig
from urllib.parse import unquote, urlsplit

require(sys.maxsize == 2**63 - 1 and sysconfig.get_platform() == tag)
if host == "darwin":
    require(os.uname().machine == "arm64" and re.fullmatch(r"macosx-[0-9.]+-arm64", tag))
elif host == "linux":
    require(os.uname().machine == "x86_64" and tag == "linux-x86_64")
else:
    require(tag == "win-amd64")

root = Path(exe).parent.parent
require(str(root.resolve(strict=True)) == str(root) and root != Path(base))
raw = sys.stdin.buffer.read(8 * 1024**2 + 1)
require(len(raw) <= 8 * 1024**2 and hashlib.sha256(raw).hexdigest() == tree_pin)
require(raw.endswith(b"\n") and 0 < raw.count(b"\n") <= 65536)
records = {}
members = {"": set()}
previous = ""
for row in raw[:-1].decode("utf-8").split("\n"):
    name, marker = row.split("\0")
    parts = name.split("/")
    require(previous < name and len(parts) <= 32 and all(p and p not in (".", "..") for p in parts))
    require(not any(ord(c) < 32 or c in "\\:" for c in name))
    require(marker == "-" or re.fullmatch("[a-f0-9]{64}", marker))
    parent, _, child = name.rpartition("/")
    require(parent in members)
    members[parent].add(child)
    records[name] = marker
    if marker == "-":
        members[name] = set()
    previous = name

size = 0
def verify_directory(directory, relative):
    global size
    # Reject extra names without stat, opening or descending into them.
    expected = members[relative]
    seen = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            require(entry.name in expected)
            seen.add(entry.name)
    require(seen == expected)
    for child in sorted(expected):
        path = directory / child
        rel = path.relative_to(root).as_posix()
        info = path.lstat()
        require(not (getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT))
        if records[rel] == "-":
            require(stat.S_ISDIR(info.st_mode))
            verify_directory(path, rel)
            continue
        if stat.S_ISLNK(info.st_mode):
            target = os.readlink(path)
            digest = hashlib.sha256(b"link\0" + os.fsencode(target))
            require(digest.hexdigest() == records[rel])
            if rel == "lib64":
                require(target == "lib" and stat.S_ISDIR((root / "lib").lstat().st_mode))
            else:
                require(rel in ("bin/python", "bin/python3", "bin/python3.12")
                        and str(path.resolve(strict=True)) == base_exe)
        else:
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= 128 * 1024**2)
            size += info.st_size
            require(size <= 512 * 1024**2)
            with path.open("rb") as stream:
                require(hashlib.file_digest(stream, "sha256").hexdigest() == records[rel])

verify_directory(root, "")

require(not os.path.lexists(Path(exe).parent / "pyvenv.cfg"))
cfg = (root / "pyvenv.cfg").read_text(encoding="utf-8").splitlines()
system_site = [v.strip().lower() for line in cfg for k, sep, v in [line.partition("=")]
               if sep and k.strip().lower() == "include-system-site-packages"]
require(system_site == ["false"])
sites = [Path(p) for p in site.getsitepackages([str(root)]) if Path(p).is_dir()]
pkg_site = root / ("Lib/site-packages" if host == "win32" else "lib/python3.12/site-packages")
require(pkg_site in sites)
for directory in sites:
    for path in directory.iterdir():
        lower = path.name.lower()
        require(not lower.startswith(("__editable__", "sitecustomize.", "usercustomize."))
                and lower not in ("sitecustomize", "usercustomize") and not lower.endswith(".egg-link"))
        if lower.endswith(".pth"):
            # The one reviewed setuptools 80.9.0 shim imports only the pinned local hook.
            require(path == pkg_site / "distutils-precedence.pth" and
                    records.get(path.relative_to(root).as_posix()) ==
                    "2638ce9e2500e572a5e0de7faed6661eb569d1b696fcba07b0dd223da5f5d224")

# Only now may the trusted base startup policy and reviewed, verified site hooks run.
site.main()
require(real(sys.prefix) == str(root) and real(sys.base_prefix) == base)
require(sys.path == list(dict.fromkeys([*base_search, *map(str, sites)])))
package = pkg_site / "sas_re"
spec = PathFinder.find_spec("sas_re", sys.path)
require(spec and spec.origin == str(package / "__init__.py"))
for name in ("__init__.py", "__main__.py", "cli.py", "platform_io.py", "data/baseline.json",
             "contracts/v1/evidence.schema.json", "contracts/v2/evidence.schema.json",
             "contracts/authorization/v1/local-authorization.schema.json"):
    require((package / name).is_file())
dist = pkg_site / ("sas_reverse_engineering-" + version + ".dist-info")
require((dist / "METADATA").is_file())
installed = list(metadata.distributions(name="sas-reverse-engineering", path=sys.path))
require(len(installed) == 1 and installed[0].locate_file("") == pkg_site)
headers = installed[0].metadata
require(headers.get_all("Name") == ["sas-reverse-engineering"] and headers.get_all("Version") == [version])
wheel = Parser().parsestr((dist / "WHEEL").read_text(encoding="utf-8"), headersonly=True)
require(wheel.get_all("Wheel-Version") == ["1.0"] and wheel.get_all("Root-Is-Purelib") == ["true"]
        and wheel.get_all("Tag") == ["py3-none-any"])

def unique(items):
    values = dict(items)
    require(len(values) == len(items))
    return values

origin = dist / "direct_url.json"
if origin.exists():
    record = json.loads(origin.read_text(encoding="utf-8"), object_pairs_hook=unique)
    require(set(record) == {"url", "archive_info"})
    url = urlsplit(record["url"])
    require(url.scheme == "file" and url.netloc in ("", "localhost") and not url.query and not url.fragment)
    require(unquote(url.path).endswith("/sas_reverse_engineering-" + version + "-py3-none-any.whl"))
    archive = record["archive_info"]
    require(set(archive) <= {"hashes", "hash"} and set(archive["hashes"]) == {"sha256"})
    sha = archive["hashes"]["sha256"]
    require(re.fullmatch("[a-f0-9]{64}", sha) and archive.get("hash", "sha256=" + sha) == "sha256=" + sha)'
"${child_env[@]}" "$py" -I -B -S -X utf8 -c "$probe" \
    "${fields[3]}" "${fields[4]}" "${fields[5]}" "${fields[6]}" \
    "${fields[7]}" "${fields[10]}" "${fields[11]}" "$host" >/dev/null 2>&1 < "$listing" ||
    blocked 'installed runtime or package does not match the approved inventory'
exec "${child_env[@]}" "$py" -I -B -X utf8 -m sas_re "$1"
