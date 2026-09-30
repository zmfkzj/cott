#!/bin/sh
set -eu

if [ "$#" -ne 0 ]; then
    printf '%s\n' 'usage: COTT_BIN=/absolute/in-tree/path/to/cott tool/setup.sh' >&2
    exit 64
fi

project=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
repository=$(CDPATH= cd -- "$project/../../.." && pwd -P)
deployment="$project/dist/rust_counter-0.1.0"

if [ ! -f "$project/cott.toml" ] || [ -L "$project/cott.toml" ] ||
   [ ! -f "$project/app/Cargo.toml" ] || [ -L "$project/app/Cargo.toml" ]; then
    printf '%s\n' 'setup must run from the checked-in Rust counter example' >&2
    exit 1
fi
if [ -e "$deployment" ] || [ -L "$deployment" ]; then
    printf '%s\n' 'refusing to overwrite dist/rust_counter-0.1.0; remove the prior trusted deployment explicitly before rerunning setup' >&2
    exit 1
fi

case "${COTT_BIN:-}" in
    /*) ;;
    *) printf '%s\n' 'COTT_BIN must name an absolute in-tree compiler executable' >&2; exit 1 ;;
esac
cott=$(realpath -e -- "$COTT_BIN")
case "$cott" in
    "$repository"/*) ;;
    *) printf '%s\n' 'COTT_BIN must resolve inside this Cott repository' >&2; exit 1 ;;
esac
if [ ! -f "$cott" ] || [ ! -x "$cott" ]; then
    printf '%s\n' 'COTT_BIN is not an executable compiler file' >&2
    exit 1
fi

printf '%s\n' 'Emitting the Rust module'
"$cott" emit rust --project "$project"
printf '%s\n' 'Verifying the exact Rust snapshot'
"$cott" verify --project "$project"
printf '%s\n' 'Deploying the portable Cargo library'
"$cott" deploy --project "$project" --output "$deployment"

if [ ! -f "$deployment/Cargo.toml" ] || [ -L "$deployment/Cargo.toml" ]; then
    printf '%s\n' 'Cott deployment did not produce a Cargo library package' >&2
    exit 1
fi
printf 'Run the standard Cargo consumer: cargo run --manifest-path %s/app/Cargo.toml\n' "$project"
