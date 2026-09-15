#!/usr/bin/env python3
"""Generates static showroom HTML pages from showroom/data JSON datasets.

Generates:
  - showroom/assets/showroom.js
  - showroom/index.html (Executive Summary & Postmortem Dossier)
  - showroom/cases.html (Interactive 30-Case Matrix & Detail Drawer)
  - showroom/methodology.html (Methodology, Controls, Limitations & Replication)
"""

import json
import os
import html

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOWROOM_DIR = os.path.join(REPO_ROOT, "showroom")
DATA_DIR = os.path.join(SHOWROOM_DIR, "data")
ASSETS_DIR = os.path.join(SHOWROOM_DIR, "assets")

def load_data():
    with open(os.path.join(DATA_DIR, "summary.json"), "r", encoding="utf-8") as f:
        summary = json.load(f)
    with open(os.path.join(DATA_DIR, "cases.json"), "r", encoding="utf-8") as f:
        cases = json.load(f)
    with open(os.path.join(DATA_DIR, "methodology.json"), "r", encoding="utf-8") as f:
        methodology = json.load(f)
    return summary, cases, methodology

def generate_js():
    js_content = """// Interaction Doctor Showroom Client Scripts
// Handles Case Explorer filtering, detail drawer navigation, and accessible keyboard interaction

(function() {
  'use strict';

  var casesData = [];
  var currentFilterOutcome = 'ALL';
  var currentFilterDifficulty = 'ALL';
  var currentSearchQuery = '';

  document.addEventListener('DOMContentLoaded', init);

  function init() {
    initCaseExplorer();
    initDrawer();
  }

  function initCaseExplorer() {
    var tableBody = document.getElementById('cases-table-body');
    if (!tableBody) return; // Not on cases.html

    var dataUrl = './data/cases.json';
    fetch(dataUrl)
      .then(function(res) {
        if (!res.ok) throw new Error('Failed to load ' + dataUrl);
        return res.json();
      })
      .then(function(data) {
        casesData = data;
        renderCasesTable();
        handleHashChange();
      })
      .catch(function(err) {
        console.error('Data load error:', err);
      });

    var filterBtns = document.querySelectorAll('.filter-btn[data-filter-type]');
    filterBtns.forEach(function(btn) {
      btn.addEventListener('click', function() {
        var type = this.getAttribute('data-filter-type');
        var val = this.getAttribute('data-filter-val');

        document.querySelectorAll('.filter-btn[data-filter-type="' + type + '"]').forEach(function(b) {
          b.classList.remove('active');
        });
        this.classList.add('active');

        if (type === 'outcome') currentFilterOutcome = val;
        if (type === 'difficulty') currentFilterDifficulty = val;

        renderCasesTable();
      });
    });

    var searchInput = document.getElementById('case-search');
    if (searchInput) {
      searchInput.addEventListener('input', function(e) {
        currentSearchQuery = e.target.value.toLowerCase().trim();
        renderCasesTable();
      });
    }

    window.addEventListener('hashchange', handleHashChange);
  }

  function renderCasesTable() {
    var tableBody = document.getElementById('cases-table-body');
    var countDisplay = document.getElementById('filtered-count');
    if (!tableBody) return;

    var filtered = casesData.filter(function(c) {
      if (currentFilterOutcome !== 'ALL' && c.outcome !== currentFilterOutcome) return false;
      if (currentFilterDifficulty !== 'ALL' && c.difficulty !== currentFilterDifficulty) return false;
      if (currentSearchQuery) {
        var matchId = c.case_id.toLowerCase().indexOf(currentSearchQuery) !== -1;
        var matchName = c.name.toLowerCase().indexOf(currentSearchQuery) !== -1;
        var matchSlug = c.slug.toLowerCase().indexOf(currentSearchQuery) !== -1;
        var matchRuntime = (c.runtime || '').toLowerCase().indexOf(currentSearchQuery) !== -1;
        if (!matchId && !matchName && !matchSlug && !matchRuntime) return false;
      }
      return true;
    });

    if (countDisplay) {
      countDisplay.textContent = 'Showing ' + filtered.length + ' of ' + casesData.length + ' cases';
    }

    if (filtered.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 32px; color: var(--ink-muted); font-family: var(--font-mono);">No cases match current filter criteria.</td></tr>';
      return;
    }

    var html = '';
    filtered.forEach(function(c) {
      var bVerdict = formatVerdict(c.runs.baseline.verdict);
      var gVerdict = formatVerdict(c.runs.generic.verdict);
      var dVerdict = formatVerdict(c.runs.doctor.verdict);

      var isSignalCase = c.doctor_intent_stopped;
      var rowStyle = isSignalCase ? 'style="background: #FEF3C7;"' : '';

      html += '<tr ' + rowStyle + ' data-case-id="' + c.case_id + '" class="case-row" style="cursor: pointer;">' +
        '<td style="font-family: var(--font-mono); font-weight: 600;">' + c.case_id + '</td>' +
        '<td>' +
          '<a href="#case-' + c.case_id + '" class="case-name-link" style="font-weight: 600; color: var(--ink-primary); text-decoration: none;">' + c.name + '</a>' +
          (isSignalCase ? ' <span class="archival-badge retained" style="margin-left: 6px; font-size: 9px;">Doctor Stopped</span>' : '') +
        '</td>' +
        '<td><span class="archival-badge" style="background: var(--bg-secondary); border: 1px solid var(--rule-border);">' + c.outcome + '</span></td>' +
        '<td style="font-family: var(--font-mono); font-size: 11px;">' + c.difficulty + '</td>' +
        '<td style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">' + c.runtime + '</td>' +
        '<td>' + bVerdict + '</td>' +
        '<td>' + gVerdict + '</td>' +
        '<td>' + dVerdict + '</td>' +
      '</tr>';
    });

    tableBody.innerHTML = html;

    tableBody.querySelectorAll('.case-row').forEach(function(row) {
      row.addEventListener('click', function(e) {
        if (e.target.tagName !== 'A') {
          var cid = this.getAttribute('data-case-id');
          location.hash = 'case-' + cid;
        }
      });
    });
  }

  function formatVerdict(verdict) {
    if (!verdict) return '<span style="color: var(--ink-faint);">—</span>';
    var cls = 'unnecessary_source_churn';
    var label = verdict.replace(/_/g, ' ');

    if (verdict === 'correct_repair') {
      cls = 'correct_repair';
      label = 'repair pass';
    } else if (verdict === 'correct_no_op') {
      cls = 'correct_no_op';
      label = 'correct no-op';
    } else if (verdict === 'needs_manual_review_ambiguity') {
      cls = 'needs_manual_review_ambiguity';
      label = 'stopped (review)';
    } else if (verdict === 'intent_guessing_violation') {
      cls = 'intent_guessing_violation';
      label = 'intent guess';
    } else if (verdict === 'defect_not_fixed') {
      cls = 'intent_guessing_violation';
      label = 'not fixed';
    }

    return '<span class="grid-cell-verdict ' + cls + '">' + label + '</span>';
  }

  function handleHashChange() {
    var hash = window.location.hash;
    if (hash && hash.indexOf('#case-') === 0) {
      var cid = hash.replace('#case-', '');
      var caseItem = casesData.find(function(c) {
        return c.case_id === cid || c.slug === cid;
      });
      if (caseItem) {
        openDrawer(caseItem);
      }
    } else {
      closeDrawer();
    }
  }

  function initDrawer() {
    var overlay = document.getElementById('case-drawer-overlay');
    var closeBtn = document.getElementById('case-drawer-close');
    if (!overlay) return;

    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) {
        history.pushState('', document.title, window.location.pathname + window.location.search);
        closeDrawer();
      }
    });

    if (closeBtn) {
      closeBtn.addEventListener('click', function() {
        history.pushState('', document.title, window.location.pathname + window.location.search);
        closeDrawer();
      });
    }

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        var overlay = document.getElementById('case-drawer-overlay');
        if (overlay && overlay.classList.contains('open')) {
          history.pushState('', document.title, window.location.pathname + window.location.search);
          closeDrawer();
        }
      }
    });
  }

  function openDrawer(c) {
    var overlay = document.getElementById('case-drawer-overlay');
    var content = document.getElementById('case-drawer-content');
    if (!overlay || !content) return;

    var relationsStr = (c.relations && c.relations.length) ? c.relations.join(', ') : 'None';
    var envStr = (c.environmental_claims && c.environmental_claims.length) ? c.environmental_claims.join(', ') : 'Standard DOM/pointer';
    var oraclesHtml = (c.primary_hidden_oracles && c.primary_hidden_oracles.length)
      ? c.primary_hidden_oracles.map(function(o) { return '<li>' + escapeHtml(o) + '</li>'; }).join('')
      : '<li>Standard pass assertions</li>';

    content.innerHTML = '<div style="margin-bottom: 20px;">' +
      '<div style="font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 4px;">' +
        'Case ' + c.case_id + ' &bull; ' + c.outcome + ' Outcome &bull; Difficulty ' + c.difficulty +
      '</div>' +
      '<h2 style="font-family: var(--font-sans); font-size: 24px; font-weight: 700; color: var(--ink-primary); margin-bottom: 8px;">' +
        escapeHtml(c.name) +
      '</h2>' +
      '<div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">' +
        'Slug: ' + c.slug + ' &bull; Runtime: ' + c.runtime +
      '</div>' +
    '</div>' +

    (c.doctor_intent_stopped ?
      '<div class="verdict-callout" style="border-left-color: var(--arm-retained); margin: 0 0 20px 0;">' +
        '<div class="verdict-callout-title" style="color: var(--arm-retained);">Doctor Ambiguity Signal Detected</div>' +
        '<div class="verdict-callout-text" style="font-size: 14px;">' +
          'On this case, Interaction Doctor v1 successfully halted execution with a manual review disposition rather than guessing an unresolved product policy. Both Baseline and Generic guessed and modified code unilaterally.' +
        '</div>' +
      '</div>' : '') +

    '<div style="background: var(--bg-secondary); border: 1px solid var(--rule-border); padding: 16px; margin-bottom: 24px;">' +
      '<div style="font-family: var(--font-mono); font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 12px; color: var(--ink-secondary);">' +
        'Experimental Arm Verdicts & Telemetry' +
      '</div>' +
      '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">' +
        '<thead>' +
          '<tr style="border-bottom: 1px solid var(--rule-border); text-align: left; font-family: var(--font-mono); font-size: 10px; color: var(--ink-muted);">' +
            '<th style="padding: 6px;">Arm</th>' +
            '<th style="padding: 6px;">Verdict</th>' +
            '<th style="padding: 6px; text-align: right;">Cost</th>' +
            '<th style="padding: 6px; text-align: right;">Time</th>' +
            '<th style="padding: 6px; text-align: right;">Tools</th>' +
          '</tr>' +
        '</thead>' +
        '<tbody>' +
          '<tr style="border-bottom: 1px solid var(--rule-fine);">' +
            '<td style="padding: 6px; font-weight: 600;"><span class="arm-dot baseline"></span> Baseline</td>' +
            '<td style="padding: 6px;">' + formatVerdict(c.runs.baseline.verdict) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">$' + c.runs.baseline.cost.toFixed(4) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.baseline.seconds.toFixed(1) + 's</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.baseline.tools + '</td>' +
          '</tr>' +
          '<tr style="border-bottom: 1px solid var(--rule-fine);">' +
            '<td style="padding: 6px; font-weight: 600;"><span class="arm-dot generic"></span> Generic</td>' +
            '<td style="padding: 6px;">' + formatVerdict(c.runs.generic.verdict) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">$' + c.runs.generic.cost.toFixed(4) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.generic.seconds.toFixed(1) + 's</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.generic.tools + '</td>' +
          '</tr>' +
          '<tr>' +
            '<td style="padding: 6px; font-weight: 600;"><span class="arm-dot doctor"></span> Doctor</td>' +
            '<td style="padding: 6px;">' + formatVerdict(c.runs.doctor.verdict) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">$' + c.runs.doctor.cost.toFixed(4) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.doctor.seconds.toFixed(1) + 's</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.doctor.tools + '</td>' +
          '</tr>' +
        '</tbody>' +
      '</table>' +
    '</div>' +

    '<div style="margin-bottom: 24px;">' +
      '<h4 style="font-family: var(--font-mono); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-secondary); margin-bottom: 8px;">' +
        'Agent Task Prompt' +
      '</h4>' +
      '<div style="background: var(--bg-surface); border: 1px solid var(--rule-border); padding: 16px; font-family: var(--font-mono); font-size: 12px; line-height: 1.6; white-space: pre-wrap;">' + escapeHtml(c.task_description) + '</div>' +
    '</div>' +

    '<div style="margin-bottom: 24px;">' +
      '<h4 style="font-family: var(--font-mono); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-secondary); margin-bottom: 8px;">' +
        'Primary Hidden Oracles & Invariants' +
      '</h4>' +
      '<ul style="padding-left: 20px; font-size: 13px; line-height: 1.5; color: var(--ink-secondary);">' +
        oraclesHtml +
      '</ul>' +
    '</div>' +

    '<div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted); border-top: 1px solid var(--rule-fine); padding-top: 12px;">' +
      '<div>Relations: ' + relationsStr + '</div>' +
      '<div>Environment Claims: ' + envStr + '</div>' +
      '<div>Contamination Risk: ' + c.contamination_risk + ' &bull; Revalidation Required: ' + c.requires_recursive_revalidation + '</div>' +
    '</div>';

    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }

  function closeDrawer() {
    var overlay = document.getElementById('case-drawer-overlay');
    if (!overlay) return;
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

})();
"""
    with open(os.path.join(ASSETS_DIR, "showroom.js"), "w", encoding="utf-8") as f:
        f.write(js_content)
    print("Wrote showroom/assets/showroom.js")

