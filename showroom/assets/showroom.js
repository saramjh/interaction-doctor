// Interaction Doctor Showroom Client Scripts
// Handles Case Explorer filtering, detail drawer navigation, accessible keyboard interaction, and localization

(function() {
  'use strict';

  var casesData = [];
  var currentFilterOutcome = 'ALL';
  var currentFilterDifficulty = 'ALL';
  var currentSearchQuery = '';
  var isKo = (document.documentElement.lang === 'ko') || (window.location.pathname.indexOf('.ko.html') !== -1);

  document.addEventListener('DOMContentLoaded', init);

  function init() {
    initCaseExplorer();
    initDrawer();
    initLangSwitch();
  }

  function initLangSwitch() {
    updateLangLinks();
    window.addEventListener('hashchange', updateLangLinks);
  }

  function updateLangLinks() {
    var hash = window.location.hash;
    var langBtns = document.querySelectorAll('.lang-btn');
    langBtns.forEach(function(btn) {
      var baseHref = btn.getAttribute('data-base-href');
      if (!baseHref) {
        baseHref = btn.getAttribute('href').split('#')[0];
        btn.setAttribute('data-base-href', baseHref);
      }
      btn.setAttribute('href', hash ? (baseHref + hash) : baseHref);
    });
  }

  function initCaseExplorer() {
    var tableBody = document.getElementById('cases-table-body');
    if (!tableBody) return; // Not on cases.html / cases.ko.html

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
      if (isKo) {
        countDisplay.textContent = '총 ' + casesData.length + '개 중 ' + filtered.length + '개 케이스 표시 중';
      } else {
        countDisplay.textContent = 'Showing ' + filtered.length + ' of ' + casesData.length + ' cases';
      }
    }

    if (filtered.length === 0) {
      var emptyMsg = isKo ? '현재 필터 조건과 일치하는 케이스가 없습니다.' : 'No cases match current filter criteria.';
      tableBody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 32px; color: var(--ink-muted); font-family: var(--font-mono);">' + emptyMsg + '</td></tr>';
      return;
    }

    var html = '';
    filtered.forEach(function(c) {
      var bVerdict = formatVerdict(c.runs.baseline.verdict, isKo);
      var gVerdict = formatVerdict(c.runs.generic.verdict, isKo);
      var dVerdict = formatVerdict(c.runs.doctor.verdict, isKo);

      var isSignalCase = c.doctor_intent_stopped;
      var rowStyle = isSignalCase ? 'style="background: #FEF3C7;"' : '';
      var badgeLabel = isKo ? '닥터 중단' : 'Doctor Stopped';

      html += '<tr ' + rowStyle + ' data-case-id="' + c.case_id + '" class="case-row" style="cursor: pointer;">' +
        '<td style="font-family: var(--font-mono); font-weight: 600;">' + c.case_id + '</td>' +
        '<td>' +
          '<a href="#case-' + c.case_id + '" class="case-name-link" style="font-weight: 600; color: var(--ink-primary); text-decoration: none;">' + escapeHtml(c.name) + '</a>' +
          (isSignalCase ? ' <span class="archival-badge retained" style="margin-left: 6px; font-size: 9px;">' + badgeLabel + '</span>' : '') +
        '</td>' +
        '<td><span class="archival-badge" style="background: var(--bg-secondary); border: 1px solid var(--rule-border);">' + c.outcome + '</span></td>' +
        '<td style="font-family: var(--font-mono); font-size: 11px;">' + c.difficulty + '</td>' +
        '<td style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">' + escapeHtml(c.runtime) + '</td>' +
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

  function formatVerdict(verdict, ko) {
    if (!verdict) return '<span style="color: var(--ink-faint);">—</span>';
    var cls = 'unnecessary_source_churn';
    var label = verdict.replace(/_/g, ' ');

    if (verdict === 'correct_repair') {
      cls = 'correct_repair';
      label = ko ? '수정 성공' : 'repair pass';
    } else if (verdict === 'correct_no_op') {
      cls = 'correct_no_op';
      label = ko ? '정상 유지' : 'correct no-op';
    } else if (verdict === 'needs_manual_review_ambiguity') {
      cls = 'needs_manual_review_ambiguity';
      label = ko ? '모호성 중단' : 'stopped (review)';
    } else if (verdict === 'intent_guessing_violation') {
      cls = 'intent_guessing_violation';
      label = ko ? '임의 추측' : 'intent guess';
    } else if (verdict === 'defect_not_fixed') {
      cls = 'intent_guessing_violation';
      label = ko ? '미수정' : 'not fixed';
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
    updateLangLinks();
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

    var relationsStr = (c.relations && c.relations.length) ? c.relations.join(', ') : (isKo ? '없음' : 'None');
    var envStr = (c.environmental_claims && c.environmental_claims.length) ? c.environmental_claims.join(', ') : (isKo ? '표준 DOM/포인터' : 'Standard DOM/pointer');
    var oraclesHtml = (c.primary_hidden_oracles && c.primary_hidden_oracles.length)
      ? c.primary_hidden_oracles.map(function(o) { return '<li>' + escapeHtml(o) + '</li>'; }).join('')
      : ('<li>' + (isKo ? '표준 통과 단언문' : 'Standard pass assertions') + '</li>');

    var headerSub = isKo
      ? ('케이스 ' + c.case_id + ' &bull; 결과: ' + c.outcome + ' &bull; 난이도: ' + c.difficulty)
      : ('Case ' + c.case_id + ' &bull; ' + c.outcome + ' Outcome &bull; Difficulty ' + c.difficulty);

    var runtimeSub = isKo
      ? ('슬러그: ' + c.slug + ' &bull; 런타임: ' + c.runtime)
      : ('Slug: ' + c.slug + ' &bull; Runtime: ' + c.runtime);

    var signalCallout = c.doctor_intent_stopped ? (
      isKo ? (
        '<div class="verdict-callout" style="border-left-color: var(--arm-retained); margin: 0 0 20px 0;">' +
          '<div class="verdict-callout-title" style="color: var(--arm-retained);">닥터 모호성 감지 신호 포착</div>' +
          '<div class="verdict-callout-text" style="font-size: 14px;">' +
            '이 케이스에서 Interaction Doctor v1은 미확정 제품 정책을 독단적으로 추측하여 코드를 고치지 않고, 수정을 멈추고 사용자 확인을 요청(NEEDS_INTENT)했습니다. 반면 베이스라인(A군)과 일반 감사(B군)는 일방적으로 정책을 추측하여 코드를 임의 수정했습니다.' +
          '</div>' +
        '</div>'
      ) : (
        '<div class="verdict-callout" style="border-left-color: var(--arm-retained); margin: 0 0 20px 0;">' +
          '<div class="verdict-callout-title" style="color: var(--arm-retained);">Doctor Ambiguity Signal Detected</div>' +
          '<div class="verdict-callout-text" style="font-size: 14px;">' +
            'On this case, Interaction Doctor v1 successfully halted execution with a manual review disposition rather than guessing an unresolved product policy. Both Baseline and Generic guessed and modified code unilaterally.' +
          '</div>' +
        '</div>'
      )
    ) : '';

    var telemetryTitle = isKo ? '실험군별 판정 및 텔레메트리' : 'Experimental Arm Verdicts & Telemetry';
    var thArm = isKo ? '실험군' : 'Arm';
    var thVerdict = isKo ? '판정' : 'Verdict';
    var thCost = isKo ? '비용' : 'Cost';
    var thTime = isKo ? '시간' : 'Time';
    var thTools = isKo ? '도구' : 'Tools';

    var armBaselineLabel = isKo ? 'A군: 베이스라인' : 'Baseline';
    var armGenericLabel = isKo ? 'B군: 일반 감사' : 'Generic';
    var armDoctorLabel = isKo ? 'C군: 닥터' : 'Doctor';

    var promptTitle = isKo ? '에이전트 태스크 프롬프트' : 'Agent Task Prompt';
    var oraclesTitle = isKo ? '비공개 테스트 오라클 및 불변 조건' : 'Primary Hidden Oracles & Invariants';

    var metaRelations = isKo ? '연관 관계: ' : 'Relations: ';
    var metaEnv = isKo ? '환경 가정: ' : 'Environment Claims: ';
    var metaRisk = isKo ? '오염 위험: ' : 'Contamination Risk: ';
    var metaReval = isKo ? ' &bull; 재귀적 재검증 필요: ' : ' &bull; Revalidation Required: ';
    var revalVal = isKo ? (c.requires_recursive_revalidation ? '예' : '아니오') : c.requires_recursive_revalidation;

    content.innerHTML = '<div style="margin-bottom: 20px;">' +
      '<div style="font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 4px;">' +
        headerSub +
      '</div>' +
      '<h2 style="font-family: var(--font-sans); font-size: 24px; font-weight: 700; color: var(--ink-primary); margin-bottom: 8px;">' +
        escapeHtml(c.name) +
      '</h2>' +
      '<div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">' +
        runtimeSub +
      '</div>' +
    '</div>' +

    signalCallout +

    '<div style="background: var(--bg-secondary); border: 1px solid var(--rule-border); padding: 16px; margin-bottom: 24px;">' +
      '<div style="font-family: var(--font-mono); font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 12px; color: var(--ink-secondary);">' +
        telemetryTitle +
      '</div>' +
      '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">' +
        '<thead>' +
          '<tr style="border-bottom: 1px solid var(--rule-border); text-align: left; font-family: var(--font-mono); font-size: 10px; color: var(--ink-muted);">' +
            '<th style="padding: 6px;">' + thArm + '</th>' +
            '<th style="padding: 6px;">' + thVerdict + '</th>' +
            '<th style="padding: 6px; text-align: right;">' + thCost + '</th>' +
            '<th style="padding: 6px; text-align: right;">' + thTime + '</th>' +
            '<th style="padding: 6px; text-align: right;">' + thTools + '</th>' +
          '</tr>' +
        '</thead>' +
        '<tbody>' +
          '<tr style="border-bottom: 1px solid var(--rule-fine);">' +
            '<td style="padding: 6px; font-weight: 600;"><span class="arm-dot baseline"></span> ' + armBaselineLabel + '</td>' +
            '<td style="padding: 6px;">' + formatVerdict(c.runs.baseline.verdict, isKo) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">$' + c.runs.baseline.cost.toFixed(4) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.baseline.seconds.toFixed(1) + 's</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.baseline.tools + '</td>' +
          '</tr>' +
          '<tr style="border-bottom: 1px solid var(--rule-fine);">' +
            '<td style="padding: 6px; font-weight: 600;"><span class="arm-dot generic"></span> ' + armGenericLabel + '</td>' +
            '<td style="padding: 6px;">' + formatVerdict(c.runs.generic.verdict, isKo) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">$' + c.runs.generic.cost.toFixed(4) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.generic.seconds.toFixed(1) + 's</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.generic.tools + '</td>' +
          '</tr>' +
          '<tr>' +
            '<td style="padding: 6px; font-weight: 600;"><span class="arm-dot doctor"></span> ' + armDoctorLabel + '</td>' +
            '<td style="padding: 6px;">' + formatVerdict(c.runs.doctor.verdict, isKo) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">$' + c.runs.doctor.cost.toFixed(4) + '</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.doctor.seconds.toFixed(1) + 's</td>' +
            '<td style="padding: 6px; text-align: right; font-family: var(--font-mono);">' + c.runs.doctor.tools + '</td>' +
          '</tr>' +
        '</tbody>' +
      '</table>' +
    '</div>' +

    '<div style="margin-bottom: 24px;">' +
      '<h4 style="font-family: var(--font-mono); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-secondary); margin-bottom: 8px;">' +
        promptTitle +
      '</h4>' +
      '<div style="background: var(--bg-surface); border: 1px solid var(--rule-border); padding: 16px; font-family: var(--font-mono); font-size: 12px; line-height: 1.6; white-space: pre-wrap;">' + escapeHtml(c.task_description) + '</div>' +
    '</div>' +

    '<div style="margin-bottom: 24px;">' +
      '<h4 style="font-family: var(--font-mono); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--ink-secondary); margin-bottom: 8px;">' +
        oraclesTitle +
      '</h4>' +
      '<ul style="padding-left: 20px; font-size: 13px; line-height: 1.5; color: var(--ink-secondary);">' +
        oraclesHtml +
      '</ul>' +
    '</div>' +

    '<div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted); border-top: 1px solid var(--rule-fine); padding-top: 12px;">' +
      '<div>' + metaRelations + escapeHtml(relationsStr) + '</div>' +
      '<div>' + metaEnv + escapeHtml(envStr) + '</div>' +
      '<div>' + metaRisk + escapeHtml(c.contamination_risk) + metaReval + revalVal + '</div>' +
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
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

})();
