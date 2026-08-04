#!/usr/bin/env bash
set -euo pipefail

readonly DASHBOARD_HEADING='Release evidence, without the rerun.'
readonly FIXTURE_BOUNDARY='Fixture evidence — not a live AX verification'
readonly FIXTURE_PASS_EXPLANATION='This PASS is a fixture-gate result'

if [[ $# -ne 1 ]]; then
  printf 'Usage: %s <deployed-pages-url>\n' "$0" >&2
  exit 64
fi

page_url="$1"
readonly page_url
if [[ ! "$page_url" =~ ^https?://[^/]+ ]]; then
  printf 'Deployed Pages URL must be an absolute HTTP(S) URL: %s\n' "$page_url" >&2
  exit 64
fi

temporary_directory=''
temporary_directory="$(mktemp -d)"
readonly temporary_directory
page_file="$temporary_directory/page.html"
readonly page_file
trap 'rm -rf "$temporary_directory"' EXIT

page_response="$(curl --fail --silent --show-error --location --retry 3 --retry-delay 5 --retry-all-errors --max-time 30 --output "$page_file" --write-out '%{http_code}\t%{url_effective}' "$page_url")"
page_status="${page_response%%$'\t'*}"
page_effective_url="${page_response#*$'\t'}"
case "$page_status" in
  2??) ;;
  *)
    printf 'Deployed page returned a non-success status: %s\n' "$page_status" >&2
    exit 1
    ;;
esac
page_origin=''
page_origin="$(printf '%s\n' "$page_effective_url" | sed -E 's#^(https?://[^/]+).*$#\1#')"
readonly page_origin
printf 'Verified deployed page response: %s (%s; effective: %s)\n' "$page_status" "$page_url" "$page_effective_url"

require_literal() {
  local literal="$1"

  if ! LC_ALL=C grep -F -- "$literal" "$page_file" >/dev/null; then
    printf 'Expected literal not found: %s\n' "$literal" >&2
    return 1
  fi
  printf 'Verified literal: %s\n' "$literal"
}

require_literal "$DASHBOARD_HEADING"
require_literal "$FIXTURE_BOUNDARY"
require_literal "$FIXTURE_PASS_EXPLANATION"

asset_match="$(LC_ALL=C grep -oE '(href|src)="[^"]*_next/static/[^"]+"' "$page_file" | head -n 1 || true)"
if [[ -z "$asset_match" ]]; then
  printf 'No deployed static asset reference was found in the page.\n' >&2
  exit 1
fi

asset_path="${asset_match#*=\"}"
asset_path="${asset_path%\"}"
case "$asset_path" in
  http://* | https://*) asset_url="$asset_path" ;;
  /*) asset_url="${page_origin}${asset_path}" ;;
  *) asset_url="${page_url%/}/${asset_path}" ;;
esac

asset_status="$(curl --fail --silent --show-error --location --retry 3 --retry-delay 5 --retry-all-errors --max-time 30 --output /dev/null --write-out '%{http_code}' "$asset_url")"
case "$asset_status" in
  2??) ;;
  *)
    printf 'Deployed static asset returned a non-success status: %s (%s)\n' "$asset_status" "$asset_url" >&2
    exit 1
    ;;
esac
printf 'Verified deployed static asset response: %s (%s)\n' "$asset_status" "$asset_url"
