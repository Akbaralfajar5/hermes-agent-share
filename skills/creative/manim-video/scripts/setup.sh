#!/usr/bin/env bash
set -euo pipefail
G="\033[0;32m"; R="\033[0;31m"; N="\033[0m"
ok() { echo -e "  ${G}+${N} $1"; }
fail() { echo -e "  ${R}x${N} $1"; }
echo ""; echo "Manim Video Skill — Setup Check"; echo ""
errors=0
# Check OS-level build deps (Ubuntu/Debian)
if command -v dpkg &>/dev/null; then
  dpkg -s libcairo2-dev &>/dev/null 2>&1 && ok "libcairo2-dev" || { fail "libcairo2-dev not installed: sudo apt-get install -y libcairo2-dev"; errors=$((errors+1)); }
  dpkg -s libpango1.0-dev &>/dev/null 2>&1 && ok "libpango1.0-dev" || { fail "libpango1.0-dev not installed: sudo apt-get install -y libpango1.0-dev"; errors=$((errors+1)); }
  dpkg -s pkg-config &>/dev/null 2>&1 && ok "pkg-config" || { fail "pkg-config not installed: sudo apt-get install -y pkg-config"; errors=$((errors+1)); }
fi
command -v python3 &>/dev/null && ok "Python $(python3 --version 2>&1 | awk '{print $2}')" || { fail "Python 3 not found"; errors=$((errors+1)); }
python3 -c "import manim" 2>/dev/null && ok "Manim $(manim --version 2>&1 | head -1)" || { fail "Manim not installed: pip install manim"; errors=$((errors+1)); }
command -v pdflatex &>/dev/null && ok "LaTeX (pdflatex)" || { fail "LaTeX not found (macOS: brew install --cask mactex-no-gui)"; errors=$((errors+1)); }
command -v ffmpeg &>/dev/null && ok "ffmpeg" || { fail "ffmpeg not found"; errors=$((errors+1)); }
echo ""
[ $errors -eq 0 ] && echo -e "${G}All prerequisites satisfied.${N}" || echo -e "${R}$errors prerequisite(s) missing.${N}"
echo ""
