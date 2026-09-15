#!/usr/bin/env python3
"""Generates static showroom HTML pages from showroom/data JSON datasets.

Generates:
  - showroom/assets/showroom.js
  - showroom/index.html (Executive Summary & Postmortem Dossier - English)
  - showroom/index.ko.html (Executive Summary & Postmortem Dossier - Korean)
  - showroom/cases.html (Interactive 30-Case Matrix & Detail Drawer - English)
  - showroom/cases.ko.html (Interactive 30-Case Matrix & Detail Drawer - Korean)
  - showroom/methodology.html (Methodology, Controls, Limitations & Replication - English)
  - showroom/methodology.ko.html (Methodology, Controls, Limitations & Replication - Korean)
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
"""
    with open(os.path.join(ASSETS_DIR, "showroom.js"), "w", encoding="utf-8") as f:
        f.write(js_content)
    print("Wrote showroom/assets/showroom.js")

def render_masthead(active_page="index", lang="en"):
    is_ko = (lang == "ko")
    
    en_links = {
        "index": "index.html",
        "cases": "cases.html",
        "methodology": "methodology.html"
    }
    ko_links = {
        "index": "index.ko.html",
        "cases": "cases.ko.html",
        "methodology": "methodology.ko.html"
    }
    
    curr_en = en_links.get(active_page, "index.html")
    curr_ko = ko_links.get(active_page, "index.ko.html")
    
    if is_ko:
        meta_dossier = "문서: EXP-ID-2026-V1 &bull; 저장소: saramjh/interaction-doctor"
        badge_skill = "스킬: 개발 중단"
        badge_bench = "벤치마크: 보존 자산"
        badge_runs = "N = 30 &times; 3 = 90회 실행"
        brand_title = "Interaction Doctor 벤치마크"
        brand_href = "./index.ko.html"
        nav_report = "총괄 보고서"
        nav_cases = "케이스 매트릭스 (30)"
        nav_meth = "방법론 및 재현 가이드"
        nav_github = "GitHub 저장소 &rarr;"
        href_report = "./index.ko.html"
        href_cases = "./cases.ko.html"
        href_meth = "./methodology.ko.html"
    else:
        meta_dossier = "DOSSIER: EXP-ID-2026-V1 &bull; REPO: saramjh/interaction-doctor"
        badge_skill = "Skill: Discontinued"
        badge_bench = "Benchmark: Retained"
        badge_runs = "N = 30 &times; 3 = 90 Runs"
        brand_title = "Interaction Doctor Benchmark"
        brand_href = "./index.html"
        nav_report = "Executive Report"
        nav_cases = "Case Matrix (30)"
        nav_meth = "Methodology &amp; Replication"
        nav_github = "GitHub Archive &rarr;"
        href_report = "./index.html"
        href_cases = "./cases.html"
        href_meth = "./methodology.html"

    en_active_cls = "lang-btn" + (" active" if not is_ko else "")
    ko_active_cls = "lang-btn" + (" active" if is_ko else "")

    return f"""
    <header class="masthead">
      <div class="masthead-meta">
        <div>{meta_dossier}</div>
        <div class="masthead-badge-group">
          <span class="archival-badge discontinued">{badge_skill}</span>
          <span class="archival-badge retained">{badge_bench}</span>
          <span>{badge_runs}</span>
        </div>
      </div>
      <div class="masthead-nav-bar">
        <div class="masthead-title">
          <a href="{brand_href}">{brand_title}</a>
        </div>
        <nav>
          <ul class="nav-links">
            <li><a href="{href_report}" class="{'active' if active_page == 'index' else ''}">{nav_report}</a></li>
            <li><a href="{href_cases}" class="{'active' if active_page == 'cases' else ''}">{nav_cases}</a></li>
            <li><a href="{href_meth}" class="{'active' if active_page == 'methodology' else ''}">{nav_meth}</a></li>
            <li><a href="https://github.com/saramjh/interaction-doctor" target="_blank" rel="noopener">{nav_github}</a></li>
          </ul>
        </nav>
        <div class="lang-switch-group">
          <a href="./{curr_en}" class="{en_active_cls}">EN</a>
          <span class="lang-divider">|</span>
          <a href="./{curr_ko}" class="{ko_active_cls}">한국어</a>
        </div>
      </div>
    </header>
    """

def render_footer(lang="en"):
    is_ko = (lang == "ko")
    if is_ko:
        line1_left = "Interaction Doctor 벤치마크 &bull; 동결된 연구 자산 (2026)"
        line1_right = "독립 변수: 동결된 Interaction Doctor v1 스킬"
        link_repo = "저장소 소스코드"
        link_protocol = "재현 프로토콜"
        protocol_href = "./methodology.ko.html"
    else:
        line1_left = "Interaction Doctor Benchmark &bull; Frozen Research Asset (2026)"
        line1_right = "Independent Variable: Frozen Interaction Doctor v1 Skill"
        link_repo = "Repository Source"
        link_protocol = "Replication Protocol"
        protocol_href = "./methodology.html"

    return f"""
    <footer class="site-footer">
      <div>
        <span>{line1_left}</span>
        <span style="margin: 0 8px;">&bull;</span>
        <span>{line1_right}</span>
      </div>
      <div>
        <a href="https://github.com/saramjh/interaction-doctor" class="footer-repo-link">{link_repo}</a>
        <span style="margin: 0 8px;">&bull;</span>
        <a href="{protocol_href}">{link_protocol}</a>
      </div>
    </footer>
    """

def format_verdict_html(verdict, lang="en"):
    if not verdict:
        return '<span style="color: var(--ink-faint);">—</span>'
    cls = "unnecessary_source_churn"
    label = verdict.replace("_", " ")
    is_ko = (lang == "ko")

    if verdict == "correct_repair":
        cls = "correct_repair"
        label = "수정 성공" if is_ko else "repair pass"
    elif verdict == "correct_no_op":
        cls = "correct_no_op"
        label = "정상 유지" if is_ko else "correct no-op"
    elif verdict == "needs_manual_review_ambiguity":
        cls = "needs_manual_review_ambiguity"
        label = "모호성 중단" if is_ko else "stopped (review)"
    elif verdict in ("intent_guessing_violation", "defect_not_fixed"):
        cls = "intent_guessing_violation"
        if verdict == "intent_guessing_violation":
            label = "임의 추측" if is_ko else "intent guess"
        else:
            label = "미수정" if is_ko else "not fixed"
    return f'<span class="grid-cell-verdict {cls}">{label}</span>'