def render_masthead(active_page="index"):
    return f"""
    <header class="masthead">
      <div class="masthead-meta">
        <div>DOSSIER: EXP-ID-2026-V1 &bull; REPO: saramjh/interaction-doctor</div>
        <div class="masthead-badge-group">
          <span class="archival-badge discontinued">Skill: Discontinued</span>
          <span class="archival-badge retained">Benchmark: Retained</span>
          <span>N = 30 &times; 3 = 90 Runs</span>
        </div>
      </div>
      <div class="masthead-nav-bar">
        <div class="masthead-title">
          <a href="./index.html">Interaction Doctor Benchmark</a>
        </div>
        <nav>
          <ul class="nav-links">
            <li><a href="./index.html" class="{'active' if active_page == 'index' else ''}">Executive Report</a></li>
            <li><a href="./cases.html" class="{'active' if active_page == 'cases' else ''}">Case Matrix (30)</a></li>
            <li><a href="./methodology.html" class="{'active' if active_page == 'methodology' else ''}">Methodology &amp; Replication</a></li>
            <li><a href="https://github.com/saramjh/interaction-doctor" target="_blank" rel="noopener">GitHub Archive &rarr;</a></li>
          </ul>
        </nav>
      </div>
    </header>
    """

def render_footer():
    return """
    <footer class="site-footer">
      <div>
        <span>Interaction Doctor Benchmark &bull; Frozen Research Asset (2026)</span>
        <span style="margin: 0 8px;">&bull;</span>
        <span>Independent Variable: Frozen Interaction Doctor v1 Skill</span>
      </div>
      <div>
        <a href="https://github.com/saramjh/interaction-doctor" class="footer-repo-link">Repository Source</a>
        <span style="margin: 0 8px;">&bull;</span>
        <a href="./methodology.html">Replication Protocol</a>
      </div>
    </footer>
    """

