# Python script to eliminate showcase index search/facet clutter and reorganize into a clean, premier explanation documentation page

with open('showcase/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove service-nav tab buttons from header
old_header_nav = """    <nav class="service-nav">
      <button class="service-tab-btn active" id="tabNavDiag" data-view="diagView">
        🩺 <span id="navTextDiag">Diagnostic Lab</span>
      </button>
      <button class="service-tab-btn" id="tabNavPres" data-view="presView">
        🚀 <span id="navTextPres">Setup Guide</span>
      </button>
    </nav>"""

if old_header_nav in html:
    html = html.replace(old_header_nav, "")
    print("HEADER_NAV_REMOVED")
else:
    print("HEADER_NAV_NOT_FOUND")

# 2. Reorganize body: presView is the main primary documentation page!
# Remove diagView entirely (the complex search-panel and index tag grid)
idx_diag_start = html.find('<!-- ================= DIAGNOSTIC HUB VIEW ================= -->')
idx_pres_start = html.find('<!-- ================= PRESENTATION & SETUP GUIDE VIEW ================= -->')

if idx_diag_start != -1 and idx_pres_start != -1:
    html = html[:idx_diag_start] + html[idx_pres_start:]
    print("DIAG_VIEW_AND_INDEX_GRID_REMOVED")
else:
    print("COULD_NOT_LOCATE_DIAG_VIEW")

# Make presView the active visible container
html = html.replace('<div class="view-container" id="presView">', '<div class="view-container active" id="presView" style="display:block;">')

# 3. Add 16 Physical Invariants Section into presView before closing div
invariants_section = """
      <!-- 16 CORE PHYSICAL INVARIANTS CHEAT-SHEET -->
      <section class="benchmark-section" style="margin-top: 40px;">
        <div class="benchmark-heading">
          📐 <span id="invariantsHeading">16 Core Physical Invariants & SWE Laws</span>
        </div>
        <p style="font-size:0.92rem; color:#94a3b8; line-height:1.6;" id="invariantsDesc">
          Mathematical rules injected into AI agents to guarantee zero-defect, hardware-native physical interaction:
        </p>

        <div class="metric-comparison-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
          <div class="comp-card" style="padding: 16px; background:#0f172a; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-weight:700; font-size:13px; color:#60a5fa; margin-bottom:6px;">⏱️ 350ms Temporal Gate</div>
            <p style="font-size:11px; color:#94a3b8; line-height:1.5;">Separates intentional drag/long-press from fast swipes and scrolls. Prevents cards from getting stuck during scrolling.</p>
          </div>

          <div class="comp-card" style="padding: 16px; background:#0f172a; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-weight:700; font-size:13px; color:#60a5fa; margin-bottom:6px;">📏 8.0px Slop Hysteresis</div>
            <p style="font-size:11px; color:#94a3b8; line-height:1.5;">Absorbs finger tremors under 8 pixels. Distinguishes repositions from accidental clicks on floating buttons.</p>
          </div>

          <div class="comp-card" style="padding: 16px; background:#0f172a; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-weight:700; font-size:13px; color:#60a5fa; margin-bottom:6px;">📱 0ms VisualViewport Sync</div>
            <p style="font-size:11px; color:#94a3b8; line-height:1.5;">Bypasses broken 100vh layout boundaries. Dynamically lifts chat inputs above native iOS/Android software keyboards.</p>
          </div>

          <div class="comp-card" style="padding: 16px; background:#0f172a; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-weight:700; font-size:13px; color:#60a5fa; margin-bottom:6px;">🎯 Centroid Invariant (Pinch Zoom)</div>
            <p style="font-size:11px; color:#94a3b8; line-height:1.5;">Locks focal point magnetically under fingers at 0.000px error during multi-touch canvas zooms. Eliminates origin drift.</p>
          </div>

          <div class="comp-card" style="padding: 16px; background:#0f172a; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-weight:700; font-size:13px; color:#60a5fa; margin-bottom:6px;">🔒 W3C setPointerCapture</div>
            <p style="font-size:11px; color:#94a3b8; line-height:1.5;">Pins dragging to the active cursor even when moving beyond viewport boundaries. Never lose scrub or resize tracking.</p>
          </div>

          <div class="comp-card" style="padding: 16px; background:#0f172a; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-weight:700; font-size:13px; color:#60a5fa; margin-bottom:6px;">🛡️ 20px OS Edge Deadzone</div>
            <p style="font-size:11px; color:#94a3b8; line-height:1.5;">Ignores touches within 20px of mobile screen edges to prevent conflicts with native iOS/Android back swipe navigation.</p>
          </div>

          <div class="comp-card" style="padding: 16px; background:#0f172a; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-weight:700; font-size:13px; color:#60a5fa; margin-bottom:6px;">⚡️ touch-action: manipulation</div>
            <p style="font-size:11px; color:#94a3b8; line-height:1.5;">Eliminates legacy 300ms mobile tap delays and disables browser double-tap page zoom for 0ms instantaneous clicks.</p>
          </div>

          <div class="comp-card" style="padding: 16px; background:#0f172a; border:1px solid #1e293b; border-radius:10px;">
            <div style="font-weight:700; font-size:13px; color:#60a5fa; margin-bottom:6px;">📜 0ms Scroll Anchoring</div>
            <p style="font-size:11px; color:#94a3b8; line-height:1.5;">Freezes reading position during dynamic content prepends in infinite scroll feeds. Prevents disorienting layout jumps.</p>
          </div>
        </div>
      </section>
"""

idx_bench_end = html.find('</section>\n    </div>\n  </div>\n\n  <div class="toast" id="toast">')
if idx_bench_end != -1:
    html = html[:idx_bench_end + 10] + invariants_section + html[idx_bench_end + 10:]
    print("INVARIANTS_SECTION_INSERTED")
else:
    # Try alternative matching
    target_needle = '<!-- QUANTITATIVE BENCHMARK SECTION -->'
    idx_target = html.find(target_needle)
    if idx_target != -1:
        idx_close = html.find('</section>', idx_target)
        if idx_close != -1:
            html = html[:idx_close + 10] + invariants_section + html[idx_close + 10:]
            print("INVARIANTS_SECTION_INSERTED_ALT")

# 4. Clean up JS: Remove references to removed index elements (searchInput, tagGrid, etc.)
js_cleanup_block = """
    // Initialize hero live battle arena directly on page load
    initHeroBattle();
    renderLanguage();
"""

# Replace bottom script initialization
idx_bot_init = html.find('renderLanguage();\n    setTimeout(() => {')
if idx_bot_init != -1:
    html = html[:idx_bot_init] + "renderLanguage();\n    initHeroBattle();\n  </script>"
    print("BOTTOM_INIT_CLEANED")

with open('showcase/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("CLEANUP_SAVED")
