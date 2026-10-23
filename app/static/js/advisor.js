/**
 * AI Financial Advisor Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const periodSelect = document.getElementById('advisorPeriodSelect');
  const generateBtn = document.getElementById('generateAdviceBtn');
  const spinner = document.getElementById('advisorSpinner');
  const btnIcon = document.getElementById('advisorBtnIcon');

  const healthScoreEl = document.getElementById('advisorHealthScore');
  const scoreBadgeEl = document.getElementById('advisorScoreBadge');
  const timestampEl = document.getElementById('advisorTimestamp');
  const summaryTextEl = document.getElementById('advisorSummaryText');

  const badgeIncome = document.getElementById('badgeIncome');
  const badgeExpense = document.getElementById('badgeExpense');
  const badgeSavingsRate = document.getElementById('badgeSavingsRate');

  const topCatsList = document.getElementById('advisorTopCategoriesList');
  const savingsTipsList = document.getElementById('advisorSavingsTipsList');
  const actionPlanContainer = document.getElementById('advisorActionPlanContainer');

  // Load Latest Cached Advice or Generate
  async function loadInitialAdvice() {
    try {
      const res = await fetch('/api/advisor/latest');
      if (res.ok) {
        const data = await res.json();
        if (data.has_insight) {
          renderAdvice(data.insight);
          return;
        }
      }
      // If no insight exists yet, generate automatically
      generateAdvice();
    } catch (err) {
      console.error('Failed to load initial advice:', err);
    }
  }

  // Generate / Refresh AI Advice
  async function generateAdvice() {
    const period = periodSelect ? periodSelect.value : 'this-month';

    generateBtn.disabled = true;
    spinner.classList.remove('d-none');
    btnIcon.classList.add('d-none');

    try {
      const res = await fetch('/api/advisor/insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ period })
      });

      if (!res.ok) throw new Error('Failed to generate insights');
      const data = await res.json();

      renderAdvice(data.insight, data.provider, data.metrics);
    } catch (err) {
      console.error('AI Advice generation error:', err);
      alert('Unable to generate AI insights. Check server connection.');
    } finally {
      generateBtn.disabled = false;
      spinner.classList.add('d-none');
      btnIcon.classList.remove('d-none');
    }
  }

  // Render Insight Data onto the UI
  function renderAdvice(insight, provider = null, metrics = null) {
    if (!insight) return;

    // Health Score
    const score = insight.health_score || 75;
    healthScoreEl.textContent = `${score}/100`;

    if (score >= 80) {
      scoreBadgeEl.textContent = 'Excellent Financial Health';
      scoreBadgeEl.className = 'fw-semibold text-success mb-1';
    } else if (score >= 65) {
      scoreBadgeEl.textContent = 'Good / Moderate Health';
      scoreBadgeEl.className = 'fw-semibold text-primary mb-1';
    } else if (score >= 50) {
      scoreBadgeEl.textContent = 'Fair / Caution Advised';
      scoreBadgeEl.className = 'fw-semibold text-warning mb-1';
    } else {
      scoreBadgeEl.textContent = 'High Outflow Warning';
      scoreBadgeEl.className = 'fw-semibold text-danger mb-1';
    }

    // Timestamp & Provider
    const provName = provider || insight.raw_response || 'Gemini 3.8 Flash';
    timestampEl.textContent = `Provider: ${provName}`;

    // Executive Summary
    summaryTextEl.textContent = insight.summary || 'Summary unavailable.';

    // Metrics Badges
    if (metrics) {
      badgeIncome.textContent = `Income: ${formatCurrency(metrics.total_income)}`;
      badgeExpense.textContent = `Expenses: ${formatCurrency(metrics.total_expenses)}`;
      badgeSavingsRate.textContent = `Savings Rate: ${metrics.savings_rate}%`;
    }

    // Top Categories
    topCatsList.innerHTML = '';
    const topCats = insight.top_categories || [];
    if (topCats.length === 0) {
      topCatsList.innerHTML = `<li class="list-group-item text-muted small py-3">No major expense outflows identified.</li>`;
    } else {
      topCats.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex align-items-center gap-2 py-3';
        li.innerHTML = `
          <i class="bi bi-arrow-right-circle-fill text-danger flex-shrink-0"></i>
          <span class="small text-dark fw-medium">${item}</span>
        `;
        topCatsList.appendChild(li);
      });
    }

    // Savings Tips
    savingsTipsList.innerHTML = '';
    const tips = insight.savings_tips || [];
    if (tips.length === 0) {
      savingsTipsList.innerHTML = `<li class="list-group-item text-muted small py-3">No savings recommendations at this time.</li>`;
    } else {
      tips.forEach(item => {
        const li = document.createElement('li');
        li.className = 'list-group-item d-flex align-items-center gap-2 py-3';
        li.innerHTML = `
          <i class="bi bi-lightbulb-fill text-warning flex-shrink-0"></i>
          <span class="small text-dark fw-medium">${item}</span>
        `;
        savingsTipsList.appendChild(li);
      });
    }

    // Action Plan
    actionPlanContainer.innerHTML = '';
    const plan = insight.action_plan || [];
    if (plan.length === 0) {
      actionPlanContainer.innerHTML = `<div class="col-12 text-muted small py-3">No action steps currently required.</div>`;
    } else {
      plan.forEach((step, idx) => {
        const col = document.createElement('div');
        col.className = 'col-12 col-md-6';
        col.innerHTML = `
          <div class="p-3 rounded-3 bg-light border h-100 d-flex align-items-start gap-3">
            <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center fw-bold flex-shrink-0" style="width: 28px; height: 28px; font-size: 0.85rem;">
              ${idx + 1}
            </div>
            <div class="small text-dark fw-medium">
              ${step}
            </div>
          </div>
        `;
        actionPlanContainer.appendChild(col);
      });
    }
  }

  // Event Listeners
  if (generateBtn) {
    generateBtn.addEventListener('click', generateAdvice);
  }

  // Initial Load
  loadInitialAdvice();
});