def format_verdict_html(verdict):
    if not verdict:
        return '<span style="color: var(--ink-faint);">—</span>'
    cls = "unnecessary_source_churn"
    label = verdict.replace("_", " ")
    if verdict == "correct_repair":
        cls = "correct_repair"
        label = "repair pass"
    elif verdict == "correct_no_op":
        cls = "correct_no_op"
        label = "correct no-op"
    elif verdict == "needs_manual_review_ambiguity":
        cls = "needs_manual_review_ambiguity"
        label = "stopped (review)"
    elif verdict in ("intent_guessing_violation", "defect_not_fixed"):
        cls = "intent_guessing_violation"
        label = "intent guess" if verdict == "intent_guessing_violation" else "not fixed"
    return f'<span class="grid-cell-verdict {cls}">{label}</span>'

def build_index_page(summary, cases):
    b = summary["arms"]["baseline"]
    g = summary["arms"]["generic"]
    d = summary["arms"]["doctor"]
    r = summary["ratios_vs_baseline"]

    # Generate NEEDS_INTENT rows
    needs_intent_cases = [c for c in cases if c["outcome"] == "NEEDS_INTENT"]
    ni_table_rows = ""
    for c in needs_intent_cases:
        bv = format_verdict_html(c["runs"]["baseline"]["verdict"])
        gv = format_verdict_html(c["runs"]["generic"]["verdict"])
        dv = format_verdict_html(c["runs"]["doctor"]["verdict"])
        stopped = c["doctor_intent_stopped"]
        highlight = 'style="background: #FEF3C7;"' if stopped else ''
        ni_table_rows += f"""
        <tr {highlight}>
          <td style="font-family: var(--font-mono); font-weight: 600;">{c['case_id']}</td>
          <td>
            <a href="./cases.html#case-{c['case_id']}" style="font-weight: 600; color: var(--ink-primary); text-decoration: none;">{c['name']}</a>
            {'<span class="archival-badge retained" style="margin-left:6px; font-size:9px;">Doctor Stopped</span>' if stopped else ''}
          </td>
          <td>{bv}</td>
          <td>{gv}</td>
          <td>{dv}</td>
          <td style="font-size: 12px; color: var(--ink-secondary);">{
            'Refused to guess unresolved policy; requested manual clarification' if stopped else 'Unilaterally selected a resolution policy without asking user'
          }</td>
        </tr>
        """

    # Generate 30-case matrix SVG or HTML grid
    matrix_rows = ""
    for c in cases:
        b_dot = format_verdict_html(c["runs"]["baseline"]["verdict"])
        g_dot = format_verdict_html(c["runs"]["generic"]["verdict"])
        d_dot = format_verdict_html(c["runs"]["doctor"]["verdict"])
        stopped = c["doctor_intent_stopped"]
        row_style = 'style="background: #FEF3C7;"' if stopped else ''
        matrix_rows += f"""
        <tr {row_style}>
          <td style="font-family: var(--font-mono); font-weight: 600; padding: 6px 10px;">{c['case_id']}</td>
          <td style="padding: 6px 10px;">
            <a href="./cases.html#case-{c['case_id']}" style="color: var(--ink-primary); font-weight: 500; text-decoration: none;">{c['name']}</a>
            {'<span class="archival-badge retained" style="margin-left:4px; font-size:8px;">STOPPED</span>' if stopped else ''}
          </td>
          <td style="padding: 6px 10px;"><span class="archival-badge" style="background:var(--bg-secondary); border:1px solid var(--rule-border); font-size:9px;">{c['outcome']}</span></td>
          <td style="padding: 6px 10px;">{b_dot}</td>
          <td style="padding: 6px 10px;">{g_dot}</td>
          <td style="padding: 6px 10px;">{d_dot}</td>
        </tr>
        """

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Interaction Doctor Benchmark &bull; Empirical Postmortem</title>
  <link rel="stylesheet" href="./assets/showroom.css">
