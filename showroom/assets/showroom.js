// Interaction Doctor Showroom Client Scripts
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