def build_index_page(summary, cases, lang="en"):
    is_ko = (lang == "ko")
    b = summary["arms"]["baseline"]
    g = summary["arms"]["generic"]
    d = summary["arms"]["doctor"]

    cases_url = "./cases.ko.html" if is_ko else "./cases.html"

    # Generate NEEDS_INTENT rows
    needs_intent_cases = [c for c in cases if c["outcome"] == "NEEDS_INTENT"]
    ni_table_rows = ""
    for c in needs_intent_cases:
        bv = format_verdict_html(c["runs"]["baseline"]["verdict"], lang)
        gv = format_verdict_html(c["runs"]["generic"]["verdict"], lang)
        dv = format_verdict_html(c["runs"]["doctor"]["verdict"], lang)
        stopped = c["doctor_intent_stopped"]
        highlight = 'style="background: #FEF3C7;"' if stopped else ''
        badge_text = "닥터 중단" if is_ko else "Doctor Stopped"
        badge_span = f'<span class="archival-badge retained" style="margin-left:6px; font-size:9px;">{badge_text}</span>' if stopped else ''
        
        if is_ko:
            behavior_desc = '미확정 정책 추측을 거부하고 사용자에게 수동 확인을 요청함' if stopped else '사용자 확인 없이 독단적으로 해결 정책을 선택하여 코드를 수정함'
        else:
            behavior_desc = 'Refused to guess unresolved policy; requested manual clarification' if stopped else 'Unilaterally selected a resolution policy without asking user'

        ni_table_rows += f"""
        <tr {highlight}>
          <td style="font-family: var(--font-mono); font-weight: 600;">{c['case_id']}</td>
          <td>
            <a href="{cases_url}#case-{c['case_id']}" style="font-weight: 600; color: var(--ink-primary); text-decoration: none;">{html.escape(c['name'])}</a>
            {badge_span}
          </td>
          <td>{bv}</td>
          <td>{gv}</td>
          <td>{dv}</td>
          <td style="font-size: 12px; color: var(--ink-secondary);">{behavior_desc}</td>
        </tr>
        """

    # Generate 30-case matrix HTML rows
    matrix_rows = ""
    for c in cases:
        b_dot = format_verdict_html(c["runs"]["baseline"]["verdict"], lang)
        g_dot = format_verdict_html(c["runs"]["generic"]["verdict"], lang)
        d_dot = format_verdict_html(c["runs"]["doctor"]["verdict"], lang)
        stopped = c["doctor_intent_stopped"]
        row_style = 'style="background: #FEF3C7;"' if stopped else ''
        badge_text = "중단" if is_ko else "STOPPED"
        badge_span = f'<span class="archival-badge retained" style="margin-left:4px; font-size:8px;">{badge_text}</span>' if stopped else ''
        matrix_rows += f"""
        <tr {row_style}>
          <td style="font-family: var(--font-mono); font-weight: 600; padding: 6px 10px;">{c['case_id']}</td>
          <td style="padding: 6px 10px;">
            <a href="{cases_url}#case-{c['case_id']}" style="color: var(--ink-primary); font-weight: 500; text-decoration: none;">{html.escape(c['name'])}</a>
            {badge_span}
          </td>
          <td style="padding: 6px 10px;"><span class="archival-badge" style="background:var(--bg-secondary); border:1px solid var(--rule-border); font-size:9px;">{c['outcome']}</span></td>
          <td style="padding: 6px 10px;">{b_dot}</td>
          <td style="padding: 6px 10px;">{g_dot}</td>
          <td style="padding: 6px 10px;">{d_dot}</td>
        </tr>
        """

    if is_ko:
        page_title = "Interaction Doctor 벤치마크 &bull; 실증 평가 회고록"
        section_dossier = "실증 평가 회고록 (Dossier)"
        headline = "비용을 정당화하지 못하고 폐기된 코딩 에이전트 스킬의 실증 기록."
        subtitle = "프론티어 모델을 대상으로 인터랙션 결함 진단, 소유권 수정, 의도 모호성 처리를 측정한 30개 케이스, 90회 실행 대조 벤치마크."
        lead = "특화 스킬인 Interaction Doctor는 기본 모델(Baseline) 대비 결함 수정 성공률을 전혀 개선하지 못했으며(0% 향상), 토큰 비용은 약 1.91배, 지연 시간은 약 2.44배 급증시켰습니다. 이에 따라 스킬 제품화는 공식 <strong>중단(DISCONTINUED)</strong>되었으며, 본 벤치마크는 독립 연구 자산(RETAINED)으로 영구 보존됩니다."
        param_title = "실험 통제 매개변수"
        param_model = "평가 모델"
        param_effort = "추론 강도 (Effort)"
        param_corpus = "벤치마크 코퍼스"
        param_corpus_val = "30개 케이스 (19 결함, 5 대조군, 6 모호성)"
        param_arms = "대조 실험군"
        param_arms_val = "3개 군 (기본 베이스라인, 일반 감사, 인터랙션 닥터 v1)"
        param_obs = "유효 관측치"
        param_obs_val = "90회 실행 (케이스 30개 &times; 3군)"
        param_sandbox = "실행 샌드박스"
        param_sandbox_val = "macOS Seatbelt (Fail-closed 네이티브 격리)"
        param_commit = "동결 커밋"
        param_outcome = "제품 최종 처분"
        param_outcome_val = "개발 중단 (DISCONTINUED)"

        sec_findings = "핵심 관측 결과"
        title_findings = "총괄 요약 (Executive Summary)"
        card1_label = "모든 군에서 동일한 수정 성공률"
        card1_desc = "기본 모델(A군), 일반 감사(B군), 닥터(C군) 모두 19개 결함 케이스를 100% 수정했습니다. 특화 스킬이 제공한 점진적 수정 능력 향상은 <strong>0%</strong>였습니다."
        card2_num = "~1.91배"
        card2_label = "닥터 스킬 실행 비용 비율"
        card2_desc = f"총 비용 ${d['total_cost']:.2f} (회당 ${d['mean_cost']:.3f}) vs 베이스라인 ${b['total_cost']:.2f} (회당 ${b['mean_cost']:.3f}). 도구 호출은 1.54배, 실행 지연 시간은 2.44배 증가했습니다."
        card3_num = "2 / 6"
        card3_label = "닥터가 멈추고 질문한 모호성 케이스"
        card3_desc = "닥터는 요구사항이 모호한 6개 케이스 중 2개(011, 016)에서 임의 수정을 멈추고 확인을 요청했습니다. 베이스라인과 일반 감사는 6개 모두 독단적으로 추측하여 코드를 수정했습니다."
        verdict_title = "최종 실증 판정"
        verdict_text = '"특화 스킬은 본 벤치마크에서 결함 수정 능력을 전혀 향상시키지 못하면서 막대한 실행 비용을 초래했습니다. 2건의 케이스에서 불필요한 정책 추측을 방지하는 제한적 신호를 보였으나, 독립된 제품으로서의 사업적·기술적 타당성을 입증하기에는 현저히 부족했습니다."'

        sec_measurements = "실증 측정 데이터"
        title_table = "3개 실험군 통제 대조표"
        prose_table = "모든 90회 실행은 동일한 프론티어 모델(<code>claude-sonnet-5</code>, medium effort)로 평가되었습니다. 유일한 독립 변수는 에이전트 환경에 주입된 개입 조건(스킬/프롬프트)뿐이었습니다."

        th_metric = "평가 지표"
        th_a = "<span class=\"arm-dot baseline\"></span> A군: 베이스라인"
        th_b = "<span class=\"arm-dot generic\"></span> B군: 일반 감사"
        th_c = "<span class=\"arm-dot doctor\"></span> C군: 인터랙션 닥터"
        th_delta = "실험적 차이 및 해석"

        r1 = ("결함 수정 성공률 (명시적 결함 케이스)", "19 / 19 (100%)", "19 / 19 (100%)", "19 / 19 (100%)", "0% 개선. 결함 해결 능력의 완전한 동등성.")
        r2 = ("정상 케이스 무변경 유지 (NO-Op)", "3 / 5 (60.0%)", "2 / 5 (40.0%)", "2 / 5 (40.0%)", "베이스라인이 불필요한 코드 변경(churn)에 덜 취약함.")
        r3 = ("기능적 오탐 (Functional False Positives)", "0 / 5 (0.0%)", "0 / 5 (0.0%)", "0 / 5 (0.0%)", "모든 군이 정상 로직의 기본 동작을 파괴하지 않음.")
        r4 = ("임의 의도 추측률 (NEEDS_INTENT)", "6 / 6 (100%)", "6 / 6 (100%)", "4 / 6 (66.7%)", "닥터가 임의 추측률을 33.3% 감소시킴 (011, 016에서 중단).")
        r5 = ("모호성 수동 확인 중단 (Manual Review Halts)", "0 / 6 (0.0%)", "0 / 6 (0.0%)", "2 / 6 (33.3%)", "유일한 긍정 신호: 불명확한 2개 케이스에서 닥터가 실행 중단.")
        r6 = ("기능 퇴행 (Measured Regressions)", "1 / 30 (3.3%)", "1 / 30 (3.3%)", "0 / 30 (0.0%)", "<em>비독립적 결과:</em> 011번에서만 발생했으며, 닥터는 수정을 멈췄기 때문에 퇴행을 피한 것임.")
        r7 = ("거짓 완료 주장 (False Closure Claims)", "0 / 30 (0.0%)", "1 / 30 (3.3%)", "0 / 30 (0.0%)", "일반 감사군(B군)이 011번에서 실패했음에도 해결 완료를 허위 주장함.")
        r8 = ("키워드 진단 휴리스틱 (Keyword Match)", "14 / 19 (73.7%)", "18 / 19 (94.7%)", "18 / 19 (94.7%)", "진단 키워드 포함 메타데이터일 뿐 실제 의미적 회상률이 아님.")
        r9 = ("총 실행 비용 (30회 합계)", f"${b['total_cost']:.4f}", f"${g['total_cost']:.4f}", f"${d['total_cost']:.4f}", "<strong>1.91배</strong> 비용 증가 (닥터 개입).")
        r10 = ("회당 평균 비용", f"${b['mean_cost']:.4f}", f"${g['mean_cost']:.4f}", f"${d['mean_cost']:.4f}", "회당 +$0.0986 추가 지출.")
        r11 = ("총 실행 시간 (Wall Clock)", f"{b['total_seconds']:.1f}초", f"{g['total_seconds']:.1f}초", f"{d['total_seconds']:.1f}초", "<strong>2.44배</strong> 실행 지연 배율.")
        r12 = ("회당 평균 실행 시간", f"{b['mean_seconds']:.1f}초", f"{g['mean_seconds']:.1f}초", f"{d['mean_seconds']:.1f}초", "회당 +40.6초 추가 지연.")
        r13 = ("총 도구 호출 횟수", f"{b['total_tools']}회", f"{g['total_tools']}회", f"{d['total_tools']}회", "<strong>1.54배</strong> 도구 호출 오버헤드.")
        r14 = ("회당 평균 도구 호출", f"{b['mean_tools']:.1f}회", f"{g['mean_tools']:.1f}회", f"{d['mean_tools']:.1f}회", "회당 +2.5회 왕복 증가.")

        chart_sec = "비교 데이터 시각화"
        chart_title_main = "비용, 지연 시간 및 수정 성공률 시각화"
        c1_title = "그림 1: 결함 수정 성공률 (명시적 결함 케이스 n=19)"
        c1_sub = "모수: 19개 결함 케이스"
        c1_caption = "동일한 막대 길이는 완전한 성능 동등성을 나타냅니다. 수정 성공률 차이는 0이었습니다."
        c2_title = "그림 2: 30회 실행 총 API 비용 ($ USD)"
        c2_sub = "모수: 군당 30회 실행"
        c2_caption = "닥터는 일반 감사 대비 81%, 베이스라인 대비 91%의 비용 페널티를 부과했습니다."
        c3_title = "그림 3: 회당 평균 실행 지연 시간 (초)"
        c3_sub = "낮을수록 빠름"
        c3_caption = "닥터는 감사 루프 오버헤드로 인해 완료까지 2.44배 더 긴 시간이 소요되었습니다."
        c4_title = "그림 4: 모호한 태스크에서의 임의 기획 추측률 (n=6)"
        c4_sub = "추측률이 낮을수록 우수함"
        c4_caption = "닥터는 2개 케이스(011, 016)에서 독단적 수정을 멈춘 반면, 베이스라인과 일반 감사는 6개 모두 추측했습니다."

        ambig_sec = "모호성 상세 분석"
        ambig_title = "NEEDS_INTENT 케이스 세부 분석"
        ambig_prose = "6개의 벤치마크 케이스는 복수의 타당한 기획 결정이 공존하는 근본적으로 불완전한 명세를 포함합니다. 에이전트가 모호성을 인식하고 독단적 결정을 내리기보다 질문을 멈추었는지를 채점했습니다."
        ambig_th_id = "ID"
        ambig_th_name = "케이스 제목"
        ambig_th_b = "베이스라인"
        ambig_th_g = "일반 감사"
        ambig_th_d = "인터랙션 닥터"
        ambig_th_outcome = "닥터 환경에서의 관측 동작"
        ambig_why_title = "왜 닥터는 011번과 016번에서만 멈추었는가?"
        ambig_why_p1 = "<code>case-011-shared-canvas-bifurcation</code>과 <code>case-016-swipe-left-double-bound</code>에서는 충돌이 동일한 DOM 타깃에 바인딩된 상충하는 2개의 이벤트 핸들러 형태로 직접 노출되었습니다. 닥터의 소유권 그래프 추출 로직이 이 물리적 충돌을 명확히 식별하여 프로토콜의 <code>NEEDS_INTENT</code> 처분을 발동시켰습니다."
        ambig_why_p2 = "반면 <code>case-004</code>, <code>case-010</code>, <code>case-013</code>, <code>case-019</code>에서는 모호성이 직접적인 동시 바인딩이 아닌 생명주기 스코프나 환경 기본값의 불일치에서 비롯되었습니다. 모델은 스킬 프롬프트를 보유하고 있었음에도 '표준적 해결책'을 스스로 합리화하며 파일을 수정했습니다."

        corpus_sec = "전체 코퍼스 조망"
        corpus_title = "30개 케이스 &times; 3개 실험군 관측 매트릭스 (90회 실행)"
        corpus_prose = "각 행은 하나의 벤치마크 픽스처를 나타냅니다. 행이나 케이스명을 클릭하면 케이스 탐색기에서 프롬프트 전문, 숨겨진 오라클 및 실행 텔레메트리를 확인할 수 있습니다."
        corpus_th_id = "ID"
        corpus_th_name = "케이스명"
        corpus_th_outcome = "결과 유형"
        corpus_th_a = "A군: 베이스라인"
        corpus_th_b = "B군: 일반 감사"
        corpus_th_c = "C군: 인터랙션 닥터"
        corpus_link_explorer = "필터 지원 케이스 탐색기 열기 &rarr;"

        post_sec = "엔지니어링 사후 회고록 (Postmortem)"
        post_title = "제품화가 실패한 이유: 3가지 아키텍처적 막다른 골목"
        post_prose = "초기 스모크 테스트에서 인터랙션 닥터를 상시 실행하면 결함 해결 이점 없이 비용만 두 배로 든다는 사실이 드러나자, 엔지니어링 팀은 스킬을 선별적으로 호출하기 위한 3가지 완화 아키텍처를 탐색했습니다. 그러나 3가지 모두 실패했습니다."

        post1_title = "1. 범용 시맨틱 평가 게이트의 딜레마 (The Universal Semantic Eval Gate Problem)"
        post1_hyp = "<strong>가설:</strong> 무거운 스킬을 로드하기 전에, 유입된 태스크가 인터랙션 소유권 문제를 포함하고 있는지 판단하는 빠르고 저렴한 업스트림 분류기 프롬프트를 모델 앞에 배치한다."
        post1_fail = "<strong>실패 원인:</strong> 연쇄적 분류기(Cascading classifier)는 비대칭적 위험을 갖습니다. 게이트의 거짓 음성(False Negative) 확률이 10%만 되어도, 하류의 전문 스킬은 해당 태스크를 아예 볼 수 없습니다. 거짓 음성을 0으로 만들기 위해 게이트의 회상률을 넓히자 사실상 거의 모든 UI 수정 작업에서 게이트가 열려 전체 비용이 다시 1.9배로 회귀했습니다."

        post2_title = "2. 모델의 자가 라우팅 실패 (The Self-Routing Failure)"
        post2_hyp = "<strong>가설:</strong> 기본 에이전트에게 간결한 도구/스킬 설명을 제공하고, 막히거나 모호성을 감지했을 때 모델 스스로 스킬을 호출하도록 한다."
        post2_fail = "<strong>실패 원인:</strong> 프론티어 모델은 인터랙션 버그를 다룰 때 심각한 메타인지적 사각지대(Meta-cognitive blindspot)를 겪습니다. 베이스라인 모델은 자신이 처음 제시한 잘못된 패치가 옳다고 확신하므로, 외부 자문을 요청하는 데 필요한 의심을 전혀 품지 않습니다. 자가 라우팅은 스킬이 가장 필요한 케이스에서 호출률이 0에 수렴했습니다."

        post3_title = "3. 네이티브 정적 탐지기 실험의 한계 (The Native Static Detector Experiment)"
        post3_hyp = "<strong>가설:</strong> IDE나 CLI에서 어휘적 AST 파싱과 정적 정규식 트리거를 사용하여 중첩 포인터 이벤트를 감지하고, LLM 게이팅 오버헤드 없이 결정론적으로 스킬을 주입한다."
        post3_fail = "<strong>실패 원인:</strong> 정적 탐지기는 프레임워크와 추상화 계층 전반에서 완전히 무력했습니다. 정상적인 표준 패턴(예: 이벤트 위임이 적용된 중첩 버튼)에서 끊임없이 오탐을 냈고, 정작 크로스 컴포넌트 생명주기 누수(예: 취소되지 않은 RAF 루프, 백그라운드 탭 리스너, 훅으로 감싸진 React Native 제스처 리스폰더)는 전혀 잡아내지 못했습니다."

        disp_sec = "처분 결정 기록 (Disposition Record)"
        disp_title = "최종 제품 처분 결정서"
        disp_cert_title = "보존 처분 결정서 &bull; EXP-202609-ID"
        disp_cert_date = "발효 일자: 2026년 9월"
        disp_item_skill = "INTERACTION DOCTOR 스킬:"
        disp_val_skill = '<span class="archival-badge discontinued">개발 중단 (DISCONTINUED)</span>'
        disp_item_bench = "벤치마크 및 하네스:"
        disp_val_bench = '<span class="archival-badge retained">연구 자산 영구 보존 (RETAINED)</span>'
        disp_item_data = "실증 관측 데이터:"
        disp_val_data = '<span class="archival-badge retained">영구 보존 (90회 실행)</span>'
        disp_rationale_lead = "<strong>핵심 결정 근거:</strong> 본 벤치마크는 최신 프론티어 코딩 모델이 도메인 특화 스킬 개입 없이도 잘 명시된 인터랙션 결함을 진단하고 수정할 수 있는 충분한 잠재 능력을 이미 보유하고 있음을 입증했습니다. 특화 스킬은 수정 능력을 향상시키지 못하면서 ~1.91배의 토큰 비용 페널티와 ~2.44배의 지연 시간 오버헤드만 초래했습니다."
        disp_rationale_body = "그러나 벤치마크 자체는 고유한 엄격성을 지닌 연구 도구로 남습니다. 비공개 동작 오라클, 무의미한 코드 변경(churn)과 기능적 수정의 구별, 프로토콜 준수와 실제 버그 픽스의 격리, 모호한 의도에 대한 엄격한 감점 체계를 갖추고 있습니다. 향후 에이전트 아키텍처 평가를 위해 본 자산을 영구 보존합니다."
    else:
        page_title = "Interaction Doctor Benchmark &bull; Empirical Postmortem"
        section_dossier = "Empirical Evaluation Dossier"
        headline = "A coding-agent skill experiment that failed to justify its cost."
        subtitle = "A 30-case, 90-run controlled benchmark measuring interaction-defect diagnosis, repair, and ambiguity handling on frontier models."
        lead = "The specialized Interaction Doctor skill provided zero measured repair advantage over the baseline model, nearly doubled token expenditure (~1.91&times;), and more than doubled latency (~2.44&times;). The skill has been <strong>discontinued</strong>. The benchmark is preserved as an independent research asset."
        param_title = "Experiment Parameters"
        param_model = "Evaluated Model"
        param_effort = "Effort Setting"
        param_corpus = "Benchmark Corpus"
        param_corpus_val = "30 cases (19 Defect, 5 Control, 6 Ambiguous)"
        param_arms = "Experimental Arms"
        param_arms_val = "3 (Baseline, Generic Rigor, Doctor v1)"
        param_obs = "Valid Observations"
        param_obs_val = "90 runs (1 per case &times; arm)"
        param_sandbox = "Execution Sandbox"
        param_sandbox_val = "macOS Seatbelt (Fail-closed native)"
        param_commit = "Frozen Commit"
        param_outcome = "Product Outcome"
        param_outcome_val = "DISCONTINUED"

        sec_findings = "Primary Findings"
        title_findings = "Executive Summary"
        card1_label = "Repair Success in Every Arm"
        card1_desc = "Baseline, Generic, and Doctor each achieved 100% repair success on all 19 defective cases. The specialized skill provided <strong>zero incremental repair capability</strong>."
        card2_num = "~1.91&times;"
        card2_label = "Doctor Execution Cost Ratio"
        card2_desc = f"Total cost of ${d['total_cost']:.2f} (${d['mean_cost']:.3f}/run) vs Baseline's ${b['total_cost']:.2f} (${b['mean_cost']:.3f}/run). Tool calls increased by 1.54&times; and wall-clock execution latency increased by 2.44&times;."
        card3_num = "2 / 6"
        card3_label = "Ambiguous Cases Stopped by Doctor"
        card3_desc = "Doctor halted for manual review on 2 of 6 ambiguous cases (case-011 and case-016). Baseline and Generic unilaterally guessed product policy on all 6 cases (0/6)."
        verdict_title = "Final Empirical Verdict"
        verdict_text = '"The specialized skill did not improve repair capability on this benchmark and imposed substantial execution cost. It showed a limited signal in preventing unsupported product-intent decisions on two specific cases, but this was insufficient to support product viability."'

        sec_measurements = "Empirical Measurements"
        title_table = "Three-Arm Controlled Comparison"
        prose_table = "All 90 runs were evaluated with the same frontier model (<code>claude-sonnet-5</code>) at medium effort. The only independent variable was the intervention injected into the agent environment."

        th_metric = "Evaluation Metric"
        th_a = "<span class=\"arm-dot baseline\"></span> Arm A: Baseline"
        th_b = "<span class=\"arm-dot generic\"></span> Arm B: Generic Rigor"
        th_c = "<span class=\"arm-dot doctor\"></span> Arm C: Interaction Doctor"
        th_delta = "Experimental Delta &amp; Interpretation"

        r1 = ("Repair Success (Specified Defects)", "19 / 19 (100%)", "19 / 19 (100%)", "19 / 19 (100%)", "0% lift. Pure parity on well-specified defects.")
        r2 = ("Correct NO-Op (Benign Controls)", "3 / 5 (60.0%)", "2 / 5 (40.0%)", "2 / 5 (40.0%)", "Baseline was slightly less prone to unnecessary churn.")
        r3 = ("Functional False Positives", "0 / 5 (0.0%)", "0 / 5 (0.0%)", "0 / 5 (0.0%)", "No arm broke the underlying logic of benign controls.")
        r4 = ("Intent Guessing Rate (NEEDS_INTENT)", "6 / 6 (100%)", "6 / 6 (100%)", "4 / 6 (66.7%)", "Doctor reduced guessing by 33.3% (stopped on 011, 016).")
        r5 = ("Manual Review Ambiguity Halts", "0 / 6 (0.0%)", "0 / 6 (0.0%)", "2 / 6 (33.3%)", "Sole positive signal: Doctor stopped on 2 underspecified cases.")
        r6 = ("Measured Regressions", "1 / 30 (3.3%)", "1 / 30 (3.3%)", "0 / 30 (0.0%)", "<em>Non-independent:</em> The only regression occurred on 011, which Doctor avoided solely by pausing.")
        r7 = ("False Closure Claims", "0 / 30 (0.0%)", "1 / 30 (3.3%)", "0 / 30 (0.0%)", "Generic arm claimed completion on case-011 while failing.")
        r8 = ("Detection Heuristic (Keyword Match)", "14 / 19 (73.7%)", "18 / 19 (94.7%)", "18 / 19 (94.7%)", "Diagnostic keyword presence only; NOT semantic recall.")
        r9 = ("Total Cost (30 Runs)", f"${b['total_cost']:.4f}", f"${g['total_cost']:.4f}", f"${d['total_cost']:.4f}", "<strong>1.91&times;</strong> cost increase for Doctor intervention.")
        r10 = ("Mean Cost per Case Run", f"${b['mean_cost']:.4f}", f"${g['mean_cost']:.4f}", f"${d['mean_cost']:.4f}", "+$0.0986 extra per case.")
        r11 = ("Total Wall Clock Time", f"{b['total_seconds']:.1f}s", f"{g['total_seconds']:.1f}s", f"{d['total_seconds']:.1f}s", "<strong>2.44&times;</strong> execution latency multiplier.")
        r12 = ("Mean Wall Time per Run", f"{b['mean_seconds']:.1f}s", f"{g['mean_seconds']:.1f}s", f"{d['mean_seconds']:.1f}s", "+40.6s added delay per run.")
        r13 = ("Total Tool Calls", f"{b['total_tools']}", f"{g['total_tools']}", f"{d['total_tools']}", "<strong>1.54&times;</strong> tool invocation overhead.")
        r14 = ("Mean Tool Invocations per Run", f"{b['mean_tools']:.1f}", f"{g['mean_tools']:.1f}", f"{d['mean_tools']:.1f}", "+2.5 roundtrips per case.")

        chart_sec = "Comparative Data Graphics"
        chart_title_main = "Cost, Latency &amp; Repair Visualizations"
        c1_title = "Figure 1: Repair Success on Specified Defects (n=19)"
        c1_sub = "Denom: 19 YES cases"
        c1_caption = "Identical bar lengths depict exact parity. No repair delta was observed."
        c2_title = "Figure 2: Total API Cost across 30 Runs ($ USD)"
        c2_sub = "Denom: 30 runs per arm"
        c2_caption = "Doctor imposed an 81% cost penalty over generic audit and 91% over baseline."
        c3_title = "Figure 3: Mean Wall-Clock Latency per Run (Seconds)"
        c3_sub = "Lower is faster"
        c3_caption = "Doctor required 2.44&times; longer to complete execution due to auditing overhead."
        c4_title = "Figure 4: Intent Guessing Rate on Ambiguous Tasks (n=6)"
        c4_sub = "Lower guessing is better"
        c4_caption = "Doctor uniquely stopped on 2 cases (011, 016), while baseline/generic guessed on all 6."

        ambig_sec = "Ambiguity Analysis"
        ambig_title = "NEEDS_INTENT Case Breakdown"
        ambig_prose = "Six benchmark cases contain fundamentally underspecified interaction policy choices where multiple plausible product decisions exist. Agents were scored on whether they recognized the ambiguity and stopped to ask rather than unilaterally implementing an ungrounded preference."
        ambig_th_id = "ID"
        ambig_th_name = "Case Title"
        ambig_th_b = "Baseline"
        ambig_th_g = "Generic"
        ambig_th_d = "Doctor"
        ambig_th_outcome = "Observed Behavioral Outcome under Doctor"
        ambig_why_title = "Why Did Doctor Only Stop on 011 and 016?"
        ambig_why_p1 = "In <code>case-011-shared-canvas-bifurcation</code> and <code>case-016-swipe-left-double-bound</code>, the conflict directly manifested as two conflicting event handlers attached to the same DOM target. Doctor's ownership graph extraction explicitly flagged the collision and triggered the protocol's <code>NEEDS_INTENT</code> disposition."
        ambig_why_p2 = "Conversely, on <code>case-004</code>, <code>case-010</code>, <code>case-013</code>, and <code>case-019</code>, the ambiguity stemmed from lifecycle scoping or environmental defaults rather than direct simultaneous event bindings. Despite possessing the skill prompt, the model rationalized a 'standard' resolution and edited the files anyway."

        corpus_sec = "Full Corpus Overview"
        corpus_title = "30-Case &times; 3-Arm Observation Matrix (90 Runs)"
        corpus_prose = "Every row represents one benchmark fixture. Click any row or case name to inspect the full prompt, hidden oracles, and execution telemetry in the Case Explorer."
        corpus_th_id = "ID"
        corpus_th_name = "Case Name"
        corpus_th_outcome = "Outcome"
        corpus_th_a = "Arm A: Baseline"
        corpus_th_b = "Arm B: Generic"
        corpus_th_c = "Arm C: Doctor"
        corpus_link_explorer = "Open Filterable Case Explorer &rarr;"

        post_sec = "Engineering Postmortem"
        post_title = "Why Productization Failed: Three Architectural Dead Ends"
        post_prose = "When early smoke tests revealed that always running Interaction Doctor doubled costs with zero repair benefit, engineering explored three separate mitigation architectures to selectively invoke the skill. All three failed."

        post1_title = "1. The Universal Semantic Eval Gate Problem"
        post1_hyp = "<strong>Hypothesis:</strong> Place a fast, cheap upstream classifier prompt in front of the model to decide whether an incoming task contains an interaction-ownership problem before loading the heavy skill."
        post1_fail = "<strong>Why it failed:</strong> Cascading classifiers have asymmetrical risk. If the gate has even a 10% false negative rate, it permanently locks out the downstream specialist from ever seeing the task. Tuning the gate for zero false negatives forced its recall so wide that it triggered on virtually every UI edit, returning total costs right back to 1.9&times;."

        post2_title = "2. The Self-Routing Failure"
        post2_hyp = "<strong>Hypothesis:</strong> Give the baseline agent a concise tool or skill description and let the model self-route when it gets stuck or detects ambiguity."
        post2_fail = "<strong>Why it failed:</strong> Frontier models suffer from severe meta-cognitive blindspots when dealing with interaction bugs. The baseline model confidently believes its first broken patch is correct, so it never experiences the doubt required to trigger an external consultation. Self-routing yielded an invocation rate near zero on the very cases that needed it."

        post3_title = "3. The Native Static Detector Experiment"
        post3_hyp = "<strong>Hypothesis:</strong> Use lexical AST parsing and static regex triggers in the IDE/CLI to flag nested pointer events and inject the skill deterministically without LLM gating overhead."
        post3_fail = "<strong>Why it failed:</strong> Static detectors proved completely brittle across custom frameworks and abstractions. They triggered endlessly on standard benign patterns (e.g. nested buttons with proper delegation) while completely missing cross-component lifecycle leaks (e.g. uncancelled RAF loops, background tab listeners, or React Native gesture responders wrapped in hooks)."

        disp_sec = "Disposition Record"
        disp_title = "Final Product Disposition"
        disp_cert_title = "ARCHIVAL DISPOSITION DECISION &bull; EXP-202609-ID"
        disp_cert_date = "EFFECTIVE DATE: SEPTEMBER 2026"
        disp_item_skill = "INTERACTION DOCTOR SKILL:"
        disp_val_skill = '<span class="archival-badge discontinued">DISCONTINUED</span>'
        disp_item_bench = "BENCHMARK &amp; HARNESS:"
        disp_val_bench = '<span class="archival-badge retained">RETAINED AS RESEARCH ASSET</span>'
        disp_item_data = "EMPIRICAL OBSERVATIONS:"
        disp_val_data = '<span class="archival-badge retained">PRESERVED (90 RUNS)</span>'
        disp_rationale_lead = "<strong>Core Rationale:</strong> The benchmark demonstrated that modern frontier coding models already possess sufficient latent capability to diagnose and repair well-specified interaction bugs without domain-specific skill intervention. The specialized skill introduced a ~1.91&times; token cost penalty and a ~2.44&times; latency overhead without improving repair outcomes."
        disp_rationale_body = "The benchmark itself, however, remains a uniquely rigorous instrument: it features private behavioral oracles, distinguishes source churn from functional repairs, isolates protocol compliance from actual bug fixes, and rigorously scores ambiguous intent. It is preserved for future evaluations of agent architectures."

    content = f"""<!DOCTYPE html>
<html lang="{'ko' if is_ko else 'en'}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <link rel="stylesheet" href="./assets/showroom.css">
</head>
<body>
  <div class="site-wrapper">
    {render_masthead("index", lang)}

    <!-- Hero Dossier -->
    <section class="hero-dossier">
      <div class="hero-grid">
        <div>
          <div class="section-label">{section_dossier}</div>
          <h1 class="hero-headline">{headline}</h1>
          <p class="hero-subtitle">
            {subtitle}
          </p>
          <div class="lead-statement">
            {lead}
          </div>
        </div>

        <div>
          <div class="hero-parameters">
            <div style="font-weight: 700; border-bottom: 1px solid var(--rule-border); padding-bottom: 6px; margin-bottom: 8px; text-transform: uppercase; font-size: 11px;">
              {param_title}
            </div>
            <dl>
              <dt>{param_model}</dt><dd>claude-sonnet-5</dd><br>
              <dt>{param_effort}</dt><dd>medium</dd><br>
              <dt>{param_corpus}</dt><dd>{param_corpus_val}</dd><br>
              <dt>{param_arms}</dt><dd>{param_arms_val}</dd><br>
              <dt>{param_obs}</dt><dd>{param_obs_val}</dd><br>
              <dt>{param_sandbox}</dt><dd>{param_sandbox_val}</dd><br>
              <dt>{param_commit}</dt><dd><code>dfb9f79</code></dd><br>
              <dt>{param_outcome}</dt><dd style="color: var(--arm-doctor);">{param_outcome_val}</dd>
            </dl>
          </div>
        </div>
      </div>
    </section>

    <!-- Executive Result Cards -->
    <section class="section-block">
      <div class="section-label">{sec_findings}</div>
      <h2 class="section-title">{title_findings}</h2>

      <div class="findings-grid">
        <div class="finding-card">
          <div class="finding-num parity">19 / 19</div>
          <div class="finding-label">{card1_label}</div>
          <div class="finding-desc">
            {card1_desc}
          </div>
        </div>

        <div class="finding-card">
          <div class="finding-num cost">{card2_num}</div>
          <div class="finding-label">{card2_label}</div>
          <div class="finding-desc">
            {card2_desc}
          </div>
        </div>

        <div class="finding-card">
          <div class="finding-num signal">{card3_num}</div>
          <div class="finding-label">{card3_label}</div>
          <div class="finding-desc">
            {card3_desc}
          </div>
        </div>
      </div>

      <div class="verdict-callout">
        <div class="verdict-callout-title">{verdict_title}</div>
        <div class="verdict-callout-text">
          {verdict_text}
        </div>
      </div>
    </section>

    <!-- Three-Arm Controlled Comparison Table -->
    <section class="section-block">
      <div class="section-label">{sec_measurements}</div>
      <h2 class="section-title">{title_table}</h2>
      <p class="prose">
        {prose_table}
      </p>

      <div class="archival-table-wrap">
        <table class="archival-table">
          <thead>
            <tr>
              <th>{th_metric}</th>
              <th class="num">{th_a}</th>
              <th class="num">{th_b}</th>
              <th class="num">{th_c}</th>
              <th>{th_delta}</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>{r1[0]}</strong></td>
              <td class="num"><strong>{r1[1]}</strong></td>
              <td class="num"><strong>{r1[2]}</strong></td>
              <td class="num"><strong>{r1[3]}</strong></td>
              <td>{r1[4]}</td>
            </tr>
            <tr>
              <td><strong>{r2[0]}</strong></td>
              <td class="num">{r2[1]}</td>
              <td class="num">{r2[2]}</td>
              <td class="num">{r2[3]}</td>
              <td>{r2[4]}</td>
            </tr>
            <tr>
              <td><strong>{r3[0]}</strong></td>
              <td class="num">{r3[1]}</td>
              <td class="num">{r3[2]}</td>
              <td class="num">{r3[3]}</td>
              <td>{r3[4]}</td>
            </tr>
            <tr>
              <td><strong>{r4[0]}</strong></td>
              <td class="num">{r4[1]}</td>
              <td class="num">{r4[2]}</td>
              <td class="num">{r4[3]}</td>
              <td>{r4[4]}</td>
            </tr>
            <tr>
              <td><strong>{r5[0]}</strong></td>
              <td class="num">{r5[1]}</td>
              <td class="num">{r5[2]}</td>
              <td class="num">{r5[3]}</td>
              <td>{r5[4]}</td>
            </tr>
            <tr>
              <td><strong>{r6[0]}</strong></td>
              <td class="num">{r6[1]}</td>
              <td class="num">{r6[2]}</td>
              <td class="num">{r6[3]}</td>
              <td>{r6[4]}</td>
            </tr>
            <tr>
              <td><strong>{r7[0]}</strong></td>
              <td class="num">{r7[1]}</td>
              <td class="num">{r7[2]}</td>
              <td class="num">{r7[3]}</td>
              <td>{r7[4]}</td>
            </tr>
            <tr>
              <td><strong>{r8[0]}</strong></td>
              <td class="num">{r8[1]}</td>
              <td class="num">{r8[2]}</td>
              <td class="num">{r8[3]}</td>
              <td>{r8[4]}</td>
            </tr>
            <tr style="background: var(--bg-secondary); font-weight: 600;">
              <td><strong>{r9[0]}</strong></td>
              <td class="num">{r9[1]}</td>
              <td class="num">{r9[2]}</td>
              <td class="num" style="color: var(--arm-doctor);">{r9[3]}</td>
              <td>{r9[4]}</td>
            </tr>
            <tr>
              <td>{r10[0]}</td>
              <td class="num">{r10[1]}</td>
              <td class="num">{r10[2]}</td>
              <td class="num" style="color: var(--arm-doctor);">{r10[3]}</td>
              <td>{r10[4]}</td>
            </tr>
            <tr style="background: var(--bg-secondary); font-weight: 600;">
              <td><strong>{r11[0]}</strong></td>
              <td class="num">{r11[1]}</td>
              <td class="num">{r11[2]}</td>
              <td class="num" style="color: var(--arm-doctor);">{r11[3]}</td>
              <td>{r11[4]}</td>
            </tr>
            <tr>
              <td>{r12[0]}</td>
              <td class="num">{r12[1]}</td>
              <td class="num">{r12[2]}</td>
              <td class="num" style="color: var(--arm-doctor);">{r12[3]}</td>
              <td>{r12[4]}</td>
            </tr>
            <tr style="background: var(--bg-secondary); font-weight: 600;">
              <td><strong>{r13[0]}</strong></td>
              <td class="num">{r13[1]}</td>
              <td class="num">{r13[2]}</td>
              <td class="num" style="color: var(--arm-doctor);">{r13[3]}</td>
              <td>{r13[4]}</td>
            </tr>
            <tr>
              <td>{r14[0]}</td>
              <td class="num">{r14[1]}</td>
              <td class="num">{r14[2]}</td>
              <td class="num" style="color: var(--arm-doctor);">{r14[3]}</td>
              <td>{r14[4]}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Data Visualizations -->
    <section class="section-block">
      <div class="section-label">{chart_sec}</div>
      <h2 class="section-title">{chart_title_main}</h2>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
        <!-- Repair Parity Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title">{c1_title}</div>
            <div class="chart-subtitle">{c1_sub}</div>
          </div>
          <svg viewBox="0 0 500 160" class="svg-chart" role="img" aria-label="Repair success chart">
            <text x="10" y="32" font-family="IBM Plex Mono" font-size="12" fill="#161616">Baseline</text>
            <rect x="120" y="18" width="300" height="20" fill="#252525" rx="1" />
            <text x="430" y="33" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">19/19 (100%)</text>

            <text x="10" y="77" font-family="IBM Plex Mono" font-size="12" fill="#161616">Generic</text>
            <rect x="120" y="63" width="300" height="20" fill="#6B7075" rx="1" />
            <text x="430" y="78" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">19/19 (100%)</text>

            <text x="10" y="122" font-family="IBM Plex Mono" font-size="12" fill="#A33A2B">Doctor v1</text>
            <rect x="120" y="108" width="300" height="20" fill="#A33A2B" rx="1" />
            <text x="430" y="123" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#A33A2B">19/19 (100%)</text>
          </svg>
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted); margin-top: 8px;">
            {c1_caption}
          </div>
        </div>

        <!-- Cost Overhead Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title">{c2_title}</div>
            <div class="chart-subtitle">{c2_sub}</div>
          </div>
          <svg viewBox="0 0 500 160" class="svg-chart" role="img" aria-label="Cost comparison chart">
            <text x="10" y="32" font-family="IBM Plex Mono" font-size="12" fill="#161616">Baseline</text>
            <rect x="120" y="18" width="156" height="20" fill="#252525" rx="1" />
            <text x="286" y="33" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">$3.24 (1.00&times;)</text>

            <text x="10" y="77" font-family="IBM Plex Mono" font-size="12" fill="#161616">Generic</text>
            <rect x="120" y="63" width="166" height="20" fill="#6B7075" rx="1" />
            <text x="296" y="78" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#161616">$3.44 (1.06&times;)</text>

            <text x="10" y="122" font-family="IBM Plex Mono" font-size="12" fill="#A33A2B">Doctor v1</text>
            <rect x="120" y="108" width="300" height="20" fill="#A33A2B" rx="1" />
            <text x="430" y="123" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="#A33A2B">$6.20 (1.91&times;)</text>
          </svg>
          <div style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted); margin-top: 8px;">
            {c2_caption}
          </div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
        <!-- Wall Time Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title">{c3_title}</div>
            <div class="chart-subtitle">{c3_sub}</div>
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
            {c3_caption}
          </div>
        </div>

        <!-- Intent Guessing Chart -->
        <div class="chart-container">
          <div class="chart-header">
            <div class="chart-title">{c4_title}</div>
            <div class="chart-subtitle">{c4_sub}</div>
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
            {c4_caption}
          </div>
        </div>
      </div>
    </section>

    <!-- NEEDS_INTENT Detail -->
    <section class="section-block">
      <div class="section-label">{ambig_sec}</div>
      <h2 class="section-title">{ambig_title}</h2>
      <p class="prose">
        {ambig_prose}
      </p>

      <div class="archival-table-wrap">
        <table class="archival-table">
          <thead>
            <tr>
              <th>{ambig_th_id}</th>
              <th>{ambig_th_name}</th>
              <th>{ambig_th_b}</th>
              <th>{ambig_th_g}</th>
              <th>{ambig_th_d}</th>
              <th>{ambig_th_outcome}</th>
            </tr>
          </thead>
          <tbody>
            {ni_table_rows}
          </tbody>
        </table>
      </div>

      <div class="prose">
        <h3>{ambig_why_title}</h3>
        <p>
          {ambig_why_p1}
        </p>
        <p>
          {ambig_why_p2}
        </p>
      </div>
    </section>

    <!-- 30-Case Observation Matrix -->
    <section class="section-block">
      <div class="section-label">{corpus_sec}</div>
      <h2 class="section-title">{corpus_title}</h2>
      <p class="prose">
        {corpus_prose}
      </p>

      <div class="archival-table-wrap">
        <table class="archival-table observation-grid-table">
          <thead>
            <tr>
              <th style="width: 50px;">{corpus_th_id}</th>
              <th>{corpus_th_name}</th>
              <th style="width: 90px;">{corpus_th_outcome}</th>
              <th>{corpus_th_a}</th>
              <th>{corpus_th_b}</th>
              <th>{corpus_th_c}</th>
            </tr>
          </thead>
          <tbody>
            {matrix_rows}
          </tbody>
        </table>
      </div>
      <div style="text-align: right; margin-top: 12px;">
        <a href="{cases_url}" style="font-family: var(--font-mono); font-size: 13px; font-weight: 600;">{corpus_link_explorer}</a>
      </div>
    </section>

    <!-- Attempts to Save the Product -->
    <section class="section-block">
      <div class="section-label">{post_sec}</div>
      <h2 class="section-title">{post_title}</h2>
      <p class="prose">
        {post_prose}
      </p>

      <div style="display: flex; flex-direction: column; gap: 24px; margin-top: 24px;">
        <div style="background: var(--bg-surface); border: 1px solid var(--rule-border); padding: 24px;">
          <h3 style="font-family: var(--font-sans); font-size: 17px; font-weight: 700; margin-bottom: 8px; color: var(--ink-primary);">
            {post1_title}
          </h3>
          <p class="prose" style="font-size: 14px; margin-bottom: 8px;">
            {post1_hyp}
          </p>
          <p class="prose" style="font-size: 14px; margin-bottom: 0;">
            {post1_fail}
          </p>
        </div>

        <div style="background: var(--bg-surface); border: 1px solid var(--rule-border); padding: 24px;">
          <h3 style="font-family: var(--font-sans); font-size: 17px; font-weight: 700; margin-bottom: 8px; color: var(--ink-primary);">
            {post2_title}
          </h3>
          <p class="prose" style="font-size: 14px; margin-bottom: 8px;">
            {post2_hyp}
          </p>
          <p class="prose" style="font-size: 14px; margin-bottom: 0;">
            {post2_fail}
          </p>
        </div>

        <div style="background: var(--bg-surface); border: 1px solid var(--rule-border); padding: 24px;">
          <h3 style="font-family: var(--font-sans); font-size: 17px; font-weight: 700; margin-bottom: 8px; color: var(--ink-primary);">
            {post3_title}
          </h3>
          <p class="prose" style="font-size: 14px; margin-bottom: 8px;">
            {post3_hyp}
          </p>
          <p class="prose" style="font-size: 14px; margin-bottom: 0;">
            {post3_fail}
          </p>
        </div>
      </div>
    </section>

    <!-- Final Decision Record -->
    <section class="section-block">
      <div class="section-label">{disp_sec}</div>
      <h2 class="section-title">{disp_title}</h2>

      <div style="background: var(--bg-secondary); border: 2px solid var(--ink-primary); padding: 32px; margin-top: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; border-bottom: 1px solid var(--rule-border); padding-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <div style="font-family: var(--font-mono); font-size: 13px; font-weight: 700; text-transform: uppercase;">
            {disp_cert_title}
          </div>
          <div style="font-family: var(--font-mono); font-size: 12px; color: var(--ink-muted);">
            {disp_cert_date}
          </div>
        </div>

        <div style="font-family: var(--font-mono); font-size: 13px; line-height: 1.8; margin-bottom: 20px;">
          <div><strong style="display:inline-block; width: 220px;">{disp_item_skill}</strong> {disp_val_skill}</div>
          <div><strong style="display:inline-block; width: 220px;">{disp_item_bench}</strong> {disp_val_bench}</div>
          <div><strong style="display:inline-block; width: 220px;">{disp_item_data}</strong> {disp_val_data}</div>
        </div>

        <div class="prose" style="font-size: 14px;">
          <p>
            {disp_rationale_lead}
          </p>
          <p style="margin-bottom: 0;">
            {disp_rationale_body}
          </p>
        </div>
      </div>
    </section>

    {render_footer(lang)}
  </div>
  <script src="./assets/showroom.js"></script>
</body>
</html>
"""
    filename = "index.ko.html" if is_ko else "index.html"
    with open(os.path.join(SHOWROOM_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote showroom/{filename}")

def build_cases_page(summary, cases, lang="en"):
    is_ko = (lang == "ko")
    
    # Pre-render table rows for static fallback
    rows_html = ""
    for c in cases:
        b_verdict = format_verdict_html(c["runs"]["baseline"]["verdict"], lang)
        g_verdict = format_verdict_html(c["runs"]["generic"]["verdict"], lang)
        d_verdict = format_verdict_html(c["runs"]["doctor"]["verdict"], lang)
        is_signal = c["doctor_intent_stopped"]
        row_style = 'style="background: #FEF3C7;"' if is_signal else ''
        badge_text = "닥터 중단" if is_ko else "Doctor Stopped"
        badge_span = f'<span class="archival-badge retained" style="margin-left: 6px; font-size: 9px;">{badge_text}</span>' if is_signal else ''

        rows_html += f"""
        <tr {row_style} data-case-id="{c['case_id']}" class="case-row" style="cursor: pointer;">
          <td style="font-family: var(--font-mono); font-weight: 600;">{c['case_id']}</td>
          <td>
            <a href="#case-{c['case_id']}" class="case-name-link" style="font-weight: 600; color: var(--ink-primary); text-decoration: none;">{html.escape(c['name'])}</a>
            {badge_span}
          </td>
          <td><span class="archival-badge" style="background: var(--bg-secondary); border: 1px solid var(--rule-border);">{c['outcome']}</span></td>
          <td style="font-family: var(--font-mono); font-size: 11px;">{c['difficulty']}</td>
          <td style="font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">{html.escape(c['runtime'])}</td>
          <td>{b_verdict}</td>
          <td>{g_verdict}</td>
          <td>{d_verdict}</td>
        </tr>
        """

    if is_ko:
        page_title = "케이스 탐색기 &bull; Interaction Doctor 벤치마크"
        sec_label = "케이스 코퍼스 명세"
        main_title = "벤치마크 케이스 탐색기 (30개 픽스처)"
        lead_statement = "30개 벤치마크 테스트 픽스처, 비공개 테스트 오라클, 베이스라인(A군)·일반 감사(B군)·닥터 v1(C군) 간에 기록된 90회의 비교 관측치를 확인하십시오."
        
        lbl_outcome = "결과 유형:"
        btn_all = "전체 (30)"
        btn_yes = "결함 케이스 (19)"
        btn_no = "정상 대조군 (5)"
        btn_ni = "모호성 (6)"

        lbl_diff = "난이도:"
        btn_diff_all = "전체"
        btn_t1 = "T1 (기본)"
        btn_t2 = "T2 (생명주기/다자간)"

        search_ph = "케이스명, ID, 런타임 검색..."
        count_init = "총 30개 중 30개 케이스 표시 중"
        hint_drawer = "행을 클릭하면 세부 점검 드로어가 열립니다"

        th_id = "ID"
        th_name = "케이스명"
        th_exp = "기대 결과"
        th_tier = "난이도"
        th_runtime = "런타임"
        th_a = "A군: 베이스라인"
        th_b = "B군: 일반 감사"
        th_c = "C군: 인터랙션 닥터"

        drawer_header = "세부 점검 드로어"
        drawer_close = "&times; 닫기"
    else:
        page_title = "Case Explorer &bull; Interaction Doctor Benchmark"
        sec_label = "Case Corpus Dossier"
        main_title = "Benchmark Case Explorer (30 Fixtures)"
        lead_statement = "Inspect all 30 benchmark test fixtures, private test oracles, and the 90 comparative observations recorded across Baseline, Generic Rigor, and Doctor v1."
        
        lbl_outcome = "Outcome:"
        btn_all = "All (30)"
        btn_yes = "YES: Defects (19)"
        btn_no = "NO: Controls (5)"
        btn_ni = "NEEDS_INTENT: Ambiguity (6)"

        lbl_diff = "Difficulty:"
        btn_diff_all = "All"
        btn_t1 = "T1 (Basic)"
        btn_t2 = "T2 (Lifecycle/Multi-Actor)"

        search_ph = "Search case name, ID, runtime..."
        count_init = "Showing 30 of 30 cases"
        hint_drawer = "Click any row to open the full test case dossier"

        th_id = "ID"
        th_name = "Case Name"
        th_exp = "Expected"
        th_tier = "Tier"
        th_runtime = "Runtime"
        th_a = "Arm A: Baseline"
        th_b = "Arm B: Generic"
        th_c = "Arm C: Doctor"

        drawer_header = "Inspection Drawer"
        drawer_close = "&times; Close"

    content = f"""<!DOCTYPE html>
<html lang="{'ko' if is_ko else 'en'}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <link rel="stylesheet" href="./assets/showroom.css">
</head>
<body>
  <div class="site-wrapper">
    {render_masthead("cases", lang)}

    <section class="section-block">
      <div class="section-label">{sec_label}</div>
      <h1 class="section-title">{main_title}</h1>
      <p class="lead-statement">
        {lead_statement}
      </p>

      <!-- Filter Toolbar -->
      <div class="filter-toolbar">
        <div class="filter-group">
          <span class="filter-label">{lbl_outcome}</span>
          <button class="filter-btn active" data-filter-type="outcome" data-filter-val="ALL">{btn_all}</button>
          <button class="filter-btn" data-filter-type="outcome" data-filter-val="YES">{btn_yes}</button>
          <button class="filter-btn" data-filter-type="outcome" data-filter-val="NO">{btn_no}</button>
          <button class="filter-btn" data-filter-type="outcome" data-filter-val="NEEDS_INTENT">{btn_ni}</button>
        </div>

        <div class="filter-group">
          <span class="filter-label">{lbl_diff}</span>
          <button class="filter-btn active" data-filter-type="difficulty" data-filter-val="ALL">{btn_diff_all}</button>
          <button class="filter-btn" data-filter-type="difficulty" data-filter-val="T1">{btn_t1}</button>
          <button class="filter-btn" data-filter-type="difficulty" data-filter-val="T2">{btn_t2}</button>
        </div>

        <div class="filter-group" style="margin-left: auto;">
          <input type="text" id="case-search" placeholder="{search_ph}" style="padding: 4px 8px; font-family: var(--font-mono); font-size: 11px; border: 1px solid var(--rule-border); border-radius: var(--radius-sm); width: 220px;">
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; font-family: var(--font-mono); font-size: 11px; color: var(--ink-muted);">
        <span id="filtered-count">{count_init}</span>
        <span>{hint_drawer}</span>
      </div>

      <!-- Case Table -->
      <div class="archival-table-wrap">
        <table class="archival-table">
          <thead>
            <tr>
              <th style="width: 48px;">{th_id}</th>
              <th>{th_name}</th>
              <th style="width: 100px;">{th_exp}</th>
              <th style="width: 60px;">{th_tier}</th>
              <th style="width: 140px;">{th_runtime}</th>
              <th>{th_a}</th>
              <th>{th_b}</th>
              <th>{th_c}</th>
            </tr>
          </thead>
          <tbody id="cases-table-body">
            {rows_html}
          </tbody>
        </table>
      </div>
    </section>

    {render_footer(lang)}
  </div>

  <!-- Detail Slide-Over Drawer -->
  <div class="case-drawer-overlay" id="case-drawer-overlay">
    <div class="case-drawer" id="case-drawer">
      <div class="case-drawer-header">
        <div style="font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; color: var(--ink-muted);">
          {drawer_header}
        </div>
        <button class="case-drawer-close" id="case-drawer-close">{drawer_close}</button>
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
    filename = "cases.ko.html" if is_ko else "cases.html"
    with open(os.path.join(SHOWROOM_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote showroom/{filename}")

def build_methodology_page(summary, methodology, lang="en"):
    is_ko = (lang == "ko")

    if is_ko:
        page_title = "방법론 및 재현 가이드 &bull; Interaction Doctor 벤치마크"
        sec_label = "실험 프로토콜 명세"
        main_title = "벤치마크 방법론 및 재현성 가이드"
        lead_statement = "실험 통제 변수, 격리 아키텍처, 채점 오라클, 사전 적격성 한계(보존된 주의사항) 및 재현 명령어에 대한 완전한 기술 명세서입니다."

        body_html = """
        <h3>1. 연구 질문 (The Research Question)</h3>
        <p>
          프론티어 코딩 모델(<code>claude-sonnet-5</code>)에 UI 인터랙션 소유권 특화 스킬(Interaction Doctor v1)을 주입했을 때, 추가 개입이 없는 기본 모델(Baseline) 또는 일반적인 엄격성 프롬프트(Generic Rigor) 대조군과 비교하여 실제 인터랙션 결함을 진단하고 수정하는 능력이 유의미하게 향상되는가?
        </p>

        <h3>2. 3개 대조 실험군 (Three Experimental Arms)</h3>
        <ul>
          <li><strong>A군 (Baseline, 기본 모델):</strong> 추가 스킬이나 특수 지침 없이 순수 태스크 지시문과 대상 프로젝트 픽스처만 제공. 모델의 본원적 인터랙션 디버깅 역량을 측정.</li>
          <li><strong>B군 (Generic Rigor, 일반 엄격 감사 프롬프트):</strong> 동일 모델에 Interaction Doctor 고유 용어 없이 일반적인 "면밀히 검토하고 엣지 케이스를 감사하라"는 지시만 추가. 프롬프트 길이와 일반적 신중함 편향을 통제.</li>
          <li><strong>C군 (Doctor v1, 인터랙션 닥터 스킬):</strong> 동일 모델의 워크스페이스 내 <code>.claude/skills/</code> 경로에 동결된 Interaction Doctor v1 스킬을 주입하고 스킬 프로토콜 준수를 명시적으로 지시.</li>
        </ul>

        <h3>3. 격리 아키텍처 (v6 Native Sandboxing)</h3>
        <p>
          모든 테스트 관측치는 저장소 외부의 임시 디렉터리(<code>$TMPDIR/interaction-doctor-bench/</code>)에 생성된 일회성 독립 워크스페이스에서 실행되었습니다. 워크스페이스는 엄격하게 순차적으로 생성, 실행, 채점, 아카이브, 삭제되었습니다.
        </p>
        <p>
          도구 접근은 Claude Code의 네이티브 아키텍처(<code>--permission-mode dontAsk</code>)로 엄격히 통제되었습니다:
        </p>
        <ul>
          <li><strong>파일 도구 통제:</strong> 기본 <code>Read</code>, <code>Edit</code>, <code>Write</code>, <code>Glob</code>, <code>Grep</code> 도구는 실행별 인라인 설정 규칙을 통해 임시 워크스페이스 디렉터리로만 엄격히 제한되었습니다. 저장소 루트, 민감 인증 경로(<code>~/.ssh</code>, <code>~/.aws</code>, <code>~/.claude</code>, macOS Keychain) 및 비공개 테스트 오라클 접근은 Fail-closed 원칙으로 전면 차단되었습니다.</li>
          <li><strong>Bash 샌드박스:</strong> 프로세스 생성은 macOS Seatbelt 샌드박스 정책을 통해 엄격히 제한되었습니다(<code>failIfUnavailable: true</code>, <code>network.strictAllowlist: true</code>, <code>network.allowedDomains: []</code>).</li>
          <li><strong>금지 도구:</strong> 외부 데이터 유출이나 웹 검색을 통한 지식 오염을 방지하기 위해 웹 검색 및 가져오기 도구(<code>WebSearch</code>, <code>WebFetch</code>) 사용이 완전히 비활성화되었습니다.</li>
        </ul>

        <h3>4. 비공개 오라클 및 채점 프로토콜 (Private Oracles &amp; Scoring)</h3>
        <p>
          채점은 <code>benchmark/graders/grade_run.py</code>를 통해 100% 자동화되고 결정론적으로 수행되었습니다. 평가 대상 에이전트에게는 비공개 테스트 단언문이나 정답 오라클이 일절 공개되지 않았습니다:
        </p>
        <ul>
          <li><strong>결함 수정 성공 (Repair Success):</strong> 에이전트가 수정한 코드에 대해 비공개 <code>test.js</code>의 목표 단언문이 모두 통과해야 함.</li>
          <li><strong>기능 퇴행 검사 (Regression Check):</strong> 수정 전 원본 픽스처에서 정상 통과하던 모든 비목표 단언문이 수정 후에도 온전히 통과해야 함.</li>
          <li><strong>단순 코드 변경(Churn)과 실제 기능 변경 구별:</strong> 채점기는 주석이나 서식 변경 같은 단순 바이트 차이와 상태 프로브로 검증된 실제 동작 변경을 엄격히 구별함.</li>
          <li><strong>모호성 채점 (NEEDS_INTENT Scoring):</strong> 기획이 불완전한 태스크에서 에이전트가 일방적으로 코드를 수정(의도 추측)하면 감점하며, 모호성을 식별하고 수정을 멈춘 채 사용자 확인을 요청했을 때만 정답으로 인정함.</li>
        </ul>

        <h3>5. 사전 적격성 한계 (보존된 주의사항, Qualification Gate Limitation)</h3>
        <div class="verdict-callout" style="border-left-color: var(--status-ambiguity); background: #FFFBEB;">
          <div class="verdict-callout-title" style="color: var(--status-ambiguity);">사전 적격성 게이트 한계 고지</div>
          <div class="verdict-callout-text" style="font-size: 14px;">
            90회 정규 배치 실행 전의 공식 사전 적격성 상태는 <strong>보류(HOLD, READY_FOR_EMPIRICAL_90_RUNS = False)</strong>였습니다. 이 보류 조치는 평가 대상 모델이 프롬프트 부록에 명시된 진단 프로브 명령을 완벽히 실행하지 않았기 때문에 발동되었습니다. 닥터는 bash 프로브는 성공적으로 실행했으나 기본 read 프로브를 건너뛰었습니다. 이는 샌드박스 인프라 결함이 아닌 모델의 프롬프트 프로브 준수 부족으로 규명되었으며, 90회 실증 배치는 명시적인 적격성 유예(waiver) 하에 진행되었습니다. 동결 검증과 워크스페이스 격리는 전체 실험 동안 완벽히 유지되었습니다.
          </div>
        </div>

        <h3>6. 실행 이력 및 재시도 정책 (Execution History &amp; Retry Policy)</h3>
        <ul>
          <li><strong>001~014번 케이스:</strong> 1차 실행(<code>run-01</code>)에서 오류 없이 정상 수집되었습니다.</li>
          <li><strong>015~030번 케이스:</strong> 초기 실행 중 Anthropic API 429 동시성/세션 한도에 도달했습니다. 실패한 인프라 트레이스는 모두 보존되었으며, 속도 제한 해제 후 3차 실행(<code>run-03</code>)에서 정상 관측치가 수집되었습니다.</li>
          <li><strong>결과 선별 재실행 금지:</strong> 결과를 좋게 만들기 위해 성공한 실행을 임의로 재실행한 적은 단 한 번도 없습니다.</li>
        </ul>

        <h3>7. 스코프 제약: 미모델링 케이스 부재 (UNMODELED Count = 0)</h3>
        <p>
          30개 벤치마크 케이스는 모두 모델링 가능한 표준 인터랙션 영역(포인터, 터치, 키보드, 포커스, 타이밍, 합성, 아날로그 MIDI 심)을 다룹니다. <strong>본 벤치마크는 미모델링(UNMODELED) 케이스를 정확히 0개 포함합니다</strong>. 따라서 본 벤치마크는 에이전트가 미지원 물리 인터랙션 양식을 인식하고 거부하는 능력에 대해 어떠한 실증적 주장도 하지 않습니다.
        </p>

        <h3>8. 재현 방법 안내 (How to Reproduce)</h3>
        <p>
          Claude Code 환경을 갖춘 연구자는 저장소 루트에서 동결 무결성을 검증하고 자체 테스트를 로컬에서 즉시 실행할 수 있습니다:
        </p>
        <div class="code-block">
# 1. 동결 해시를 기준으로 파일 무결성 검증
python3 benchmark/design/verify_experiment_freeze.py

# 2. 채점기 자체 검증 실행 (정답 픽스처에 대한 채점 로직 검증)
python3 benchmark/graders/grade_run_selftest.py

# 3. 원천 데이터와 쇼룸 데이터 간 일치 검증
python3 scripts/validate_showroom_data.py
        </div>
        """
    else:
        page_title = "Methodology &amp; Replication &bull; Interaction Doctor Benchmark"
        sec_label = "Experimental Protocol"
        main_title = "Benchmark Methodology &amp; Reproducibility Guide"
        lead_statement = "A complete specification of experimental variables, isolation architecture, scoring oracles, preflight qualification limitations, and replication commands."

        body_html = """
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
        """

    content = f"""<!DOCTYPE html>
<html lang="{'ko' if is_ko else 'en'}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{page_title}</title>
  <link rel="stylesheet" href="./assets/showroom.css">
</head>
<body>
  <div class="site-wrapper">
    {render_masthead("methodology", lang)}

    <section class="section-block">
      <div class="section-label">{sec_label}</div>
      <h1 class="section-title">{main_title}</h1>
      <p class="lead-statement">
        {lead_statement}
      </p>

      <div class="prose">
        {body_html}
      </div>
    </section>

    {render_footer(lang)}
  </div>
</body>
</html>
"""
    filename = "methodology.ko.html" if is_ko else "methodology.html"
    with open(os.path.join(SHOWROOM_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote showroom/{filename}")

def main():
    summary, cases, methodology = load_data()
    generate_js()
    
    # English pages
    build_index_page(summary, cases, "en")
    build_cases_page(summary, cases, "en")
    build_methodology_page(summary, methodology, "en")
    
    # Korean pages
    build_index_page(summary, cases, "ko")
    build_cases_page(summary, cases, "ko")
    build_methodology_page(summary, methodology, "ko")
    
    print("All showroom pages (EN & KO) successfully generated.")

if __name__ == '__main__':
    main()