</head>
<body>
  <div class="site-wrapper">
    {render_masthead("index")}

    <!-- Hero Dossier -->
    <section class="hero-dossier">
      <div class="hero-grid">
        <div>
          <div class="section-label">Empirical Evaluation Dossier</div>
          <h1 class="hero-headline">A coding-agent skill experiment that failed to justify its cost.</h1>
          <p class="hero-subtitle">
            A 30-case, 90-run controlled benchmark measuring interaction-defect diagnosis, repair, and ambiguity handling on frontier models.
          </p>
          <div class="lead-statement">
            The specialized Interaction Doctor skill provided zero measured repair advantage over the baseline model, nearly doubled token expenditure (~1.91&times;), and more than doubled latency (~2.44&times;). The skill has been <strong>discontinued</strong>. The benchmark is preserved as an independent research asset.
          </div>
        </div>

        <div>
          <div class="hero-parameters">
            <div style="font-weight: 700; border-bottom: 1px solid var(--rule-border); padding-bottom: 6px; margin-bottom: 8px; text-transform: uppercase; font-size: 11px;">
              Experiment Parameters
            </div>
            <dl>
              <dt>Evaluated Model</dt><dd>claude-sonnet-5</dd><br>
              <dt>Effort Setting</dt><dd>medium</dd><br>
              <dt>Benchmark Corpus</dt><dd>30 cases (19 Defect, 5 Control, 6 Ambiguous)</dd><br>
              <dt>Experimental Arms</dt><dd>3 (Baseline, Generic Rigor, Doctor v1)</dd><br>
              <dt>Valid Observations</dt><dd>90 runs (1 per case &times; arm)</dd><br>
              <dt>Execution Sandbox</dt><dd>macOS Seatbelt (Fail-closed native)</dd><br>
              <dt>Frozen Commit</dt><dd><code>dfb9f79</code></dd><br>
              <dt>Product Outcome</dt><dd style="color: var(--arm-doctor);">DISCONTINUED</dd>
            </dl>
          </div>
        </div>
      </div>
    </section>

    <!-- Executive Result Cards -->
    <section class="section-block">
      <div class="section-label">Primary Findings</div>
      <h2 class="section-title">Executive Summary</h2>

      <div class="findings-grid">
        <div class="finding-card">
          <div class="finding-num parity">19 / 19</div>
          <div class="finding-label">Repair Success in Every Arm</div>
          <div class="finding-desc">
            Baseline, Generic, and Doctor each achieved 100% repair success on all 19 defective cases. The specialized skill provided <strong>zero incremental repair capability</strong>.
          </div>
        </div>

        <div class="finding-card">
          <div class="finding-num cost">~1.91&times;</div>
          <div class="finding-label">Doctor Execution Cost Ratio</div>
          <div class="finding-desc">
            Total cost of $6.20 ($0.207/run) vs Baseline's $3.24 ($0.108/run). Tool calls increased by 1.54&times; and wall-clock execution latency increased by 2.44&times;.
          </div>
        </div>

        <div class="finding-card">
          <div class="finding-num signal">2 / 6</div>
          <div class="finding-label">Ambiguous Cases Stopped by Doctor</div>
          <div class="finding-desc">
            Doctor halted for manual review on 2 of 6 ambiguous cases (case-011 and case-016). Baseline and Generic unilaterally guessed product policy on all 6 cases (0/6).
          </div>
        </div>
      </div>

      <div class="verdict-callout">
        <div class="verdict-callout-title">Final Empirical Verdict</div>
        <div class="verdict-callout-text">
          "The specialized skill did not improve repair capability on this benchmark and imposed substantial execution cost. It showed a limited signal in preventing unsupported product-intent decisions on two specific cases, but this was insufficient to support product viability."
        </div>
      </div>
    </section>

    <!-- Three-Arm Controlled Comparison Table -->
    <section class="section-block">
      <div class="section-label">Empirical Measurements</div>
      <h2 class="section-title">Three-Arm Controlled Comparison</h2>
      <p class="prose">
        All 90 runs were evaluated with the same frontier model (<code>claude-sonnet-5</code>) at medium effort. The only independent variable was the intervention injected into the agent environment.
      </p>

      <div class="archival-table-wrap">
        <table class="archival-table">
          <thead>
            <tr>
              <th>Evaluation Metric</th>
              <th class="num"><span class="arm-dot baseline"></span> Arm A: Baseline</th>
              <th class="num"><span class="arm-dot generic"></span> Arm B: Generic Rigor</th>
              <th class="num"><span class="arm-dot doctor"></span> Arm C: Interaction Doctor</th>
              <th>Experimental Delta &amp; Interpretation</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Repair Success (Specified Defects)</strong></td>
              <td class="num"><strong>19 / 19</strong> (100%)</td>
              <td class="num"><strong>19 / 19</strong> (100%)</td>
              <td class="num"><strong>19 / 19</strong> (100%)</td>
              <td>0% lift. Pure parity on well-specified defects.</td>
            </tr>
            <tr>
              <td><strong>Correct NO-Op (Benign Controls)</strong></td>
              <td class="num">3 / 5 (60.0%)</td>
              <td class="num">2 / 5 (40.0%)</td>
              <td class="num">2 / 5 (40.0%)</td>
              <td>Baseline was slightly less prone to unnecessary churn.</td>
            </tr>
            <tr>
              <td><strong>Functional False Positives</strong></td>
              <td class="num">0 / 5 (0.0%)</td>
              <td class="num">0 / 5 (0.0%)</td>
              <td class="num">0 / 5 (0.0%)</td>
              <td>No arm broke the underlying logic of benign controls.</td>
            </tr>
            <tr>
              <td><strong>Intent Guessing Rate (NEEDS_INTENT)</strong></td>
              <td class="num">6 / 6 (100%)</td>
              <td class="num">6 / 6 (100%)</td>
              <td class="num">4 / 6 (66.7%)</td>
              <td>Doctor reduced guessing by 33.3% (stopped on 011, 016).</td>
            </tr>
            <tr>
              <td><strong>Manual Review Ambiguity Halts</strong></td>
              <td class="num">0 / 6 (0.0%)</td>
              <td class="num">0 / 6 (0.0%)</td>
              <td class="num">2 / 6 (33.3%)</td>
              <td>Sole positive signal: Doctor stopped on 2 underspecified cases.</td>
            </tr>
            <tr>
              <td><strong>Measured Regressions</strong></td>
              <td class="num">1 / 30 (3.3%)</td>
              <td class="num">1 / 30 (3.3%)</td>
              <td class="num">0 / 30 (0.0%)</td>
              <td><em>Non-independent:</em> The only regression occurred on 011, which Doctor avoided solely by pausing.</td>
            </tr>
            <tr>
              <td><strong>False Closure Claims</strong></td>
              <td class="num">0 / 30 (0.0%)</td>
              <td class="num">1 / 30 (3.3%)</td>
              <td class="num">0 / 30 (0.0%)</td>
              <td>Generic arm claimed completion on case-011 while failing.</td>
            </tr>
            <tr>
              <td><strong>Detection Heuristic (Keyword Match)</strong></td>
              <td class="num">14 / 19 (73.7%)</td>
              <td class="num">18 / 19 (94.7%)</td>
              <td class="num">18 / 19 (94.7%)</td>
              <td>Diagnostic keyword presence only; NOT semantic recall.</td>
            </tr>
            <tr style="background: var(--bg-secondary); font-weight: 600;">
              <td><strong>Total Cost (30 Runs)</strong></td>
              <td class="num">${b['total_cost']:.4f}</td>
              <td class="num">${g['total_cost']:.4f}</td>
              <td class="num" style="color: var(--arm-doctor);">${d['total_cost']:.4f}</td>
              <td><strong>1.91&times;</strong> cost increase for Doctor intervention.</td>
            </tr>
            <tr>
              <td>Mean Cost per Case Run</td>
              <td class="num">${b['mean_cost']:.4f}</td>
              <td class="num">${g['mean_cost']:.4f}</td>
              <td class="num" style="color: var(--arm-doctor);">${d['mean_cost']:.4f}</td>
              <td>+$0.0986 extra per case.</td>
            </tr>
            <tr style="background: var(--bg-secondary); font-weight: 600;">
              <td><strong>Total Wall Clock Time</strong></td>
              <td class="num">{b['total_seconds']:.1f}s</td>
              <td class="num">{g['total_seconds']:.1f}s</td>
              <td class="num" style="color: var(--arm-doctor);">{d['total_seconds']:.1f}s</td>
              <td><strong>2.44&times;</strong> execution latency multiplier.</td>
            </tr>
            <tr>
              <td>Mean Wall Time per Run</td>
              <td class="num">{b['mean_seconds']:.1f}s</td>
              <td class="num">{g['mean_seconds']:.1f}s</td>
              <td class="num" style="color: var(--arm-doctor);">{d['mean_seconds']:.1f}s</td>
              <td>+40.6s added delay per run.</td>
            </tr>
            <tr style="background: var(--bg-secondary); font-weight: 600;">
              <td><strong>Total Tool Calls</strong></td>
              <td class="num">{b['total_tools']}</td>
              <td class="num">{g['total_tools']}</td>
              <td class="num" style="color: var(--arm-doctor);">{d['total_tools']}</td>
              <td><strong>1.54&times;</strong> tool invocation overhead.</td>
            </tr>
            <tr>
              <td>Mean Tool Invocations per Run</td>
              <td class="num">{b['mean_tools']:.1f}</td>
              <td class="num">{g['mean_tools']:.1f}</td>
              <td class="num" style="color: var(--arm-doctor);">{d['mean_tools']:.1f}</td>
              <td>+2.5 roundtrips per case.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Data Visualizations -->
    <section class="section-block">
      <div class="section-label">Comparative Data Graphics</div>
      <h2 class="section-title">Cost, Latency &amp; Repair Visualizations</h2>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
        <!-- Repair Parity Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title">Figure 1: Repair Success on Specified Defects (n=19)</div>
            <div class="chart-subtitle">Denom: 19 YES cases</div>
          </div>
          <svg viewBox="0 0 500 160" class="svg-chart" role="img" aria-label="Repair success chart showing 19/19 parity in all arms">
            <!-- Baseline -->
            <text x="10" y="32" font-family="IBM Plex Mono" font-size="12" fill="#161616">Baseline</text>
            <rect x="120" y="18" width="300" height="20" fill="#252525" rx="1" />
            <text x="430" y="33" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">19/19 (100%)</text>

            <!-- Generic -->
            <text x="10" y="77" font-family="IBM Plex Mono" font-size="12" fill="#161616">Generic</text>
            <rect x="120" y="63" width="300" height="20" fill="#6B7075" rx="1" />
            <text x="430" y="78" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">19/19 (100%)</text>

            <!-- Doctor -->
            <text x="10" y="122" font-family="IBM Plex Mono" font-size="12" fill="#A33A2B">Doctor v1</text>
            <rect x="120" y="108" width="300" height="20" fill="#A33A2B" rx="1" />
            <text x="430" y="123" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#A33A2B">19/19 (100%)</text>
          </svg>
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted); margin-top: 8px;">
            Identical bar lengths depict exact parity. No repair delta was observed.
          </div>
        </div>

        <!-- Cost Overhead Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title">Figure 2: Total API Cost across 30 Runs ($ USD)</div>
            <div class="chart-subtitle">Denom: 30 runs per arm</div>
          </div>
          <svg viewBox="0 0 500 160" class="svg-chart" role="img" aria-label="Cost comparison chart showing Doctor at nearly 2x baseline cost">
            <!-- Baseline -->
            <text x="10" y="32" font-family="IBM Plex Mono" font-size="12" fill="#161616">Baseline</text>
            <rect x="120" y="18" width="156" height="20" fill="#252525" rx="1" />
            <text x="286" y="33" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">$3.24 (1.00&times;)</text>

            <!-- Generic -->
            <text x="10" y="77" font-family="IBM Plex Mono" font-size="12" fill="#161616">Generic</text>
            <rect x="120" y="63" width="166" height="20" fill="#6B7075" rx="1" />
            <text x="296" y="78" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">$3.44 (1.06&times;)</text>

            <!-- Doctor -->
            <text x="10" y="122" font-family="IBM Plex Mono" font-size="12" fill="#A33A2B">Doctor v1</text>
            <rect x="120" y="108" width="300" height="20" fill="#A33A2B" rx="1" />
            <text x="430" y="123" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#A33A2B">$6.20 (1.91&times;)</text>
          </svg>
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted); margin-top: 8px;">
            Doctor imposed an 81% cost penalty over generic audit and 91% over baseline.
          </div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
        <!-- Wall Time Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title">Figure 3: Mean Wall-Clock Latency per Run (Seconds)</div>
            <div class="chart-subtitle">Lower is faster</div>
          </div>
          <svg viewBox="0 0 500 160" class="svg-chart" role="img" aria-label="Wall time comparison chart">
            <text x="10" y="32" font-family="IBM Plex Mono" font-size="12" fill="#161616">Baseline</text>
            <rect x="120" y="18" width="123" height="20" fill="#252525" rx="1" />
            <text x="253" y="33" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">28.3s (1.00&times;)</text>

            <text x="10" y="77" font-family="IBM Plex Mono" font-size="12" fill="#161616">Generic</text>
            <rect x="120" y="63" width="144" height="20" fill="#6B7075" rx="1" />
            <text x="274" y="78" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">33.1s (1.17&times;)</text>

            <text x="10" y="122" font-family="IBM Plex Mono" font-size="12" fill="#A33A2B">Doctor v1</text>
            <rect x="120" y="108" width="300" height="20" fill="#A33A2B" rx="1" />
            <text x="430" y="123" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#A33A2B">68.9s (2.44&times;)</text>
          </svg>
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted); margin-top: 8px;">
            Doctor required 2.44&times; longer to complete execution due to auditing overhead.
          </div>
        </div>

        <!-- Intent Guessing Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title">Figure 4: Intent Guessing Rate on Ambiguous Tasks (n=6)</div>
            <div class="chart-subtitle">Lower guessing is better</div>
          </div>
          <svg viewBox="0 0 500 160" class="svg-chart" role="img" aria-label="Intent guessing comparison chart">
            <text x="10" y="32" font-family="IBM Plex Mono" font-size="12" fill="#161616">Baseline</text>
            <rect x="120" y="18" width="300" height="20" fill="#A33A2B" rx="1" />
            <text x="430" y="33" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#A33A2B">6/6 (100%)</text>

            <text x="10" y="77" font-family="IBM Plex Mono" font-size="12" fill="#161616">Generic</text>
            <rect x="120" y="63" width="300" height="20" fill="#A33A2B" rx="1" />
            <text x="430" y="78" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#A33A2B">6/6 (100%)</text>

            <text x="10" y="122" font-family="IBM Plex Mono" font-size="12" fill="#2F5B4D">Doctor v1</text>
            <rect x="120" y="108" width="200" height="20" fill="#2F5B4D" rx="1" />
            <text x="330" y="123" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#2F5B4D">4/6 (66.7%)</text>
          </svg>
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted); margin-top: 8px;">
            Doctor uniquely stopped on 2 cases (011, 016), while baseline/generic guessed on all 6.
          </div>
        </div>
      </div>
    </section>

    <!-- NEEDS_INTENT Detail -->
    <section class="section-block">
      <div class="section-label">Ambiguity Analysis</div>
      <h2 class="section-title">NEEDS_INTENT Case Breakdown</h2>
      <p class="prose">
        Six benchmark cases contain fundamentally underspecified interaction policy choices where multiple plausible product decisions exist. Agents were scored on whether they recognized the ambiguity and stopped to ask rather than unilaterally implementing an ungrounded preference.
      </p>

      <div class="archival-table-wrap">
        <table class="archival-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Case Title</th>
              <th>Baseline</th>
              <th>Generic</th>
              <th>Doctor</th>
              <th>Observed Behavioral Outcome under Doctor</th>
            </tr>
          </thead>
          <tbody>
            {ni_table_rows}
          </tbody>
        </table>
      </div>

      <div class="prose">
        <h3>Why Did Doctor Only Stop on 011 and 016?</h3>
        <p>
          In <code>case-011-shared-canvas-bifurcation</code> and <code>case-016-swipe-left-double-bound</code>, the conflict directly manifested as two conflicting event handlers attached to the same DOM target. Doctor's ownership graph extraction explicitly flagged the collision and triggered the protocol's <code>NEEDS_INTENT</code> disposition.
        </p>
        <p>
          Conversely, on <code>case-004</code>, <code>case-010</code>, <code>case-013</code>, and <code>case-019</code>, the ambiguity stemmed from lifecycle scoping or environmental defaults rather than direct simultaneous event bindings. Despite possessing the skill prompt, the model rationalized a "standard" resolution and edited the files anyway.
        </p>
      </div>
    </section>

    <!-- 30-Case Observation Matrix -->
    <section class="section-block">
      <div class="section-label">Full Corpus Overview</div>
      <h2 class="section-title">30-Case &times; 3-Arm Observation Matrix (90 Runs)</h2>
      <p class="prose">
        Every row represents one benchmark fixture. Click any row or case name to inspect the full prompt, hidden oracles, and execution telemetry in the Case Explorer.
      </p>

      <div class="archival-table-wrap">
        <table class="archival-table observation-grid-table">
          <thead>
            <tr>
              <th style="width: 50px;">ID</th>
              <th>Case Name</th>
              <th style="width: 90px;">Outcome</th>
              <th>Arm A: Baseline</th>
              <th>Arm B: Generic</th>
              <th>Arm C: Doctor</th>
            </tr>
          </thead>
          <tbody>
            {matrix_rows}
          </tbody>
        </table>
      </div>
      <div style="text-align: right; margin-top: 12px;">
        <a href="./cases.html" style="font-family: var(--font-mono); font-size: 13px; font-weight: 600;">Open Filterable Case Explorer &rarr;</a>
      </div>
    </section>

    <!-- Attempts to Save the Product -->
    <section class="section-block">
      <div class="section-label">Engineering Postmortem</div>
      <h2 class="section-title">Why Productization Failed: Three Architectural Dead Ends</h2>
      <p class="prose">
        When early smoke tests revealed that always running Interaction Doctor doubled costs with zero repair benefit, engineering explored three separate mitigation architectures to selectively invoke the skill. All three failed.
      </p>

      <div style="display: flex; flex-direction: column; gap: 24px; margin-top: 24px;">
        <div style="background: var(--bg-surface); border: 1px solid var(--rule-border); padding: 24px;">
          <h3 style="font-family: var(--font-sans); font-size: 17px; font-weight: 700; margin-bottom: 8px; color: var(--ink-primary);">
            1. The Universal Semantic Eval Gate Problem
          </h3>
          <p class="prose" style="font-size: 14px; margin-bottom: 8px;">
            <strong>Hypothesis:</strong> Place a fast, cheap upstream classifier prompt in front of the model to decide whether an incoming task contains an interaction-ownership problem before loading the heavy skill.
          </p>
          <p class="prose" style="font-size: 14px; margin-bottom: 0;">
            <strong>Why it failed:</strong> Cascading classifiers have asymmetrical risk. If the gate has even a 10% false negative rate, it permanently locks out the downstream specialist from ever seeing the task. Tuning the gate for zero false negatives forced its recall so wide that it triggered on virtually every UI edit, returning total costs right back to 1.9&times;.
          </p>
        </div>

        <div style="background: var(--bg-surface); border: 1px solid var(--rule-border); padding: 24px;">
          <h3 style="font-family: var(--font-sans); font-size: 17px; font-weight: 700; margin-bottom: 8px; color: var(--ink-primary);">
            2. The Self-Routing Failure
          </h3>
          <p class="prose" style="font-size: 14px; margin-bottom: 8px;">
            <strong>Hypothesis:</strong> Give the baseline agent a concise tool or skill description and let the model self-route when it gets stuck or detects ambiguity.
          </p>
          <p class="prose" style="font-size: 14px; margin-bottom: 0;">
            <strong>Why it failed:</strong> Frontier models suffer from severe meta-cognitive blindspots when dealing with interaction bugs. The baseline model confidently believes its first broken patch is correct, so it never experiences the doubt required to trigger an external consultation. Self-routing yielded an invocation rate near zero on the very cases that needed it.
          </p>
        </div>

        <div style="background: var(--bg-surface); border: 1px solid var(--rule-border); padding: 24px;">
          <h3 style="font-family: var(--font-sans); font-size: 17px; font-weight: 700; margin-bottom: 8px; color: var(--ink-primary);">
            3. The Native Static Detector Experiment
          </h3>
          <p class="prose" style="font-size: 14px; margin-bottom: 8px;">
            <strong>Hypothesis:</strong> Use lexical AST parsing and static regex triggers in the IDE/CLI to flag nested pointer events and inject the skill deterministically without LLM gating overhead.
          </p>
          <p class="prose" style="font-size: 14px; margin-bottom: 0;">
            <strong>Why it failed:</strong> Static detectors proved completely brittle across custom frameworks and abstractions. They triggered endlessly on standard benign patterns (e.g. nested buttons with proper delegation) while completely missing cross-component lifecycle leaks (e.g. uncancelled RAF loops, background tab listeners, or React Native gesture responders wrapped in hooks).
          </p>
        </div>
      </div>
    </section>

    <!-- Final Decision Record -->
    <section class="section-block">
      <div class="section-label">Disposition Record</div>
      <h2 class="section-title">Final Product Disposition</h2>

      <div style="background: var(--bg-secondary); border: 2px solid var(--ink-primary); padding: 32px; margin-top: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; border-bottom: 1px solid var(--rule-border); padding-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <div style="font-family: var(--font-mono); font-size: 13px; font-weight: 700; text-transform: uppercase;">
            ARCHIVAL DISPOSITION DECISION &bull; EXP-202609-ID
          </div>
          <div style="font-family: var(--font-mono); font-size: 12px; color: var(--ink-muted);">
            EFFECTIVE DATE: SEPTEMBER 2026
          </div>
        </div>

        <div style="font-family: var(--font-mono); font-size: 13px; line-height: 1.8; margin-bottom: 20px;">
          <div><strong style="display:inline-block; width: 220px;">INTERACTION DOCTOR SKILL:</strong> <span class="archival-badge discontinued">DISCONTINUED</span></div>
          <div><strong style="display:inline-block; width: 220px;">BENCHMARK &amp; HARNESS:</strong> <span class="archival-badge retained">RETAINED AS RESEARCH ASSET</span></div>
          <div><strong style="display:inline-block; width: 220px;">EMPIRICAL OBSERVATIONS:</strong> <span class="archival-badge retained">PRESERVED (90 RUNS)</span></div>
        </div>

        <div class="prose" style="font-size: 14px;">
          <p>
            <strong>Core Rationale:</strong> The benchmark demonstrated that modern frontier coding models already possess sufficient latent capability to diagnose and repair well-specified interaction bugs without domain-specific skill intervention. The specialized skill introduced a ~1.91&times; token cost penalty and a ~2.44&times; latency overhead without improving repair outcomes.
          </p>
          <p style="margin-bottom: 0;">
            The benchmark itself, however, remains a uniquely rigorous instrument: it features private behavioral oracles, distinguishes source churn from functional repairs, isolates protocol compliance from actual bug fixes, and rigorously scores ambiguous intent. It is preserved for future evaluations of agent architectures.
          </p>
        </div>
      </div>
    </section>

    {render_footer()}
  </div>
  <script src="./assets/showroom.js"></script>
</body>
</html>
"""
    with open(os.path.join(SHOWROOM_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote showroom/index.html")

def build_cases_page(summary, cases):
    # Pre-render table rows for static fallback
    rows_html = ""
    for c in cases:
        b_verdict = format_verdict_html(c["runs"]["baseline"]["verdict"])
        g_verdict = format_verdict_html(c["runs"]["generic"]["verdict"])
        d_verdict = format_verdict_html(c["runs"]["doctor"]["verdict"])
        is_signal = c["doctor_intent_stopped"]
        row_style = 'style="background: #FEF3C7;"' if is_signal else ''

        rows_html += f"""
        <tr {row_style} data-case-id="{c['case_id']}" class="case-row" style="cursor: pointer;">
          <td style="font-family: var(--font-mono); font-weight: 600;">{c['case_id']}</td>
          <td>
            <a href="#case-{c['case_id']}" class="case-name-link" style="font-weight: 600; color: var(--ink-primary); text-decoration: none;">{c['name']}</a>
            {'<span class="archival-badge retained" style="margin-left: 6px; font-size: 9px;">Doctor Stopped</span>' if is_signal else ''}
          </td>
          <td><span class="archival-badge" style="background: var(--bg-secondary); border: 1px solid var(--rule-border);">{c['outcome']}</span></td>
          <td style="font-family: var(--font-mono); font-size: 11px;">{c['difficulty']}</td>
          <td style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">{c['runtime']}</td>
          <td>{b_verdict}</td>
          <td>{g_verdict}</td>
          <td>{d_verdict}</td>
        </tr>
        """

    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Case Explorer &bull; Interaction Doctor Benchmark</title>
  <link rel="stylesheet" href="./assets/showroom.css">
</head>
<body>
  <div class="site-wrapper">
    {render_masthead("cases")}

    <section class="section-block">
      <div class="section-label">Case Corpus Dossier</div>
      <h1 class="section-title">Benchmark Case Explorer (30 Fixtures)</h1>
      <p class="lead-statement">
        Inspect all 30 benchmark test fixtures, private test oracles, and the 90 comparative observations recorded across Baseline, Generic Rigor, and Doctor v1.
      </p>

      <!-- Filter Toolbar -->
      <div class="filter-toolbar">
        <div class="filter-group">
          <span class="filter-label">Outcome:</span>
          <button class="filter-btn active" data-filter-type="outcome" data-filter-val="ALL">All (30)</button>
          <button class="filter-btn" data-filter-type="outcome" data-filter-val="YES">YES: Defects (19)</button>
          <button class="filter-btn" data-filter-type="outcome" data-filter-val="NO">NO: Controls (5)</button>
          <button class="filter-btn" data-filter-type="outcome" data-filter-val="NEEDS_INTENT">NEEDS_INTENT: Ambiguity (6)</button>
        </div>

        <div class="filter-group">
          <span class="filter-label">Difficulty:</span>
          <button class="filter-btn active" data-filter-type="difficulty" data-filter-val="ALL">All</button>
          <button class="filter-btn" data-filter-type="difficulty" data-filter-val="T1">T1 (Basic)</button>
          <button class="filter-btn" data-filter-type="difficulty" data-filter-val="T2">T2 (Lifecycle/Multi-Actor)</button>
        </div>

        <div class="filter-group" style="margin-left: auto;">
          <input type="text" id="case-search" placeholder="Search case name, ID, runtime..." style="padding: 4px 8px; font-family: var(--font-mono); font-size: 11px; border: 1px solid var(--rule-border); border-radius: var(--radius-sm); width: 220px;">
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">
        <span id="filtered-count">Showing 30 of 30 cases</span>
        <span>Click any row to open the full test case dossier</span>
      </div>

      <!-- Case Table -->
      <div class="archival-table-wrap">
        <table class="archival-table">
          <thead>
            <tr>
              <th style="width: 48px;">ID</th>
              <th>Case Name</th>
              <th style="width: 100px;">Expected</th>
              <th style="width: 60px;">Tier</th>
              <th style="width: 140px;">Runtime</th>
              <th>Arm A: Baseline</th>
              <th>Arm B: Generic</th>
              <th>Arm C: Doctor</th>
            </tr>
          </thead>
          <tbody id="cases-table-body">
            {rows_html}
          </tbody>
        </table>
      </div>
    </section>

    {render_footer()}
  </div>

  <!-- Detail Slide-Over Drawer -->
  <div class="case-drawer-overlay" id="case-drawer-overlay">
    <div class="case-drawer" id="case-drawer">
      <div class="case-drawer-header">
        <div style="font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; color: var(--ink-muted);">
          Inspection Drawer
        </div>
        <button class="case-drawer-close" id="case-drawer-close">&times; Close</button>
      </div>
      <div id="case-drawer-content">
        <!-- Injected dynamically by showroom.js -->
      </div>
    </div>
  </div>

  <script src="./assets/showroom.js"></script>
</body>
</html>
"""
    with open(os.path.join(SHOWROOM_DIR, "cases.html"), "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote showroom/cases.html")

def build_methodology_page(summary, methodology):
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Methodology &amp; Replication &bull; Interaction Doctor Benchmark</title>
  <link rel="stylesheet" href="./assets/showroom.css">
</head>
<body>
  <div class="site-wrapper">
    {render_masthead("methodology")}

    <section class="section-block">
      <div class="section-label">Experimental Protocol</div>
      <h1 class="section-title">Benchmark Methodology &amp; Reproducibility Guide</h1>
      <p class="lead-statement">
        A complete specification of experimental variables, isolation architecture, scoring oracles, preflight qualification limitations, and replication commands.
      </p>

      <div class="prose">
        <h3>1. The Research Question</h3>
        <p>
          Does injecting a domain-specialized interaction-ownership coding skill (Interaction Doctor v1) into a frontier coding agent (<code>claude-sonnet-5</code>) improve its ability to diagnose and repair real-world interaction bugs, compared to the baseline agent or a generic rigorous prompt control?
        </p>

        <h3>2. Three Experimental Arms</h3>
        <ul>
          <li><strong>Arm A (Baseline):</strong> The frontier coding model provided solely with the task instructions and the project fixture. Measures the model's natural interaction troubleshooting capabilities.</li>
          <li><strong>Arm B (Generic Rigor):</strong> The exact same model with a generic "careful review / edge-case audit" instruction appended to the prompt, without any Interaction Doctor terminology or formal protocol. Controls for prompt length and diligence bias.</li>
          <li><strong>Arm C (Doctor v1):</strong> The exact same model with the frozen Interaction Doctor v1 skill injected into the workspace's <code>.claude/skills/</code> directory and explicit instruction to apply the skill.</li>
        </ul>

        <h3>3. Isolation Architecture (v6 Native Sandboxing)</h3>
        <p>
          Each test observation was executed in an ephemeral, completely isolated workspace created in <code>$TMPDIR/interaction-doctor-bench/</code> outside the repository root. Workspaces were created, executed, graded, archived, and wiped strictly sequentially.
        </p>
        <p>
          Tool access was locked down using Claude Code's native architecture under <code>--permission-mode dontAsk</code>:
        </p>
        <ul>
          <li><strong>File Tools:</strong> Built-in <code>Read</code>, <code>Edit</code>, <code>Write</code>, <code>Glob</code>, and <code>Grep</code> were restricted via inline per-run settings rules to the temporary workspace directory only. Access to the repository root, credential paths (<code>~/.ssh</code>, <code>~/.aws</code>, <code>~/.claude</code>, macOS Keychain), and private test oracles was denied fail-closed.</li>
          <li><strong>Bash Sandbox:</strong> Spawns were constrained via macOS Seatbelt sandbox policies configured fail-closed (<code>failIfUnavailable: true</code>, <code>network.strictAllowlist: true</code>, <code>network.allowedDomains: []</code>).</li>
          <li><strong>Disallowed Tools:</strong> Web search and web fetching tools (<code>WebSearch</code>, <code>WebFetch</code>) were explicitly forbidden to prevent web leakage or external retrieval.</li>
        </ul>

        <h3>4. Private Oracles &amp; Scoring</h3>
        <p>
          Grading is entirely deterministic and automated via <code>benchmark/graders/grade_run.py</code>. The evaluated agent is never shown the test assertions or the private ground truth:
        </p>
        <ul>
          <li><strong>Repair Success:</strong> Target assertions in private <code>test.js</code> pass on the agent's edited code.</li>
          <li><strong>Regression Check:</strong> All non-target assertions that held on the unmodified starting fixture must continue to hold.</li>
          <li><strong>Source Churn vs Functional Change:</strong> Graders distinguish raw byte diffs (comments, whitespace) from actual behavioral alterations verified by state probes.</li>
          <li><strong>NEEDS_INTENT Scoring:</strong> On ambiguous tasks, an agent is penalized for unilateral code modifications (intent guessing) and credited only when it identifies the ambiguity and stops to ask for user clarification.</li>
        </ul>

        <h3>5. Preflight Qualification Limitation (Preserved Caveat)</h3>
        <div class="verdict-callout" style="border-left-color: var(--status-ambiguity); background: #FFFBEB;">
          <div class="verdict-callout-title" style="color: var(--status-ambiguity);">Qualification Gate Limitation Note</div>
          <div class="verdict-callout-text" style="font-size: 14px;">
            The official paid preflight status before the 90-run batch was <strong>HOLD (READY_FOR_EMPIRICAL_90_RUNS = False)</strong>. This hold was issued because the evaluated models did not execute the diagnostic probe appendix instructions embedded in the preflight prompt. Doctor executed its bash probes successfully but skipped builtin read probes. This was recognized as prompt probe-compliance insufficiency rather than sandbox infrastructure failure; the 90-run empirical batch was executed under an explicit qualification waiver. Freeze verification and workspace isolation remained active throughout.
          </div>
        </div>

        <h3>6. Execution History &amp; Retry Policy</h3>
        <ul>
          <li><strong>Cases 001–014:</strong> Sourced from valid first-attempt runs (<code>run-01</code>).</li>
          <li><strong>Cases 015–030:</strong> Initial runs hit Anthropic API 429 concurrency/session limits. Failed infrastructure traces were archived, and valid observations were collected from <code>run-03</code> after the rate-limit window cleared.</li>
          <li><strong>No Result Cherry-Picking:</strong> No successful or completed run was ever rerun to improve its result.</li>
        </ul>

        <h3>7. Scope Constraint: UNMODELED Count = 0</h3>
        <p>
          All 30 benchmark cases represent modeled interaction paradigms (pointer, touch, keyboard, focus, timing, composition, analog MIDI shims). <strong>The benchmark contains exactly 0 UNMODELED cases</strong>. Consequently, this benchmark makes no empirical claims regarding an agent's ability to recognize or handle unsupported physical interaction modalities.
        </p>

        <h3>8. How to Reproduce</h3>
        <p>
          Researchers with access to Claude Code can verify the benchmark freeze and run the self-tests locally from the repository root:
        </p>
        <div class="code-block">
# 1. Verify freeze integrity against frozen hashes
python3 benchmark/design/verify_experiment_freeze.py

# 2. Run grader self-tests (verifies scoring logic against ground truth)
python3 benchmark/graders/grade_run_selftest.py

# 3. Validate showroom dataset against source-of-truth JSON
python3 scripts/validate_showroom_data.py
        </div>
      </div>
    </section>

    {render_footer()}
  </div>
</body>
</html>
"""
    with open(os.path.join(SHOWROOM_DIR, "methodology.html"), "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote showroom/methodology.html")

def main():
    summary, cases, methodology = load_data()
    generate_js()
    build_index_page(summary, cases)
    build_cases_page(summary, cases)
    build_methodology_page(summary, methodology)
    print("All showroom pages successfully generated.")

if __name__ == '__main__':
    main()
